import argparse
import cv2
import numpy as np

ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="images/drone-updown-recog.MP4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=3, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")

args = vars(ap.parse_args())

# kernel for blob dilation
# changing the dimensions affects size of dilation.
kernel = np.ones((5, 5), np.float32) / 25

frame = None


def main():
    # frame display/saving
    cap = cv2.VideoCapture(args["video"])


    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # end capture once video is over
        if frame is None:
            break

        result = perform_filters(frame)

        # display frames to window
        if result['binaryThresh'] is not None:
            cv2.imshow('BINARY_FILTER', result['binaryThresh'])
        cv2.imshow('ORIGINAL_FRAME', result['origFrame'])

        # quit video on keypress(q)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # close window and camera
    cap.release()
    cv2.destroyAllWindows()


def perform_filters(image):
    global frame

    # resize frame to reduce processing times
    image = cv2.resize(image, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))

    # Greyscale and Blurring to eliminate
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = cv2.GaussianBlur(gray, (int(args["blur"]), int(args["blur"])), 0)

    diff = None
    if frame is not None:
        diff = cv2.absdiff(mask, frame)
        (t, diff) = cv2.threshold(diff, float(args["threshold"]), 255, cv2.THRESH_BINARY)
        contours = cv2.findContours(diff.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours[0]:
             cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
             cv2.drawContours(diff, [c], -1, 255, 2)

    frame = mask

    # return processed frames
    return {'binaryThresh': diff, 'origFrame': image}


if __name__ == '__main__':
    main()
