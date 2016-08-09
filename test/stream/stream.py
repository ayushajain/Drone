import cv2
import capture

#capture.start()

while True:
    img = cv2.imread('img.bmp')
    if img is not None:
        cv2.imshow("test", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
