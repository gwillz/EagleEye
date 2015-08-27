#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version: 0.1.3
#

import cv2, sys

class InnerCvar(type):
    major_ver = int(cv2.__version__.split('.')[0])
        
    def __getattr__(self, attr):
        if attr not in self.__dict__:
            # look in v3 style areas
            if attr in cv2.__dict__:
                setattr(self, attr, cv2.__dict__[attr])
            
            # look in v1 style areas
            elif "CV_"+attr in cv2.cv.__dict__:
                setattr(self, attr, cv2.cv.__dict__["CV_"+attr])
            
            # last effort (strip prepending name, replace with CV)
            else:
                attr = "CV_" + "_".join(attr.split("_")[1:])
                setattr(self, attr, cv2.cv.__dict__[attr])
        
        return self.__dict__[attr]

class CVFlag:
    __metaclass__ = InnerCvar
    

if __name__ == "__main__" and sys.argv[1] == 'test':
    print "testing version:", CVFlag.major_ver
    
    if CVFlag.major_ver >= 3:
        frame_count = cv2.CAP_PROP_FRAME_COUNT
        line_aa = cv2.LINE_AA
    else:
        frame_count = cv2.cv.CV_CAP_PROP_FRAME_COUNT
        line_aa = cv2.cv.CV_AA
    
    print "CAP_PROP_FRAME_COUNT:", CVFlag.CAP_PROP_FRAME_COUNT, "=", frame_count
    print "LINE_AA:", CVFlag.LINE_AA, "=", line_aa