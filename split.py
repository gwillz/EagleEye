#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
#

import eagleeye as ee, sys, cv2

def usage():
    print "usage: split.py <in video> <out video> {-rotate <r0|r90|r180|r270> | -split <left|right|none> | -crop \"(N,E,S,W)\" }"

args = ee.EasyArgs()

if len(args) < 2:
    usage()
    exit(1)

crop = args.crop or (0, 0, 120, 0)
side = Theta.resolve(args.split or "Left")
rotate = ee.BuffSplitCap.__dict__[args.rotate or "r270"]

cap  = ee.BuffSplitCap(args[1], 
                       crop=crop, 
                       side=side, 
                       rotate=rotate)

fps  = cap.get(cv2.CAP_PROP_FPS)
size = list(cap.shape[:2])
if side != Theta.Both:
    size[1] /= 2
size[0] -= crop[0] - crop[2]
size[1] -= crop[1] - crop[3]

out  = cv2.VideoWriter(args[2], 
                        cv2.VideoWriter_fourcc(*'DIVX'), 
                        fps, tuple(size))

print "in: {} at {}".format(size, fps)

while True:
    out.write(cap.frame())
    sys.stdout.write(cap.status() + "\r")
    sys.stdout.flush()
    
    if cap.at() == 50:
        break
    
    if not cap.next():
        break
        

cap.release()
out.release()

print "\nDone."
exit(0)