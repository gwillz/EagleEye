#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.1.6
# 
# Processes a video and extracts singular frames for calibration.
# 

import sys, cv2, os
from eagleeye import EasyArgs, BuffSplitCap, Key, EasyConfig
from eagleeye.display_text import *

def usage():
    print "usage: python2 extract_frames.py <video file> <output image folder> {-split <left|right> | -prefix <output name> | --config <file>}"

def main(sysargs):
    # test args
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.config, group="chessboard_extract")
    if len(args) <= 2:
        usage()
        return 1

    # video settings, etc
    window_name = "Chessboard Extractor"
    side = BuffSplitCap.__dict__[args.split or 'right']
    rotate = BuffSplitCap.r0
    crop = (0,0,0,0)
    font = cv2.FONT_HERSHEY_SIMPLEX

    # image stuff
    image_path = os.path.join(args[2], args.prefix or 'frame_')
    if not os.path.exists(args[2]):
        os.makedirs(args[2])

    cv2.namedWindow(window_name)
    cap = BuffSplitCap(args[1], side=side, rotate=rotate, crop=crop, buff_max=cfg.buffer_size)

    # loop video file
    while cap.isOpened():
        frame = cap.frame()
        
        # display status
        textframe = frame.copy()
        displayText(textframe, cap.status(), top=True)
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
    return 0

if __name__ == '__main__':
    exit(main(sys.argv))
