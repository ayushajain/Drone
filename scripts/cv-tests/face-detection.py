import numpy as np
import cv2

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
face_cascade = cv2.CascadeClassifier('/usr/local/Cellar/opencv3/3.1.0_1/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml')

height, width, channels = frame.shape

fourcc = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (width, height))


while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()


    # Display the resulting frame
    out.write(frame)

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
out.release()
cv2.destroyAllWindows()
