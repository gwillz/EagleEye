#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.5
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

import cv2, sys, os, numpy as np, random
from eagleeye import EasyArgs, Key
from python_vicon import PyVicon

def usage():
    print "usage: live_tracer.py <object_name> {-height | -width | -framerate | -max_height | -video_file | -codec | -image_file | -no_preview}"

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
    framerate = args.framerate or 30    # fps
    max_height = args.max_height = 400  # pixels
    ip_address = args.ip_address or "192.168.10.1"
    port = 801
    target = args[1]

    # working vars
    scale = float(max_height) / height
    img_h = int(height * scale)
    img_w = int(width * scale)
    sleep_time = int((1.0 / framerate) * 1000) # in miliseconds

    # open video writer (if applicable)
    if "video_file" in args:
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

    # open pyvicon
    client = PyVicon()
    client.connect(ip_address, port)
    client.setStreamMode(PyVicon.SM_ServerPush)

    for i in range(0,20):
        client.frame()
    subjects = client.subjects()

    # settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = 0.5
    dot_col = (255,255,255)

    trace_cols = {}
    for s in subjects:
        b = int(random.random() * 155) + 100
        g = int(random.random() * 155) + 100
        r = int(random.random() * 155) + 100
        trace_cols[s] = (b,g,r)

    print "tracking {} objects".format(len(subjects))
    print img_w, img_h

    # a frame to paste the trace on
    emptyframe = np.zeros((img_h,img_w,3), np.uint8)
    baseframe = emptyframe.copy()

    while True:
        # a frame to draw dots and text, without affecting the trace frame
        dotframe = baseframe.copy()
        
        client.frame()
        for s in trace_cols:
            x, y, _ = client.translation(s)
            pt = (int(x*scale), img_h-int(y*scale))
            
            # draw
            cv2.circle(baseframe, pt, 1, trace_cols[s], 2)
            cv2.circle(dotframe, pt, 3, dot_col, 5)
        
        # show and wait
        if not args.no_preview:
            cv2.imshow(window_name, dotframe)
            key = cv2.waitKey(sleep_time)
            if key == Key.esc:
                break
            elif key == Key.space:
                baseframe = emptyframe.copy()
        
        # save to video
        if export:
            video.write(dotframe)
        
        # console text
        sys.stdout.write("{}, {}\r".format(x, y))
        sys.stdout.flush()
        
    # write last still image
    if "image_file" in args:
        cv2.imwrite(args.image_file, dotframe)

    # clean up
    if export:
        video.release()
    cv2.destroyAllWindows()
    print "\ndone"
    return 0


if __name__ == '__main__':
    exit(main(sys.argv))
