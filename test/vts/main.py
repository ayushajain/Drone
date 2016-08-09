import argparse
import cv2
import math
from flashdetector import FlashDetector

# generate arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--video", required=False, default="../../CV Scripts/images/drone-updown-recog.mp4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=1, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")
args = vars(ap.parse_args())

PATTERN = "01010111"


def main():
    # start camera
    cap = cv2.VideoCapture(args['video'])

    ret, frame = cap.read()

    state = 0
    """ Managing state for detecting and tracking location
    state = 0: detecting flash
    state = 1: tracking flash
    state = 2: lost flash -> scan and search
    """

    correct_flash = None

    # create our flash detector
    flash_detector = FlashDetector(PATTERN, args)

    while True:

        # Capture frame-by-frame
        ret, frame = cap.read()

        # quit video on keypress(q) or when videocapture ends
        if frame is None or cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame = cv2.resize(frame, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))
        frame_height, frame_width, frame_shape = frame.shape
        compass = math.radians(40)  # TODO: get compass direction from drone

        if state == 0:
            flash, frame = flash_detector.identify_flash(frame)
            show_stats(frame, flash, compass)

            if flash is not None:
                state = 1
                correct_flash = flash
                del flash_detector.flash_rois[:]
        elif state == 1:
            temp_flash, frame = flash_detector.track(correct_flash, frame)
            show_stats(frame, temp_flash, compass)

            angle = math.degrees(math.atan2(0, -1) - math.atan2(correct_flash.x - frame_width/2, correct_flash.y - frame_height/2))
            if angle < 0:
                angle += 360
            print angle

            if temp_flash is not None:
                correct_flash = temp_flash

        # display image
        cv2.imshow("FRAME", frame)

    cap.release()
    cv2.destroyAllWindows()


def calculate_error(flash, rad, altitude, dimensions):
    height, width, channels = dimensions

    x = flash.x - width/2
    y = flash.y - height/2
    error_x = round(y * math.sin(rad) + x * math.cos(rad))
    error_y = -round(y * math.cos(rad) - x * math.sin(rad))

    print error_x, error_y

    pix_to_meter_const = 260
    return error_x * altitude / pix_to_meter_const, error_y * altitude / pix_to_meter_const


def show_stats(frame, flash, rad, dimensions=None):
    height, width, channels = frame.shape if dimensions is None else dimensions

    # draw crosshair
    north = tuple(map(sum,zip(rotate_point(point=(0, height/2), rad=rad), (width/2, height/2))))
    south = tuple(map(sum,zip(rotate_point(point=(0, -height/2), rad=rad), (width/2, height/2))))
    east = tuple(map(sum, zip(rotate_point(point=(0, height/2), rad=rad + math.pi/2), (width / 2, height / 2))))
    west = tuple(map(sum, zip(rotate_point(point=(0, -height / 2), rad=rad + math.pi/2), (width / 2, height / 2))))

    cv2.line(frame, north, south, (0, 255, 255), 1)
    cv2.line(frame, east, west, (0, 255, 255), 1)
    cv2.putText(frame, "N", north, cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255))

    if flash is not None:
        cv2.line(frame, (width / 2, height / 2), (flash.x, flash.y), (0, 255, 255), 1)


def rotate_point(point, rad):
    x, y = point
    return int(round(y * math.sin(rad) + x * math.cos(rad))), -int(round(y * math.cos(rad) - x * math.sin(rad)))

if __name__ == '__main__':
    main()
