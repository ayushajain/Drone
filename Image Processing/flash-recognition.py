import argparse
from collections import Counter
from flash import Flash
import cv2
import numpy as np

ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="images/200fps.MP4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=230, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=15, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")

args = vars(ap.parse_args())

# bit pattern length
BIT_PATTERN_LENGTH = 8

# frame interval
FRAME_INTERVAL = 10

# kernel for blob dilation
# changing the dimensions affects size of dilation.
kernel = np.ones((5, 5), np.float32) / 25

# frame interval
frame_wait_time = FRAME_INTERVAL

# raw bits captured during processing
raw_bit_rate = []

# current pattern being processed
current_pattern = []

# single flash
flash = Flash()


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
        cv2.imshow('BINARY_FILTER', result['binaryThresh'])
        cv2.imshow('ORIGINAL_FRAME', result['origFrame'])

        # quit video on keypress(q)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # close window and camera
    cap.release()
    cv2.destroyAllWindows()


def perform_filters(image):
    global frame_wait_time

    # resize frame to reduce processing times
    image = cv2.resize(image, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))

    # Grayscale and Blurring to eliminate
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (int(args["blur"]), int(args["blur"])), 0)

    # Threshold Filters
    (t, mask) = cv2.threshold(blurred, float(args["threshold"]), 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Find contours on thresholded frame
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pixel = 0

    # iterate through all the contour shapes found
    for c in contours[0]:

        # grab information about contours
        moments = cv2.moments(c)
        center_x = 0
        center_y = 0
        try:
            # determine center of contour
            center_x = int((moments["m10"] / moments["m00"]))
            center_y = int((moments["m01"] / moments["m00"]))

            pixel = mask[center_y, center_x]

        except ZeroDivisionError:
            pass

        # draw contours to frame with a circle at the center
        cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
        cv2.circle(image, (center_x, center_y), 4, (0, 0, 255), -1)
        # cv2.putText(frame, str(len(approx)), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # pattern recognition
    raw_bit_rate.append(pixel)

    # add bit to pattern every 10 frames
    if frame_wait_time > 1:
        frame_wait_time -= 1
    else:
        current_pattern.append(pixel)
        frame_wait_time = FRAME_INTERVAL

    # add current pattern once bit length is reached
    if len(current_pattern) is BIT_PATTERN_LENGTH:
        flash.add_pattern(current_pattern)
        del current_pattern[:]

    # TEST: printing out data
    print current_pattern
    print flash.patterns
    print "Most Commonly Occurring Flash: " + flash.get_pattern()

    # return processed frames
    return {'binaryThresh': mask, 'origFrame': image}


if __name__ == '__main__':
    main()