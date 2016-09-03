import sys
reload(sys)
sys.path.append("/usr/lib/python2.7/site-packages")
sys.setdefaultencoding('ascii')
import cv2
import time
import threading
from SoloCamera import SoloCamera
from firebase import firebase
firebase = firebase.FirebaseApplication('https://solodata.firebaseio.com/', None)

cam = SoloCamera()
print cam
print "Capturing an image..."
ret, frame = cam.read()
if frame is None:
    print "shits is not workin"


interval = 10

while True:
    # Capture frame-by-frame
    ret, frame = cam.read()

    if interval < 0:

        firebase.post("", str(frame.tolist()))
        interval = 10

    interval -= 1

