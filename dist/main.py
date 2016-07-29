import argparse
import cv2
import numpy as np
from flashdetector import FlashDetector

ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="../CV Scripts/images/drone-updown-recog.mp4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=3, help="Blur amount")
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

    term_crit = None
    correct_flash = None
    track_window = None
    roi_hist = None

    # create our flash detector
    flash_detector = FlashDetector(PATTERN, args)

    while True:

        # Capture frame-by-frame
        ret, frame = cap.read()
        frame = cv2.resize(frame, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))

        # quit video on keypress(q) or when videocapture ends
        if frame is None or cv2.waitKey(1) & 0xFF == ord('q'):
            break


        if state == 0:
            flash, image = flash_detector.identify_flash(frame)
            show_stats(image, flash)

            if flash is not None:
                state = 1
                term_crit, roi_hist, track_window = get_termcrit(track_window=(flash.x, flash.y, 10, 10), frame=frame)
                correct_flash = flash
        elif state == 1:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            dst = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)
            ret, track_window = cv2.meanShift(dst, track_window, term_crit)
            x, y, w, h = track_window
            cv2.rectangle(frame, (x, y), (x + w, y + h), 255, 2)

        # display image
        cv2.imshow("FRAME", frame)

    cap.release()
    cv2.destroyAllWindows()


def show_stats(frame, flash, dimensions=None):

    height, width, channels = frame.shape if dimensions is None else dimensions

    # draw crosshair
    cv2.line(frame, (0, height / 2), (width, height / 2), (0, 255, 255), 1)
    cv2.line(frame, (width / 2, 0), (width / 2, height), (0, 255, 255), 1)

    if flash is not None:
        cv2.line(frame, (width / 2, height / 2), (flash.x, flash.y), (0, 255, 255), 1)
        cv2.putText(frame, 'Error: ' + "{0:.5f}".format(flash.distance_to(location=(width / 2, height / 2))) + ' (x: ' + str(flash.x - width/2) + ', y: ' + str(flash.y - height/2) + ')', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


def get_termcrit(track_window, frame):
    col, row, width, height = track_window

    roi = frame[row:row + height, col:col + width]
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_roi, np.array((0., 30., 32.)), np.array((180., 255., 255.)))
    roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180])
    cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
    return (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1), roi_hist, track_window


if __name__ == '__main__':
    main()
