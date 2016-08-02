import sys
reload(sys)
sys.path.append("/usr/lib/python2.7/site-packages")  # append python module path for opencv and numpy

import cv2
import argparse
import time
from flask import Flask, render_template, Response
from flashdetector import FlashDetector
from SoloCamera import SoloCamera

# parse arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--video", required=False, default="../CV Scripts/images/drone-updown-recog.mp4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=1, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")
args = vars(ap.parse_args())


PATTERN = "01010111"
timestamp = int(round(time.time() * 1000))


# Flask streaming
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    cam = SoloCamera()
    return Response(main(cam), mimetype='multipart/x-mixed-replace; boundary=frame')


def main(cap):
    global timestamp

    state = 0
    correct_flash = None

    # create our flash detector
    flash_detector = FlashDetector(PATTERN, args)

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if state == 0:
            flash, frame = flash_detector.identify_flash(frame)
            show_stats(frame, flash)

            if flash is not None:
                state = 1
                correct_flash = flash
                del flash_detector.flash_rois[:]
        elif state == 1:
            temp_flash, frame = flash_detector.track(correct_flash, frame)
            show_stats(frame, temp_flash)

            if temp_flash is not None:
                correct_flash = temp_flash
        """ Managing state for detecting and tracking location

            state = 0: detecting flash
            state = 1: tracking flash
            state = 2: lost flash -> scan and search
        """

        print_fps()

        # display to Flash server
        converted, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tostring() + b'\r\n\r\n')

    cap.stop()


def print_fps():
    global timestamp
    print 1000.0 / (timestamp - int(round(time.time() * 1000)))
    timestamp = int(round(time.time() * 1000))


def show_stats(frame, flash, dimensions=None):
    height, width, channels = frame.shape if dimensions is None else dimensions

    # draw crosshair
    cv2.line(frame, (0, height / 2), (width, height / 2), 0, 1)
    cv2.line(frame, (width / 2, 0), (width / 2, height), 0, 1)

    if flash is not None:
        cv2.line(frame, (width / 2, height / 2), (flash.x, flash.y), 255, 1)
        cv2.putText(frame, 'Error: ' + "{0:.5f}".format(flash.distance_to(location=(width / 2, height / 2))) + ' (x: ' + str(flash.x - width/2) + ', y: ' + str(flash.y - height/2) + ')', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255, 2)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    print "Hosted at: 10.1.1.10:5000"
