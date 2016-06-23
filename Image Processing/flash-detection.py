import argparse
import imutils
import numpy as np
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required = False, default = "foo", help = "Path to the image to be processed")
ap.add_argument("-t", "--threshold", required = False, default = 230, help = "Threshold limit")
ap.add_argument("-s", "--scale", required = False, default = 1, help = "Image scale size")
ap.add_argument("-b", "--blur", required = False, default = 15, help = "Blur amount")
ap.add_argument("-r", "--rotate", required = False, default = 0, help = "Image rotation amount")
ap.add_argument("-v", "--video", required = False, default = False, help = "Passing in a video parameter")

args = vars(ap.parse_args())

body_cascade = cv2.CascadeClassifier('/usr/local/Cellar/opencv3/3.1.0_1/share/OpenCV/haarcascades/haarcascade_fullbody.xml')

def performFilters(frame):

    # kernel for high pass filters
    kernel = np.ones((2,2),np.uint8)

    # Grayscale and Blurring
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray,(int(args["blur"]),int(args["blur"])),0)

    # Threshold Filters
    (T, binaryThresh) = cv2.threshold(blurred, float(args["threshold"]), 255, cv2.THRESH_BINARY)
    (T, toZeroInvThresh) = cv2.threshold(blurred, float(args["threshold"]), 255, cv2.THRESH_TOZERO_INV)

    mask = cv2.dilate(binaryThresh, None, iterations=5)

    body = body_cascade.detectMultiScale(gray, 1.3, 5)
    for (x,y,w,h) in body:
         cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)


    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts[0]:
        peri = cv2.arcLength(c, True);
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        if len(c) < 50 and len(c) > 5:
            cv2.drawContours(frame, [c], -1, (0,255,0), 2)

    filtered = {}
    filtered['binaryThresh'] = mask
    filtered['toZeroInvThresh'] = frame

    return filtered


if args["image"] is "foo" or args["video"]:
    cap = None

    if args["video"]:
        cap = cv2.VideoCapture(args["image"])
    else:
        cap = cv2.VideoCapture(0)
    
    w=int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH ))
    h=int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT ))
    # video recorder
    fourcc = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')  # cv2.VideoWriter_fourcc() does not exist
    out = cv2.VideoWriter("output.mp4", fourcc, 25, (w, h))

    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()

        result = performFilters(frame)
        # cv2.imshow('BINARY_FILTER', result['binaryThresh'])
        # cv2.imshow('TOZERO_INVERSE_FILTER', result['toZeroInvThresh'])
        
        out.write(result['toZeroInvThresh'])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
else:
    result = performFilters(cv2.resize(cv2.imread(args["image"]), (0,0), fx=float(args["scale"]), fy=float(args["scale"])))

    cv2.imshow('BINARY_FILTER', result['binaryThresh'])
    cv2.imshow('TOZERO_INVERSE_FILTER', result['toZeroInvThresh'])

    cv2.waitKey(0)


cap.release()
out.release()
cv2.destroyAllWindows()
