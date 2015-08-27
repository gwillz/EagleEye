#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.1.1
# 
# Processes a video and extracts singular frames for calibration.
# 

import sys, cv2, os
from eagleeye import EasyArgs, BuffSplitCap, Key, CVFlag, EasyConfig

def usage():
    print "usage: python2 extract_frames.py <video file> <output image folder> [-prefix <output name>]"


# test args
args = EasyArgs()
config = EasyConfig(args.config, group="calib")
if not args.verifyLen(3):
    usage()
    exit(1)

# video settings, etc
window_name = "Chessboard Extractor"
side = BuffSplitCap.__dict__[config.side]
rotate = BuffSplitCap.__dict__[config.rotate]
font = CVFlag.FONT_HERSHEY_SIMPLEX

# image stuff
image_path = os.path.join(args[2], args.prefix or 'frame_')
if not os.path.exists(args[2]):
    os.makedirs(args[2])

cv2.namedWindow(window_name)
cap = BuffSplitCap(args[1], side=side, rotate=rotate, buff_max=config.buffer_size)

# loop video file
while cap.isOpened():
    frame = cap.frame()
    
    # display status
    textframe = frame.copy()
    cv2.putText(textframe, cap.status(),
                (5,15), font, config.font_size, config.font_colour, config.font_thick, CVFlag.LINE_AA)
    cv2.imshow(window_name, textframe)
    
    # controls
    key = cv2.waitKey(0)
    if key == Key.right:
        cap.next()
    elif key == Key.left:
        cap.back()
    elif key == Key.enter:
        print "Snapped at: ", cap.at()
        cv2.imwrite("{}{:02d}.jpg".format(image_path, cap.at()), frame)
    elif key == Key.esc:
        print "Quitting."
        break

# clean up
cap.release()
cv2.destroyAllWindows()

print "\nDone."
exit(0)
