import argparse
import cv2
import numpy as npq
from flash import Flash

ap = argparse.ArgumentParser()

# generate arguments
ap.add_argument("-i", "--video", required=False, default="images/drone-updown-recog.MP4", help="Path to the video to be processed")
ap.add_argument("-t", "--threshold", required=False, default=230, help="Threshold limit")
ap.add_argument("-s", "--scale", required=False, default=0.5, help="Image scale size")
ap.add_argument("-b", "--blur", required=False, default=15, help="Blur amount")
ap.add_argument("-r", "--rotate", required=False, default=0, help="Image rotation amount")

args = vars(ap.parse_args())

# bit pattern length
BIT_PATTERN_LENGTH = 8

# frame interval
FRAME_INTERVAL = 5

# kernel for blob dilation
# changing the dimensions affects size of dilation.
kernel = np.ones((5, 5), np.float32) / 25

# frame interval
frame_wait_time = FRAME_INTERVAL

# single flash
flashes = []

# update values for each flash to make sure that bits aren't pushed repeatedly
update_count = 0

# TEST: flash identity
flash_identity = 0

# TEST: get pattern from user
PATTERN = "01010111"


# TODO: create a state function for gps, flash detection/recognition, moving towards flash, regaining flash location
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
    global flash_identity
    global frame_wait_time
    global PATTERN
    global update_count

    # resize frame to reduce processing times
    image = cv2.resize(image, (0, 0), fx=float(args["scale"]), fy=float(args["scale"]))

    # Greyscale and Blurring to eliminate
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (int(args["blur"]), int(args["blur"])), 0)

    # Threshold Filters
    (t, mask) = cv2.threshold(blurred, float(args["threshold"]), 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Find contours on threshold frame
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pixels = []

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

            pixels.append({"location":(center_x, center_y), "value":mask[center_y][center_x]})

        except ZeroDivisionError:
            pass

        # draw contours to frame with a circle at the center
        # cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
        cv2.circle(image, (center_x, center_y), 4, (0, 0, 255), -1)
        # cv2.putText(frame, str(len(approx)), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # identify and flashes
    for flash in flashes:
        print flash
        cv2.putText(image, str(flash.identity), (flash.x, flash.y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        if flash.equals_pattern(PATTERN):
            cv2.rectangle(image, (flash.x - 15, flash.y - 15), (flash.x + 15, flash.y + 15), (0, 255, 0), 2)

    # pattern recognition
    # add bit to pattern every n frames
    if frame_wait_time > 1:
        frame_wait_time -= 1
    else:

        # iterate through flash pixels found in current frame
        for pixel in pixels:

            # determines whether a flash object has already been created for the current pixel
            flash_exists = False

            # iterate through the flashes we determined in previous frames
            for flash in flashes:

                # TODO: change distance to pixel based on drone altitude and implement object tracking
                # mean-shift calculation here
                if flash.distance_to(pixel['location']) < 10:
                    flash_exists = True

                    # push on bit to flash and update location
                    if flash.last_update != update_count:
                        flash.last_update = update_count
                        flash.push_raw_bits(255)
                        flash.update_location(pixel['location'])

            # define a flash object if one does not already exist
            if not flash_exists:
                flashes.append(Flash(pixel['location'], str(flash_identity)))
                flash_identity += 1

        # push off bit to flash if necessary
        for flash in flashes:
            if flash.last_update != update_count:
                flash.last_update = update_count
                flash.push_raw_bits(0)

        frame_wait_time = FRAME_INTERVAL

    # TEST: prevents overlapped bits in a flash
    update_count += 1

    # return processed frames
    return {'binaryThresh': mask, 'origFrame': image}


if __name__ == '__main__':
    main()
