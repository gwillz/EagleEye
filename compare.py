#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.1.4
#
# Reads video and two datasets xml files
# then draws them over the video for comparison
# 

import sys, cv2, numpy as np, time, os
from eagleeye import BuffCap, Xmlset, EasyArgs, EasyConfig, CVFlag, Key

def usage():
    print "usage: python2 compare.py <video file> <xml dataset> <xml dataset>"
    exit(1)

args = EasyArgs()
config = EasyConfig(args.config, group="compare")

window_name = "EagleEye Comparator"
cv2.namedWindow(window_name)

if args.verifyLen(4):
    vid = BuffCap(args[1], buff_max=config.buffer_size)
    xml1 = Xmlset(args[2])
    xml2 = Xmlset(args[3])
    
    xml1.setRatio(vid.total)
    print 'ratio at:', xml1._ratio
    
    while vid.isOpened():
        frame = vid.frame()
        
        for name in xml1.data():
            obj = xml1.data()[name]
            
            pt1 = (int(float(obj['box']['x'])), int(float(obj['box']['y'])))
            pt2 = (pt1[0] + int(float(obj['box']['width'])), 
                    pt1[1] + int(float(obj['box']['height'])))
            
            centre = (int(float(obj['centre']['x'])), int(float(obj['centre']['y'])))
            
            cv2.rectangle(frame, pt1, pt2, config.xml1_colour, 1)
            cv2.circle(frame, centre, 1, config.xml1_colour, 2)
        
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(0)
        
        if key == Key.esc:
            print "exiting."
            exit(1)
        elif key == Key.right:
            if vid.next():
                xml1.next()
                xml2.next()
        elif key == Key.left:
            if vid.back():
                xml1.back()
                xml2.back()
    
    vid.release()
    cv2.destroyAllWindows()
else:
    usage()
    
exit(0)