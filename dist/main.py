import argparse
import cv2
import numpy as np
from flashdetector import FlashDetector

ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="../CV Scripts/images/drone-updown-recog.mp4", help="Path to the video to be processed")
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

        if correct_flash is not None:
            # draw a box around the correct flash
            box_size = 20
            cv2.rectangle(frame, (correct_flash.x - box_size, correct_flash.y - box_size), (correct_flash.x + box_size, correct_flash.y + box_size), (0, 255, 0), 1)

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


if __name__ == '__main__':
    main()
