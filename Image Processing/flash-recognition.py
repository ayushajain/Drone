import argparse
import imutils
import numpy as np
import cv2
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required = False, default = "foo", help = "Path to the image to be processed")
ap.add_argument("-t", "--threshold", required = False, default = 230, help = "Threshold limit")
ap.add_argument("-s", "--scale", required = False, default = 1, help = "Image scale size")
ap.add_argument("-b", "--blur", required = False, default = 15, help = "Blur amount")
ap.add_argument("-r", "--rotate", required = False, default = 0, help = "Image rotation amount")
ap.add_argument("-v", "--video", required = False, default = False, help = "Passing in a video parameter")

args = vars(ap.parse_args())
kernel = np.ones((5,5),np.float32)/25

initialDelay = 4
frameWaitTime = 10
rawBitRate = []
patterns = []
currPattern = []

def printData(patterns):
    data = Counter(tuple(patterns))
    mostCommonPattern = data.most_common(1)

    if len(mostCommonPattern) > 0:
        mostCommonPattern = mostCommonPattern[0]
        print "Most Commonly Occuring Pattern: " + str(mostCommonPattern[0])
        print "Accuracy: " + str(mostCommonPattern[1] / float(len(patterns)))


def getAverageBrightness(frame):
    val = cv2.mean(frame)
    return val

def patternToBinary(pattern):
    stringPattern = ""

    for i in pattern:
        stringPattern += ("1" if i is not 0 else "0")

    return stringPattern


def performFilters(frame):
    global frameWaitTime
    global initialDelay

    frame = cv2.resize(frame, (0,0), fx=float(args["scale"]), fy=float(args["scale"]))

    # Grayscale and Blurring to eliminate
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray,(int(args["blur"]),int(args["blur"])),0)

    # Threshold Filters
    # avgBrightness = getAverageBrightness(blurred)
    (T, mask) = cv2.threshold(blurred, float(args["threshold"]), 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask,kernel,iterations = 1)

    ######### MEMORY INTENSIVE ALGORITHMS ########

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pixel = 0

    for c in cnts[0]:
        peri = cv2.arcLength(c, True);
        approx = cv2.approxPolyDP(c, 0.01 * peri, True)
        M = cv2.moments(c)
        cX = 0
        cY = 0
        try:
            cX = int((M["m10"] / M["m00"]))
            cY = int((M["m01"] / M["m00"]))

            pixel = mask[cY, cX]

        except:
            None

        cv2.drawContours(frame, [c], -1, (0,255,0), 2)
        cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)
        # cv2.putText(frame, str(len(approx)), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


    # save output of single bitoutput

    # pattern recognition
    if initialDelay < 0:
        rawBitRate.append(pixel)

        if frameWaitTime > 0:
            frameWaitTime -= 1
        else:
            currPattern.append(pixel)
            frameWaitTime = 9

        if len(currPattern) is 8:
            patterns.append(patternToBinary(currPattern))
            del currPattern[:]

        print currPattern
        print patterns
        printData(patterns)

    initialDelay -= 1

    ###############################################

    filtered = {}
    filtered['binaryThresh'] = mask
    filtered['origFrame'] = frame

    return filtered






# frame display/saving

if args["image"] is "foo" or args["video"]:

    cap = cv2.VideoCapture(args["image"])


    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()

        result = performFilters(frame)
        cv2.imshow('BINARY_FILTER', result['binaryThresh'])
        cv2.imshow('ORIGINAL_FRAME', result['origFrame'])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break




cap.release()
cv2.destroyAllWindows()
