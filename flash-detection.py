import numpy as np
import cv2

cap = cv2.VideoCapture(0)

THRESHOLD = 240

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    kernel = np.ones((2,2),np.uint8)


    # Grayscale and Blurring
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray,(15,15),0)

    # Threshold Filters
    (T, binaryThresh) = cv2.threshold(blurred, THRESHOLD, 255, cv2.THRESH_BINARY)
    (T, toZeroInvThresh) = cv2.threshold(blurred, THRESHOLD, 255, cv2.THRESH_TOZERO_INV)

    # Laplacian Filter
    laplacian = cv2.Laplacian(blurred, cv2.CV_64F)

    opening = cv2.morphologyEx(binaryThresh, cv2.MORPH_OPEN, kernel)

    # Display the resulting frame
    cv2.imshow('BINARY_FILTER', binaryThresh)
    cv2.imshow('TOZERO_INVERSE_FILTER', opening)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
