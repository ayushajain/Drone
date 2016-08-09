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
`sololink.sdp` provides the interface for grabbing stream directly from the solo
> Stream comes from udp://10.1.1.10:5600

`ffplay -protocol_whitelist file,udp,rtp sololink.sdp`  
> Use this to stream live video from the solo

`ffmpeg -protocol_whitelist file,udp,rtp -i sololink.sdp -codec copy -f mpegts output.mp4`
> Writes stream to file `output.mp4`