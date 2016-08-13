import os, shutil, subprocess, signal, sys, cv2

stream_path = "video"
fps = 16

# ffmpeg stream command
raw_command = "ffmpeg -protocol_whitelist file,udp,rtp -i sololink.sdp -y -vf fps=" + str(fps) + " -f image2 " + stream_path + "/img%09d.bmp"


def signal_handler(signal1, frame):
    os.killpg(os.getpgid(stream_process.pid), signal.SIGTERM)
    shutil.rmtree(stream_path)
    print "closing safely"
    sys.exit(0)


if __name__ == "__main__":
    # empty stream directory contents
    if os.path.exists(stream_path):
        shutil.rmtree(stream_path)
    os.makedirs(stream_path)

    signal.signal(signal.SIGINT, signal_handler)

    # begin grabbing frames from stream
    stream_process = subprocess.Popen(raw_command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

    while True:
        files = os.listdir(stream_path)
        for x in range(0, len(files) - 1):
            if x == len(files) - 2:
                img = cv2.imread(stream_path + "/" + files[x])
                if img is not None:
                    cv2.imshow("breh", img)
                    cv2.waitKey(100)
            os.remove(stream_path + "/" + files[x])
        #print os.listdir(stream_path)


    # close stream safely
    os.killpg(os.getpgid(stream_process.pid), signal.SIGTERM)
    shutil.rmtree(stream_path)
    print "closing safely"


