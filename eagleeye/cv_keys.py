#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# 0.2.1
# 

import locale as lc

class Key:
    # this should only run on import, right?
    if lc.getdefaultlocale()[1] == "UTF-8":
        enter     = 10
        backspace = 65288
        left      = 65361
        up        = 65362
        right     = 65363
        down      = 65364
    else:
        enter     = 13
        backspace = 8
        left      = 2424832
        up        = 2490368
        right     = 2555904
        down      = 2621440
    
    space = 32
    esc   = 27
    
    @staticmethod
    def char(key, char):
        return key & 0xFF == ord(char)


# experiment thingy - to find new keys
if __name__ == "__main__":
    import cv2
    
    cv2.namedWindow("test me")
    while True:
        key = cv2.waitKey(0)
        
        if key == Key.esc:
            break
        else:
            print key
    
    cv2.destroyAllWindows()
    print "\nDone!"
    exit(0)
