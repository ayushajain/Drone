## Drone Information

Use `python flash-detection.py -i images/flashmovement.mov -t 220 -s 0.3 -b 25 -v True` to run flash-detection.py

##### 200fps 
`python flash-recognition.py -i images/200fps.MP4 -t 230 -s 0.5 -b 15 -v True`

### flash-detection.py flags
`-i` - image/video path relative to current directory  
`-t` - the binary threshold  
`-b` - the blur amount  
`-v` - using video  
`-s` - scaling  


For the other python files, just use `python filename`.
