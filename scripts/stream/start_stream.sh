ffmpeg -protocol_whitelist file,udp,rtp -i sololink.sdp -y -vf fps=16 -f image2 -updatefirst 1 stream.bmp
