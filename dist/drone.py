import sys
reload(sys)
sys.path.append("/usr/lib/python2.7/site-packages")  # append python module path for opencv and numpy

import cv2, argparse, time as pytime, math
from flask import Flask, render_template, Response
from flashdetector import FlashDetector
from SoloCamera import SoloCamera
from dronekit import connect, time, VehicleMode


# Connect to UDP endpoint (and wait for default attributes to accumulate)
target = sys.argv[1] if len(sys.argv) >= 2 else 'udpin:0.0.0.0:14550'
print 'Connecting to ' + target + '...'
vehicle = connect(target, wait_ready=False)

# parse arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--video", required=False, default="../CV Scripts/images/drone-updown-recog.mp4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.6, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=3, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")
args = vars(ap.parse_args())


PATTERN = "01010111"
timestamp = int(round(pytime.time() * 1000))

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

        frame = cv2.resize(frame, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))

        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        compass = math.radians(360 - vehicle.heading) # get drone altitude

        if state == 0:
            flash, frame = flash_detector.identify_flash(frame)
            show_stats(frame, flash, compass)

            if flash is not None:
                print "############## Detected Flash ###################"
                state = 1
                correct_flash = flash
                del flash_detector.flash_rois[:]

        elif state == 1:
            temp_flash, frame = flash_detector.track(correct_flash, frame)
            show_stats(frame, correct_flash, compass)

            print correct_flash.identity
            # distance between drone and

            error_x, error_y = calculate_error(correct_flash, compass, 10, frame.shape)

            if temp_flash is not None:
                correct_flash = temp_flash


        """ Managing state for detecting and tracking location

            state = 0: detecting flash
            state = 1: tracking flash
            state = 2: lost flash -> scan and search  """

        print_fps()

        # display to Flash server
        converted, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tostring() + b'\r\n\r\n')

    cap.stop()


def print_fps():
    global timestamp
    print "fps: " + str(1000.0 / -(timestamp - int(round(pytime.time() * 1000))))
    timestamp = int(round(pytime.time() * 1000))


def calculate_error(flash, rad, altitude, dimensions):
    height, width, channels = dimensions

    x = flash.x - width/2
    y = flash.y - height/2
    error_x = round(y * math.sin(rad) + x * math.cos(rad))
    error_y = -round(y * math.cos(rad) - x * math.sin(rad))

    pix_to_meter_const = 260

    return error_x * altitude / pix_to_meter_const, error_y * altitude / pix_to_meter_const


def show_stats(frame, flash, rad, dimensions=None):
    height, width, channels = frame.shape

    # draw crosshair
    north = tuple(map(sum,zip(rotate_point(point=(0, height/2), rad=rad), (width/2, height/2))))
    south = tuple(map(sum,zip(rotate_point(point=(0, -height/2), rad=rad), (width/2, height/2))))
    east = tuple(map(sum, zip(rotate_point(point=(0, height/2), rad=rad + math.pi/2), (width / 2, height / 2))))
    west = tuple(map(sum, zip(rotate_point(point=(0, -height / 2), rad=rad + math.pi/2), (width / 2, height / 2))))

    cv2.line(frame, north, south, (0, 255, 255), 1)
    cv2.line(frame, east, west, (0, 255, 255), 1)
    cv2.putText(frame, "N", north, cv2.FONT_HERSHEY_PLAIN, 1, (255))

    if flash is not None:
        cv2.line(frame, (width / 2, height / 2), (flash.x, flash.y), (0, 255, 255), 1)


def rotate_point(point, rad):
    x, y = point
    return int(round(y * math.sin(rad) + x * math.cos(rad))), -int(round(y * math.cos(rad) - x * math.sin(rad)))


def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    print "Basic pre-arm checks"
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print " Waiting for vehicle to initialise..."
        time.sleep(1)

    print "Arming motors"
    # Copter should arm in GUIDED mode
    vehicle.mode    = VehicleMode("GUIDED")
    vehicle.armed   = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print " Waiting for arming..."
        time.sleep(1)

    print "Taking off!"
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude NOTE: asynchronous method

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print " Altitude: ", vehicle.location.global_relative_frame.alt
        #Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
            print "Reached target altitude"
            break
        time.sleep(1)

if __name__ == '__main__':
    #cam = SoloCamera()
    #main(cam)
    arm_and_takeoff(10)
    app.run(host='0.0.0.0', debug=True)
