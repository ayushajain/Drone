Visual Targetting System
=======================
### Project Structure

    .
    ├── dist                                 
    ├── test
    │   ├── cv-tests
    │   ├── solo-flight
    │   ├── stream
    │   └── vts
    ├── Drone-Flash Android
    ├── LICENSE
    └── README.md

> Scripts are specific to the 3DR Solo


### Streaming
Connect to the solo's controller by running: `nc 10.1.1.1 5502`  
`sololink.sdp` provides the interface for grabbing stream directly from the solo
> Stream comes from udp://10.1.1.10:5600

`ffplay -protocol_whitelist file,udp,rtp sololink.sdp`  
> Use this to stream live video from the solo

`ffmpeg -protocol_whitelist file,udp,rtp -i sololink.sdp -y  -f image2 -updatefirst 1 img.bmp`
> Writes stream to file `img.bmp`