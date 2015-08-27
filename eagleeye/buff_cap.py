#
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version: 0.2.7
# 

import cv2
from cv_flags import CVFlag

class BuffCap:
    def __init__(self, path, buff_max=30):
        self._cap = cv2.VideoCapture(path)
        self.buff_max = buff_max
        self.buff = []
        self.buff_at = 0
        self._frame_at = buff_max
        
        # load up the first buffer
        for i in xrange(0, buff_max):
            self.buff.append(self._cap.read()[1])
        
        if self.buff[0] is None:
            raise IOError("Empty/missing video file")
        
        self._frame = self.buff[0]
        self.shape = self._frame.shape
        self.total = int(self._cap.get(CVFlag.CAP_PROP_FRAME_COUNT))
        
    def frame(self):
        return self._frame.copy()
    
    def next(self):
        # load new frames if at head of the stack
        if self.buff_at >= self.buff_max -1 and self._cap.isOpened():
            ret, img = self._cap.read()
            
            if img is not None:
                self._frame_at += 1
                self.buff.append(img)
                self.buff.pop(0)
                self._frame = img
                return True
            else:
                return False
        
        # otherwise read from within the buffer
        else: 
            self.buff_at += 1
            self._frame = self.buff[self.buff_at]
            return True
        
    def back(self):
        # read backwards through the stack
        ret = self.buff_at > 0
        if self.buff_at > 0: self.buff_at -= 1
        self._frame = self.buff[self.buff_at]
        return ret
        
    def isOpened(self):
        return self._cap.isOpened()
        
    def release(self):
        self._cap.release()
        
    def at(self):
        return self._frame_at + self.buff_at - self.buff_max
    
    def status(self):
        return "frame: {:0>2d}/{:d} buffer: {:0>2d}/{:0>2d}"\
            .format(self.at(), self.total, self.buff_at+1, self.buff_max)
