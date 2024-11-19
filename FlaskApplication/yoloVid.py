import datetime
import threading
from ultralytics import YOLO
from storage import client, get_db_connection, bucket_url
from flask import jsonify
import mariadb
import cv2
import math
import time
import io

def video_detection(path_x, is_running):
    video_capture = path_x
    cap = cv2.VideoCapture(video_capture)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    model = YOLO("../RunningYolo/best.pt")  # Load the YOLO model
    classNames = ["helmet", "no-helmet", "rider"]

    while is_running:
        success, img = cap.read()
        if not success:
            break

        results = model(img, stream=True)

        for r in results:
            boxes = r.boxes

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                cls = int(box.cls[0])  # Get class ID
                class_name = classNames[cls]

                if class_name == "rider":  # Check if the class is 'rider'
                    rider_detected = True

                    # Check for "no helmet" within the rider's bounding box
                    for inner_box in boxes:
                        inner_x1, inner_y1, inner_x2, inner_y2 = inner_box.xyxy[0]
                        inner_x1, inner_y1, inner_x2, inner_y2 = int(inner_x1), int(inner_y1), int(inner_x2), int(inner_y2)
                        inner_cls = int(inner_box.cls[0])
                        inner_class_name = classNames[inner_cls]

                        # Ensure "no-helmet" is within rider box
                        if (
                            inner_class_name == "no-helmet" and
                            (x1 < inner_x1 < x2 and y1 < inner_y1 < y2) or
                            (x1 < inner_x2 < x2 and y1 < inner_y2 < y2)
                        ):
                            # Draw rider box
                            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 3)  # Yellow for Rider
                            cv2.putText(
                                img,
                                "Rider",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 255),
                                2,
                            )

                            # Draw no-helmet box
                            cv2.rectangle(img, (inner_x1, inner_y1), (inner_x2, inner_y2), (0, 0, 255), 3)  # Red for No Helmet
                            cv2.putText(
                                img,
                                "No Helmet",
                                (inner_x1, inner_y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 0, 255),
                                2,
                            )

                            # Optional: Log or save the detected image
                            saveDetectedImageToCloud(img, "Rider without Helmet")

        yield img

    cap.release()
    cv2.destroyAllWindows()



def saveDetectedImageToCloud(img, class_name):
    def async_upload_and_save():
        try:
            timestamp = int(datetime.datetime.now().timestamp())
            filename = f'captured_image_{timestamp}.png'

            # Encode the image to bytes
            _, buffer = cv2.imencode('.png', img)
            image_byte = io.BytesIO(buffer)

            # Cloud bucket upload
            bucket_name = 'aihelmetdetection'
            object_key = f'captured_image_{timestamp}.png'
            client.upload_fileobj(image_byte, bucket_name, object_key)

            # Save the URL to the database
            saveImageUrlToDb(filename)
        except Exception as e:
            print(f"Error in saving detected image: {e}")

    # Run the function asynchronously
    upload_thread = threading.Thread(target=async_upload_and_save)
    upload_thread.start()

def saveImageUrlToDb(filename):
    conn = get_db_connection()
    if conn:
            cur = conn.cursor()
            image_path=f'{bucket_url}/{filename}'

            cur.execute("INSERT INTO footage (image_url) VALUES (?)", (image_path,))
            conn.commit()
