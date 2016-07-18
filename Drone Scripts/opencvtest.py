from __future__ import print_function
import time
import sys
import site

sys.path.append("/usr/lib/python2.7/site-packages")
print(site)

import cv2

def rgb_encode(red, green, blue):
    return 16 + (int(red*6) * 36) + (int(green*6) * 6) + int(blue*6)

def print_color(*args, **kwargs):
    fg = kwargs.pop('fg', None)
    bg = kwargs.pop('bg', None)

    set_color = ''
    if fg:
        set_color += '\x1b[38;5;%dm' % rgb_encode(*fg)
    if bg:
        set_color += '\x1b[48;5;%dm' % rgb_encode(*bg)
    print(set_color, end='')
    print(*args, **kwargs)
    print('\x1b[0m', end='')

# Open /dev/video2
vc = cv2.VideoCapture()
vc.open(2)

# Start our printing loop.
interval = .5
last = time.time()
while True:
    # Grab a frame. Then retrieve it from the buffer.
    vc.grab()
    ret, buf = vc.retrieve()
    if not ret:
        SystemExit('Could not retrieve image.')

    # Get a tuple of (r, g, b) as float values.
    rgb = [x/255.0 for x in cv2.mean(buf)[2::-1]]

    # Wait for our interval to have elapsed.
    next = time.time()
    if next - last < interval:
        time.sleep(interval - (next - last))
    last = time.time()

    # Print out hex color and a color strip.
    print('Average hex color: 0x%02X%02X%02X    ' % tuple([int(x*255) for x in rgb]), end='')
    print_color('          ', bg=rgb, end='')
    print(' ')
