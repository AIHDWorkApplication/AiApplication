import datetime
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

    rider_detected = False
    for r in results:
      boxes = r.boxes
      for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        cls = int(box.cls[0])  # Get class ID
        class_name = classNames[cls]

        if class_name == classNames[2]:  # Check if 'Rider'
          rider_detected = True
          cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

          # Only check for Helmet/No Helmet if rider is detected
          for inner_box in boxes:
            inner_x1, inner_y1, inner_x2, inner_y2 = inner_box.xyxy[0]
            inner_x1, inner_y1, inner_x2, inner_y2 = int(inner_x1), int(inner_y1), int(inner_x2), int(inner_y2)
            inner_cls = int(inner_box.cls[0])
            inner_class_name = classNames[inner_cls]

            if (inner_class_name == classNames[0] or inner_class_name == classNames[1]) and (
                (x1 < inner_x1 < x2 and y1 < inner_y1 < y2) or  # Check if inner box is within rider box
                (x1 < inner_x2 < x2 and y1 < inner_y2 < y2)
            ):
              cv2.rectangle(img, (inner_x1, inner_y1), (inner_x2, inner_y2), (0, 255 if inner_class_name == classNames[0] else 0, 255), 3)
              saveDetectedImageToCloud(img, class_name)
            

    if not rider_detected:
      # No rider detected, reset any previous labels
      pass  # Add logic to clear previous labels if needed
    
    
    yield img

  cap.release()
  cv2.destroyAllWindows()

def saveDetectedImageToCloud (img, class_name):
    timestamp = int(datetime.datetime.now().timestamp())
    filename = f'captured_image_{timestamp}.png'

    _, buffer = cv2.imencode('.png', img) 
    image_byte = io.BytesIO(buffer)

    bucket_name = 'aihelmetdetection'
    object_key = f'captured_image_{timestamp}.png'
    client.upload_fileobj(image_byte, bucket_name, object_key)
    # print(f'Image uploaded to R2 bucket: {bucket_name}/captured_image_{timestamp}.png')

    saveImageUrlToDb(filename)

def saveImageUrlToDb(filename):
    conn = get_db_connection()
    if conn:
            cur = conn.cursor()
            image_path=f'{bucket_url}/{filename}'

            cur.execute("INSERT INTO footage (image_url) VALUES (?)", (image_path,))
            conn.commit()
