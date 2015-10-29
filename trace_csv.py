#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.6
#
# A cheeky little script for tracing the robot movements from a topdown viewpoint.
# 
# Example usage:
#  To run at 30fps:
#      trace.py 2015_EE1.csv -f 30
#
#  To export video:
#      trace.py 2015_EE1.csv -f 30 -video_file EE1.avi -n
#  
#  To save the final trace image:
#      trace.py 2015_EE1.csv -image_file EE1.png -n
#
# Options:
#   -max_height      : to adjust the scaling (in pixels)
#   -width & -height : adjusts the bounds of the lab floor (in milimetres) 
#   -codec           : specify a foucc video codec
#   -no_preview      : toggles previewing
#
#   -image_file and -video_file : enables output files
#

import cv2, sys, os, time, numpy as np, random
from eagleeye import Memset, EasyArgs, Key
from eagleeye.display_text import *

def usage():
    print "trace_csv.py [<csv files>] {-height | -width | -framerate | -max_height | -video_file | -codec | -image_file | -no_preview}"


def main(sysargs):
    args = EasyArgs(sysargs)
    
    if 'help' in args:
        usage()
        return 0
    
    # arg sanity checks
    if len(args) < 2:
        usage()
        return 1
    
    if args.no_preview and not args.video_file and not args.image_file:
        print "if -no_preview is toggled, you must a video or image output"
        usage()
        return 1
    
    # default args
    height = args.height or 3000        # milimetres
    width = args.width or 9000          # milimetres
    framerate = args.framerate or 44.94 # fps
    max_height = args.max_height or 400  # pixels
    
    # working vars
    scale = float(max_height) / height
    img_h = int(height * scale)
    img_w = int(width * scale)
    sleep_time = int((1.0 / framerate) * 1000) # in miliseconds
    
    # open video writer (if applicable)
    if 'video_file' in args:
        export = True
        codec = args.codec or 'DIVX'
        video  = cv2.VideoWriter(args.video_file, 
                                cv2.VideoWriter_fourcc(*codec), 
                                framerate, (img_w, img_h))
    else:
        export = False
    
    # open window
    window_name = "Tracer"
    cv2.namedWindow(window_name)
    print img_w, img_h
    
    # load up csvs
    csvs = {}
    for a in args[1:]:
        f = Memset(a)
        col = (55+random.random()*200,
               55+random.random()*200,
               55+random.random()*200)
        csvs[f] = col
        total = f.total
    
    # a frame to paste the trace on
    baseframe = np.zeros((img_h,img_w,3), np.uint8)
    
    # loopies
    for i in range(0, total):
        # a frame to draw dots and text, without affecting the trace frame
        dotframe = baseframe.copy()
        
        first = True
        for c in csvs:
            x = int(float(c.row()[2]))
            y = int(float(c.row()[3]))
            pt = (int(x*scale), img_h-int(y*scale))
                
            # draw
            cv2.circle(baseframe, pt, 1, csvs[c], 2)
            cv2.circle(dotframe, pt, 3, (255,255,255), 5)
            displayText(dotframe, "{}, {}".format(x, y), colour=csvs[c], top=first)
            
            # load next frame
            c.next()
            first = False
            
        # show and wait
        if not args.no_preview:
            cv2.imshow(window_name, dotframe)
            if cv2.waitKey(sleep_time) == Key.esc:
                break
        
        # save to video
        if export:
            video.write(dotframe)
        
        # console text
        sys.stdout.write("{}/{}\r".format(i, total))
        sys.stdout.flush()
        
    # write last still image
    if 'image_file' in args:
        cv2.imwrite(args.image_file, dotframe)
    
    # clean up
    if export:
        video.release()
    cv2.destroyAllWindows()
    print "\ndone"
    return 0


if __name__ == "__main__":
    exit(main(sys.argv))
