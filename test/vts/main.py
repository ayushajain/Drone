import argparse, cv2, shutil, signal, subprocess
from flashdetector import FlashDetector
from dronekit import *

# generate arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--video", required=False, default="../images/drone-updown-recog.mp4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=70, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.8, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=1, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")
args = vars(ap.parse_args())

# TEST: Temporary debugging variables
PATTERN = "01010111"
live = True


# location of where frames are being written from ffmpeg
stream_path = "video/"

# buffer for how many frames can be saved to hardrive at a time
BUFFER = 1

# interval between processing frames (should be a little bit below the bit frame rate due to processing lag)
wait_time = 190

fps = 16
stream_process = None
nc_process = None
correct_flash = None

# ffmpeg stream command
raw_netcat_command = "nc 10.1.1.1 5502"
raw_stream_command = "ffmpeg -protocol_whitelist file,udp,rtp -i sololink.sdp -y -vf fps=" + str(fps) + " -f image2 " + stream_path + "img%09d.bmp"


# Managing state for detecting and tracking location
# state = 0: detecting flash
# state = 1: tracking flash
# state = 2: lost flash -> scan and search
# state = 3: takeoff
# state = 4: gps navigation
state = 0

# connect to drone
vehicle = connect('udpin:0.0.0.0:14550',wait_ready=True)

# Camera resolution
horizontal_resolution = 1280
vertical_resolution = 720

# Camera FOV (radians) - References:
# https://gopro.com/support/articles/hero3-field-of-view-fov-information
# https://gopro.com/support/articles/video-resolution-settings-and-format
horizontal_fov = math.radians(118.2)
vertical_fov = math.radians(69.5)


def close_stream(signal_passed=None, frame=None):
    global stream_process

    os.killpg(os.getpgid(stream_process.pid), signal.SIGTERM)
    shutil.rmtree(stream_path)
    print "Closed Stream Safely"
    sys.exit(0)


def main():
    global stream_process

    # empty stream directory contents
    if os.path.exists(stream_path):
        shutil.rmtree(stream_path)
    os.makedirs(stream_path)

    # close stream on any sigints
    signal.signal(signal.SIGINT, close_stream)

    # begin grabbing frames from stream
    stream_process = subprocess.Popen(raw_netcat_command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
    stream_process = subprocess.Popen(raw_stream_command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

    # create our flash detector
    flash_detector = FlashDetector(PATTERN, args)
    frame, cap = None, None

    # start camera
    if not live:
        cap = cv2.VideoCapture(args['video'])

    arm_and_takeoff(15.24)
    print "detecting"

    while True:
        # Capture frame-by-frame
        files = os.listdir(stream_path)

        for x in range(0, len(files) - BUFFER):
            if x == len(files) - BUFFER - 1:
                frame = cv2.imread(stream_path + files[x])
                if frame is not None:

                    # perform visual targeting system on frames
                    vts(frame, flash_detector)

            # remove files from hard drive
            os.remove(stream_path + files[x])

        # quit video on keypress(q) or when video capture ends
        if cv2.waitKey(wait_time) & 0xFF == ord('q'):
            break

    if not live:
        cap.release()
    cv2.destroyAllWindows()

    # close stream safely
    close_stream()


def vts(frame, flash_detector):
    global state
    global correct_flash

    frame = cv2.resize(frame, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))
    frame_height, frame_width, frame_shape = frame.shape
    #compass = math.radians(vehicle.heading)

    if state == 0:
        flash, frame = flash_detector.identify_flash(frame)
        show_stats(frame, flash, 0)

        if flash is not None:
            state = 1
            correct_flash = flash
            del flash_detector.flash_rois[:]

    elif state == 1:
        temp_flash, frame = flash_detector.track(correct_flash, frame)
        show_stats(frame, temp_flash, 0)
        angle = math.degrees(math.atan2(0, -1) - math.atan2(correct_flash.x - frame_width / 2, correct_flash.y - frame_height / 2))
        if angle < 0:
            angle += 360

        if temp_flash is not None:
            send_land_message(temp_flash.x, temp_flash.y)
            correct_flash = temp_flash

    # display image
    cv2.imshow("FRAME", frame)


def send_land_message(x, y):
    """ lands the drone at target

    References: http://mavlink.org/messages/common#LANDING_TARGET

    Args:
        x:
        y:

    Returns:

    """
    print "Landing!!"
    msg = vehicle.message_factory.landing_target_encode(
        0,       # time_boot_ms (not used)
        0,       # target num
        0,       # frame
        (x - horizontal_resolution / 2) * horizontal_fov / horizontal_resolution,
        (y - vertical_resolution / 2) * vertical_fov / vertical_resolution,
        0,       # altitude.  Not supported.
        0,0)     # size of target in radians
    vehicle.send_mavlink(msg)
    #vehicle.flush()


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
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

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


def show_stats(frame, flash, rad):
    height, width, channels = frame.shape

    # find coordinates of NSEW vectors
    north = tuple(map(sum,zip(rotate_point(point=(0, height/2), rad=rad), (width/2, height/2))))
    south = tuple(map(sum,zip(rotate_point(point=(0, -height/2), rad=rad), (width/2, height/2))))
    east = tuple(map(sum, zip(rotate_point(point=(0, height/2), rad=rad + math.pi/2), (width / 2, height / 2))))
    west = tuple(map(sum, zip(rotate_point(point=(0, -height / 2), rad=rad + math.pi/2), (width / 2, height / 2))))

    # draw crosshair
    cv2.line(frame, north, south, (0, 255, 255), 1)
    cv2.line(frame, east, west, (0, 255, 255), 1)
    cv2.putText(frame, "N", north, cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255))

    # draw box around flash
    if flash is not None:
        cv2.line(frame, (width / 2, height / 2), (flash.x, flash.y), (0, 255, 255), 1)


def rotate_point(point, rad):
    x, y = point
    return int(round(y * math.sin(rad) + x * math.cos(rad))), -int(round(y * math.cos(rad) - x * math.sin(rad)))


if __name__ == '__main__':
    main()
