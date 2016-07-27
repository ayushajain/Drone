import sys

reload(sys)
# append python module path for opencv and numpy
sys.path.append("/usr/lib/python2.7/site-packages")


from flask import Flask, render_template, Response
from SoloCamera import SoloCamera
import cv2

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        ret, frame = camera.read()
        converted, jpeg = cv2.imencode('.jpg', frame)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tostring() + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    cam = SoloCamera()
    return Response(gen(cam),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)