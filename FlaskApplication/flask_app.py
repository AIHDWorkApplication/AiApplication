from flask import Flask, redirect, render_template, Response,jsonify,request, send_from_directory,session, url_for

#FlaskForm--> it is required to receive input from the user
# Whether uploading a video file  to our object detection model

from flask_wtf import FlaskForm


from wtforms import FileField, SubmitField,StringField,DecimalRangeField,IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired,NumberRange
import os


# Required to run the YOLOv8 model
import cv2

# YOLO_Video is the python file which contains the code for our object detection model
#Video Detection is the Function which performs Object Detection on Input Video
from yoloVid import video_detection
app = Flask(__name__)

app.config['SECRET_KEY'] = 'testName123'
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

def generate_frames_web(path_x, is_run):
    yolo_output = video_detection(path_x,is_run)
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
    if is_running:
        # Generate frames if the camera is on
        return Response(generate_frames_web(is_run=is_running, path_x=0), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        # Serve a static image if the camera is off
        return send_from_directory('static/images', 'camera-off.svg')



@app.route('/toggle_webcam', methods=['POST'])
def toggle_webcam():
    # Toggle the 'is_running' value in the session
    session['is_running'] = not session.get('is_running', False)
    return redirect(url_for('webcam'))



if __name__ == "__main__":
    app.run(debug=True)