#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders, Kin Kuen Liu
# version 0.0.1
#
# Compares any corresponding image points to reprojected points
# And calculate and display the reprojection error
# 

import sys, cv2, numpy as np, time, os
from eagleeye import BuffCap, Xmlset, EasyArgs, EasyConfig, Key, marker_tool

def usage():
    print "usage: python2 compare_trainer.py <video file> <trainer xml> <mapper xml> {<mark_in> <mark_out> | -config <file> | -export <file>}"

def main(sysargs):
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.cfg, group="compare_trainer")
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
    vid = BuffCap(args[1], buff_max=cfg.buffer_size)
    trainer_xml = Xmlset(args[2])
    mapper_xml = Xmlset(args[3])
    
    cropped_total = mark_out - mark_in
    mapper_xml.setRatio(cropped_total)
    print 'ratio at:', mapper_xml._ratio
    
    # open export (if specified)
    if args.export:
        in_fps  = vid._cap.get(cv2.CAP_PROP_FPS)
        in_size = (int(vid._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(vid._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        out_vid = cv2.VideoWriter(args.export,
                                  cv2.VideoWriter_fourcc(*cfg.fourcc),
                                  in_fps, vid.shape[:2])
    else:
        cv2.namedWindow(window_name)
    
    count = 0
    while vid.isOpened():
        count += 1
        
        # restrict to flash marks
        if count <= mark_in: 
            vid.next()
            continue
        
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
            sys.stdout.write("{}/{}\r".format(count, cropped_total))
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
