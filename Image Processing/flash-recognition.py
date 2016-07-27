import argparse
import cv2
import numpy as np
from flash import Flash

ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="images/drone-updown-recog.MP4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=40, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=3, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")

args = vars(ap.parse_args())

# bit pattern length
BIT_PATTERN_LENGTH = 8

# frame interval
FRAME_INTERVAL = 5

# kernel for blob dilation
# changing the dimensions affects size of dilation.
kernel = np.ones((5, 5), np.float32) / 25

# single flash
flashes = []

# last frame for cv2.absoluteValue
last_frame = None

# frame count
frame_count = 0

# TEST: flash identity
flash_identity = 0

# TEST: get pattern from user
PATTERN = "01010111"


# TODO: create a state function for gps, flash detection/recognition, moving towards flash, regaining flash location
def main():
    # frame display/saving
    cap = cv2.VideoCapture(args['video'])

    ret, frame = cap.read()
    print frame.tolist()

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

    pixels = []
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

                pixels.append({"location":(center_x, center_y), "value": gray[center_y][center_x]})

            except ZeroDivisionError:
                pass

            # draw contours to frame with a circle at the center
            cv2.circle(image, (center_x, center_y), 1, (0, 0, 255), -1)

    # update last frame to current one
    last_frame = mask
    frame_count += 1


    # return processed frames
    return {'binaryThresh': image if diff is None else diff, 'origFrame': image, 'ROIS': pixels}


def draw_flashes(image):
    # identify and flashes
    for flash in flashes:
        # print flash
        cv2.putText(image, str(flash.identity), (flash.x, flash.y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        if flash.equals_pattern(PATTERN):
            cv2.rectangle(image, (flash.x - 15, flash.y - 15), (flash.x + 15, flash.y + 15), (0, 255, 0), 2)


def identify_flash(regions_of_interest):
    global flash_identity

    # iterate through flash pixels found in current frame
    for roi in regions_of_interest:

        # determines whether a flash object has already been created for the current pixel
        flash_exists = False

        # iterate through the flashes we determined in previous frames
        for flash in flashes:

            # TODO: change distance to pixel based on drone altitude and implement object tracking
            # mean-shift calculation here
            if flash.distance_to(roi['location']) < 30:
                flash_exists = True

                # push bit to flash and update location
                if flash.last_update != frame_count:
                    flash.last_update = frame_count
                    flash.push_raw_bits(roi['value'])
                    flash.update_location(roi['location'])

        # define a flash object if one does not already exist
        if not flash_exists:
            flashes.append(Flash(roi['location'], str(flash_identity)))
            flash_identity += 1


if __name__ == '__main__':
    main()
