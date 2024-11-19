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

    model = YOLO("../YOLO-Weights/best.pt")  # Load the YOLO model
    classNames = ["helmet", "no-helmet", "rider"]

    # Class Names (Ensure they match your model's training classes)
    CLASS_RIDER = "rider"
    CLASS_HELMET = "helmet"
    CLASS_NO_HELMET = "no-helmet"

    # Define colors for each class
    COLOR_RIDER = (0, 255, 255)    # Yellow for Rider
    COLOR_HELMET = (0, 255, 0)     # Green for Helmet
    COLOR_NO_HELMET = (0, 0, 255)  # Red for No Helmet

    while is_running:
        success, img = cap.read()
        if not success:
            break

        results = model(img, stream=True, conf=0.8)

            # Extract detection information
        # detections = results[0].boxes  # Get the bounding boxes and class info

        # Variables to track rider and helmet status
        is_rider_detected = False
        helmet_detected = False
        no_helmet_detected = False

        for r in results:
            detections = r.boxes


            for detection in detections:
                    class_id = int(detection.cls)  # Class index
                    class_name = model.names[class_id]  # Get class name from the model
                    bbox = detection.xyxy[0].tolist()  # Get bounding box coordinates (x1, y1, x2, y2)
                    confidence = detection.conf.tolist()[0]  # Detection confidence score
                    print(f"Detected {class_name} with confidence {confidence} at {bbox}")  # Debug information
                    x1, y1, x2, y2 = map(int, bbox)


                    # Check for rider
                    if class_name == CLASS_RIDER:
                        is_rider_detected = True
                        label = "Rider"
                        color = COLOR_RIDER
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    # Check for helmet
                    elif class_name == CLASS_HELMET:
                        helmet_detected = True
                        label = "Helmet"
                        color = COLOR_HELMET
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    # Check for no helmet
                    elif class_name == CLASS_NO_HELMET:
                        no_helmet_detected = True
                        label = "No-Helmet"
                        color = COLOR_NO_HELMET
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Check the conditions after processing all detections
            if is_rider_detected:
                if helmet_detected and not no_helmet_detected:
                    cv2.putText(img, "Riding with Helmet", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_HELMET, 2)
                elif no_helmet_detected:
                    cv2.putText(img, "Riding without Helmet", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_NO_HELMET, 2)
                else:
                    cv2.putText(img, "Riding Status: Unknown", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                cv2.putText(img, "No Rider Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                                #
                            #  Optional: Log or save the detected image
                            # saveDetectedImageToCloud(img, "Rider without Helmet")

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
