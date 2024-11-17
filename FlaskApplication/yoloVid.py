from ultralytics import YOLO
from storage import client, get_db_connection, bucket_url
import cv2
import math
import time
import io

def video_detection(path_x, is_running):
    video_capture = path_x
    #Create a Webcam Object
    cap=cv2.VideoCapture(video_capture)
    frame_width=int(cap.get(3))
    frame_height=int(cap.get(4))
    #out=cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc('M', 'J', 'P','G'), 10, (frame_width, frame_height))

    # model=YOLO("../RunningYolo/yolo11n.pt")
    model=YOLO("../RunningYolo/best.pt")
    classNames = ["helmet","no-helmet","rider"]

    while is_running is True:
        success, img = cap.read()
        results=model(img,stream=True)
        for r in results:
            boxes=r.boxes
            for box in boxes:
                x1,y1,x2,y2=box.xyxy[0]
                x1,y1,x2,y2=int(x1), int(y1), int(x2), int(y2)
                print(x1,y1,x2,y2)
                cv2.rectangle(img, (x1,y1), (x2,y2), (255,0,255),3)
                conf=math.ceil((box.conf[0]*100))/100
                cls=int(box.cls[0])
                class_name=classNames[cls]
                label=f'{class_name}{conf}'
                t_size = cv2.getTextSize(label, 0, fontScale=1, thickness=2)[0]
                print(t_size)
                c2 = x1 + t_size[0], y1 - t_size[1] - 3
                cv2.rectangle(img, (x1,y1), c2, [255,0,255], -1, cv2.LINE_AA)  # filled
                cv2.putText(img, label, (x1,y1-2),0, 1,[255,255,255], thickness=1,lineType=cv2.LINE_AA)

                if class_name == classNames[1]:
                    saveDetectedImageToCloud(img, class_name)

        yield img
        #out.write(img)
        #cv2.imshow("image", img)
        #if cv2.waitKey(1) & 0xFF==ord('1'):
            #break
    #out.release()
    while is_running is False:
        cap.release()
cv2.destroyAllWindows()

def saveDetectedImageToCloud (img, class_name):
    timestamp = int(time.time())
    filename = f'captured_image_{timestamp}.jpg'
    image_path = f'static/captured_image_{timestamp}.jpg'
    cv2.imwrite(image_path, img)
    # print(f"Image saved at {image_path} due to detection of class: {class_name}")

    _, buffer = cv2.imencode('.png', img) 
    image_byte = io.BytesIO(buffer)

    bucket_name = 'aihelmetdetection'
    object_key = f'captured_image_{timestamp}.png'
    client.upload_fileobj(image_byte, bucket_name, object_key)
    # print(f'Image uploaded to R2 bucket: {bucket_name}/captured_image_{timestamp}.png')

    saveImageUrlToDb(filename, timestamp)

def saveImageUrlToDb(filename, date):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            image_path=f'{bucket_url}/{filename}'

            cur.execute("INSERT INTO footage (image_url, date) VALUES (?, ?)", (image_path, date))
            conn.commit()

            return jsonify({"message": "Database connection is successful!"}), 200
        except mariadb.Error as e:
            return jsonify({"error": f"Query execution failed: {e}"}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Failed to connect to the database."}), 500