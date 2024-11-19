from flask import Flask, redirect, render_template, Response,jsonify,request, send_from_directory,session, url_for

#FlaskForm--> it is required to receive input from the user
# Whether uploading a video file  to our object detection model
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from flask_cors import CORS

import mariadb
from wtforms import FileField, SubmitField,StringField,DecimalRangeField,IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired,NumberRange
import os

from storage import get_db_connection
# Required to run the YOLOv8 model
import cv2
# YOLO_Video is the python file which contains the code for our object detection model
#Video Detection is the Function which performs Object Detection on Input Video

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# print(os.getenv('MARIA_DB_PATH'))

with app.app_context():
    from yoloVid import video_detection
# app.config['UPLOAD_FOLDER'] = 'static/files'
is_running = False

#Use FlaskForm to get input video file  from user
class UploadFileForm(FlaskForm):
    #We store the uploaded video file path in the FileField in the variable file
    #We have added validators to make sure the user inputs the video in the valid format  and user does upload the
    #video when prompted to do so
    file = FileField("File",validators=[InputRequired()]) 
    submit = SubmitField("Run")


def generate_frames(path_x = ''):
    yolo_output = video_detection(path_x,True)
    for detection_ in yolo_output:
        ref,buffer=cv2.imencode('.jpg',detection_)

        frame=buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')

def generate_frames_web(path_x, is_run,confidence_lv):
    yolo_output = video_detection(path_x,is_run,confidenceLv=confidence_lv)
    for detection_ in yolo_output:
        ref,buffer=cv2.imencode('.jpg',detection_)

        frame=buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')

@app.route('/', methods=['GET','POST'])
@app.route('/home', methods=['GET','POST'])
def home():
    session.clear()
    return render_template('home.html')

@app.route('/gallery')
def gallery():
    session.clear()
    return render_template('gallery.html')
# Rendering the Webcam Rage
#Now lets make a Webcam page for the application
#Use 'app.route()' method, to render the Webcam page at "/webcam"
@app.route("/webcam", methods=['GET', 'POST'])
def webcam():
    if 'is_running' not in session:
        session['is_running'] = False  # default value
    return render_template('index.html', is_running=session['is_running'])

# @app.route('/FrontPage', methods=['GET','POST'])
# def front():
#     # Upload File Form: Create an instance for the Upload File Form
#     form = UploadFileForm()
#     if form.validate_on_submit():
#         # Our uploaded video file path is saved here
#         file = form.file.data
#         file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
#                                secure_filename(file.filename)))  # Then save the file
#         # Use session storage to save video file path
#         session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
#                                              secure_filename(file.filename))
#     return render_template('videoprojectnew.html', form=form)
@app.route('/video')
def video():
    is_running = True
    #return Response(generate_frames(path_x='static/files/bikes.mp4'), mimetype='multipart/x-mixed-replace; boundary=frame')
    if is_running is True:
        print("is running")
    return Response(generate_frames(path_x = session.get('video_path', None)),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webapp')
def webapp():
    is_running = session.get('is_running', False)
    selected_webcam = session.get('selected_webcam', 0)  # Default to webcam 0
    confidence_level = session.get('selected_conf_lv', 0.7)
    if is_running:
        # Use the selected webcam index
        return Response(generate_frames_web(is_run=is_running, path_x=selected_webcam,confidence_lv=confidence_level), 
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return send_from_directory('static/images', 'camera-off.svg')


@app.route('/set_selected_webcam', methods=['POST'])
def set_selected_webcam():
    data = request.get_json()
    webcam_id = data.get("webcam_id")

    if webcam_id is not None:
        session['selected_webcam'] = int(webcam_id)
        return jsonify({"message": "Webcam updated successfully"}), 200
    else:
        return jsonify({"error": "Invalid webcam ID"}), 400

@app.route('/set_conf_lv', methods=['POST'])
def set_conf_level():
    data = request.get_json()
    conf_lv = data.get("conf_lv")

    if conf_lv is not None:
        try:
            session['selected_conf_lv'] = float(conf_lv)
            return jsonify({"message": "Confidence level updated successfully"}), 200
        except ValueError:
            return jsonify({"error": "Invalid confidence level format"}), 400
    else:
        return jsonify({"error": "Confidence level not provided"}), 400


@app.route('/get_all_conf_lv_available', methods=['GET'])
def get_all_conf_lv_available():
    conf_lv = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99]
    return jsonify({"conf_lv": conf_lv}), 200



@app.route('/get_available_webcams', methods=['GET'])
def get_available_webcams():
    webcams = []
    for i in range(5):  # Check the first 10 indices for connected webcams
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            webcams.append({"id": i, "name": f"Webcam {i}"})
            cap.release()
    return jsonify(webcams), 200



@app.route('/toggle_webcam', methods=['POST'])
def toggle_webcam():
    # Toggle the 'is_running' value in the session
    session['is_running'] = not session.get('is_running', False)
    return redirect(url_for('webcam'))

@app.route('/get_capture_image', methods=['GET'])
def get_image():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Execute a query to get all image data from the `footage` table
            cur.execute("SELECT image_url, date FROM footage")
            rows = cur.fetchall()  # Fetch all rows from the result

            # Convert the result into a list of dictionaries
            images = [{"image_url": row[0], "date": row[1]} for row in rows]

            return jsonify(images), 200
        except mariadb.Error as e:
            return jsonify({"error": f"Failed to retrieve images: {e}"}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Failed to connect to the database."}), 500


if __name__ == "__main__":
    app.run(debug=True)