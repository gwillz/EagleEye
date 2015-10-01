#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.2.13
#
# Reads video and two datasets xml files
# then draws them over the video for comparison
# 

import sys, cv2, numpy as np, time, os
from eagleeye import BuffSplitCap, Xmlset, EasyArgs, EasyConfig, Key, marker_tool

def usage():
    print "usage: python2 compare.py <video file> <xml dataset> <xml dataset> {<mark_in> <mark_out> | -config <file> | -export <file>}"

def main(sysargs):
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.cfg, group="compare")
    font = cv2.FONT_HERSHEY_SIMPLEX
    window_name = "EagleEye Comparator"
    
    # grab marks from args
    if len(args) > 5:
        mark_in = args[4]
        mark_out = args[5]
        
        # test integer-ness
        try: int(mark_in) and int(mark_out)
        except: 
            usage()
            return 1
    
    # or grab them from a marker tool
    elif len(args) > 3:
        ret, mark_in, mark_out = marker_tool(args[1], 50, window_name)
        if not ret:
            print "Not processing - exiting."
            return 1
    else:
        usage()
        return 1
    
    # open video files
    vid = BuffSplitCap(args[1], buff_max=cfg.buffer_size)
    xml1 = Xmlset(args[2])
    xml2 = Xmlset(args[3])
    
    # trim the video
    vid.restrict(mark_in, mark_out)
    
    # trim the CSV
    cropped_total = mark_out - mark_in
    xml1.setRatio(cropped_total)
    print 'ratio at:', xml1._ratio
    
    # open export (if specified)
    if args.export:
        in_fps  = vid.get(cv2.CAP_PROP_FPS)
        in_size = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        out_vid = cv2.VideoWriter(args.export,
                                  cv2.VideoWriter_fourcc(*cfg.fourcc),
                                  in_fps, vid.shape[:2])
    else:
        cv2.namedWindow(window_name)
    
    while vid.isOpened():
        sys.stdout.write(vid.status() + "\r")
        sys.stdout.flush()
        
        frame = vid.frame()
        
        # get each object in the xml
        for name in xml1.data():
            obj = xml1.data()[name]
            
            pt1 = (int(float(obj['box']['x'])), 
                    int(float(obj['box']['y'])))
            pt2 = (pt1[0] + int(float(obj['box']['width'])), 
                    pt1[1] + int(float(obj['box']['height'])))
            
            centre = (int(float(obj['centre']['x'])), 
                    int(float(obj['centre']['y'])))
            
            cv2.rectangle(frame, pt1, pt2, cfg.xml1_colour, 1)
            cv2.circle(frame, centre, 1, cfg.xml1_colour, 2)
        
        # export or navigate
        if args.export:
            sys.stdout.write("{}/{}\r".format(vid.at(), cropped_total))
            sys.stdout.flush()
            
            out_vid.write(frame)
            
            if vid.next():
                xml1.next()
            else:
                print "end of video"
                break
        else:
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(0)
            
            # controls
            if key == Key.esc:
                print "exiting."
                return 1
            elif key == Key.right:
                if vid.next():
                    xml1.next()
                    xml2.next()
            elif key == Key.left:
                if vid.back():
                    xml1.back()
                    xml2.back()
    
    # clean up
    vid.release()
    if args.export:
        out_vid.release()
    else:
        cv2.destroyAllWindows()
        
    return 0
    
if __name__ == '__main__':
    exit(main(sys.argv))
