import os

command = "ffmpeg -protocol_whitelist file,udp,rtp -i sololink.sdp -y -vf fps=25 -f image2 -updatefirst 1 img.bmp"

def start():
    os.system(command)
