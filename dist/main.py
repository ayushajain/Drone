import argparse
import cv2
from flashdetector import FlashDetector

ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="../CV Scripts/images/drone-updown-recog.MP4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=3, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")

args = vars(ap.parse_args())

PATTERN = "01010111"


def main():

    # start camera
    cap = cv2.VideoCapture(args['video'])

    # create our flash detector
    flash_detector = FlashDetector(PATTERN, args)

    while True:

        # Capture frame-by-frame
        ret, frame = cap.read()

        # quit video on keypress(q) or when videocapture ends
        if frame is None or cv2.waitKey(1) & 0xFF == ord('q'):
            break

        flash, image = flash_detector.identify_flash(frame)
        show_stats(image, flash)



        # display image
        cv2.imshow("FRAME", image)


    cap.release()
    cv2.destroyAllWindows()


def show_stats(frame, flash, dimensions=None):

    width, height, channels = frame.shape if dimensions is None else dimensions

    # draw crosshair
    cv2.line(frame, (0, height / 2), (width, height / 2), (0, 255, 255), 1)
    cv2.line(frame, (width / 2, 0), (width / 2, height), (0, 255, 255), 1)

    if flash is not None:
        cv2.line(frame, (width / 2, height / 2), (flash.x, flash.y), (255, 255, 255), 1)
        cv2.putText(frame, 'Error: ' + str(flash.distance_to(location=(width / 2, height / 2))), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

if __name__ == '__main__':
    main()
