import cv2
import numpy
from multiprocessing import Pool
import subprocess as sp

raw_command = 'ffmpeg -protocol_whitelist file,udp,rtp -i sololink.sdp -f image2 -updatefirst 1 -pix_fmt rgb24 -vcodec rawvideo -'
command = raw_command.split(" ")

width = 1280
height = 720
channels = 3
pipe = None

def open_pipe():
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**6)

pool = Pool(processes=1)              # Start a worker processes.
result = pool.apply_async(open_pipe)

while True:
    print pipe
    if pipe is not None:
        print "yeet"
raw_image = pipe.stdout.read(height * width * channels)
image =  numpy.fromstring(raw_image, dtype='uint8')
image = image.reshape((height,width,channels))
cv2.imshow("test", image)

pipe.stdout.flush()
