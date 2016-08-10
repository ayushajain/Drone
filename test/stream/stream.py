import cv2, argparse

ap = argparse.ArgumentParser()
ap.add_argument("-t", "--time", required=False, default=20, help="interval in millisec")
args = vars(ap.parse_args())

while True:

    img = cv2.imread("img.bmp")
    if img is not None:
        cv2.imshow("test", img)

    img = None

    if cv2.waitKey(int(args["time"])) & 0xFF == ord('q'):
            break
