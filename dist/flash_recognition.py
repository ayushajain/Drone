import sys
reload(sys)
# append python module path for opencv and numpy
sys.path.append("/usr/lib/python2.7/site-packages")
import argparse

# import local scripts and SoloCamera for drone video access
running_locally = False
from flash import Flash
try:
    from SoloCamera import SoloCamera
except OSError:
    running_locally = True

import cv2
import numpy as np


ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="../Image Processing/images/drone-updown-recog.MP4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=3, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")

args = vars(ap.parse_args())

# list of possible flashes
possible_flashes = []

# last frame for cv2.absoluteValue
last_frame = None

# frame count
frame_count = 0

# kernel for blob dilation
# changing the dimensions affects size of dilation.
kernel = np.ones((5, 5), np.float32) / 25

# TEST: get pattern from user
PATTERN = "01010111"


# TODO: create a state function for gps, flash detection/recognition, moving towards flash, regaining flash location
def main():

    # setup camera based on script run location
    cap = None
    if not running_locally:
        cap = SoloCamera()
    else:
        cap = cv2.VideoCapture(args['video'])

    ret, last_frame = cap.read()

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # end capture once video is over
        if frame is None:
            break

        filtered = perform_filters(frame)

        if len(filtered['ROIS']) > 0:
            identify_flash(filtered['ROIS'])
        draw_flashes(filtered['origFrame'])

        # display frames to window
        if running_locally:
            cv2.imshow('BINARY_FILTER', filtered['binaryThresh'])
            cv2.imshow('ORIGINAL_FRAME', filtered['origFrame'])

        # quit video on keypress(q)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # close window and camera
    cap.release()
    cv2.destroyAllWindows()


def perform_filters(image):
    global PATTERN
    global last_frame
    global frame_count

    # resize frame to reduce processing times
    image = cv2.resize(image, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))

    # Greyscale and Blurring to eliminate
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = cv2.GaussianBlur(gray, (int(args["blur"]), int(args["blur"])), 0)

    rois = []
    diff = None
    if last_frame is not None:
        diff = cv2.absdiff(mask, last_frame)
        (t, diff) = cv2.threshold(diff, float(args["threshold"]), 255, cv2.THRESH_BINARY)

        # Find contours on threshold frame
        contours = cv2.findContours(diff.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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

                rois.append({"location":(center_x, center_y), "value": gray[center_y][center_x]})

            except ZeroDivisionError:
                pass

            # draw contours to frame with a circle at the center
            cv2.circle(image, (center_x, center_y), 1, (0, 0, 255), -1)

    # update last frame to current one
    last_frame = mask
    frame_count += 1


    # return processed frames
    return {'binaryThresh': image if diff is None else diff, 'origFrame': image, 'ROIS': rois}


def draw_flashes(image):
    # identify and flashes
    for flash in possible_flashes:
        # print flash
        cv2.putText(image, str(flash.identity), (flash.x, flash.y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        if flash.equals_pattern(PATTERN):
            cv2.rectangle(image, (flash.x - 15, flash.y - 15), (flash.x + 15, flash.y + 15), (0, 255, 0), 2)


def identify_flash(regions_of_interest):

    # iterate through flash pixels found in current frame
    for roi in regions_of_interest:

        # determines whether a flash object has already been created for the current pixel
        flash_exists = False

        # iterate through the flashes we determined in previous frames
        for pf in possible_flashes:

            # TODO: change distance to pixel based on drone altitude and implement object tracking
            # mean-shift calculation here
            if pf.distance_to(roi['location']) < 30:
                flash_exists = True

                # push bit to flash and update location
                if pf.last_update != frame_count:
                    pf.last_update = frame_count
                    pf.push_raw_bits(roi['value'], 100)
                    pf.update_location(roi['location'])

        # define a flash object if one does not already exist
        if not flash_exists:
            possible_flashes.append(Flash(roi['location']))


if __name__ == '__main__':
    main()
