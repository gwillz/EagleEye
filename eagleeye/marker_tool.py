#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.1.3
#

from buff_split_cap import BuffSplitCap
from cv_keys import Key
import cv2

def marker_tool(video_path, buffer_size=50, window_name="Marking Tool"):
    # load video, create window
    cap = BuffSplitCap(video_path, buff_max=buffer_size)
    cv2.namedWindow(window_name)
    
    # working vars
    mark_in = 0
    mark_out = cap.total
    
    # marking loop
    while cap.isOpened():
        frame = cap.frame()
        cv2.putText(frame, \
                    cap.status() + " in: {0} out: {1}".format(mark_in, mark_out), 
                    (5,15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)
        
        # display and wait
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(0)
        
        # controls
        if key == Key.esc:
            cap.release()
            cv2.destroyAllWindows()
            return False, None, None
        
        elif key == Key.enter:
            break
        elif key == Key.right:
            cap.next()
        elif key == Key.left:
            cap.back()
        elif Key.char(key, '['):
            if cap.at() > mark_out:
                print "You cannot mark in after mark out."
                continue
            else:
                mark_in = cap.at()
        elif Key.char(key, ']'):
            if cap.at() < mark_in:
                print "You cannot mark out before mark in."
                continue
            else:
                mark_out = cap.at()

    # clean up
    cap.release()
    cv2.destroyWindow(window_name)
    
    return True, mark_in, mark_out


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print "please specify a video file"
        exit(1)
    
    print marker_tool(sys.argv[1])
    
    exit(0)
