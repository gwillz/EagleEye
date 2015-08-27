#
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version: 0.1
# 
# Implements features from both BuffCapture and SplitCapture.
# Can buffer and split, rotate, crop frames on-the-fly.
#

import cv2, numpy as np
from cv_flags import CVFlag

class BuffSplitCap:
    left = 0
    right = 1
    both = 2
    r0 = 0
    r90 = 1
    r180 = 2
    r270 = 3
    
    # open a path, set the default transformations
    def __init__(self, path, side=right, rotate=r270, crop=(0, 0, 120, 0), buff_max=30):
        self._cap = cv2.VideoCapture(path)
        
        # buffer variables
        self.buff_max = buff_max
        self.buff = []
        self.buff_at = 0
        self._frame_at = buff_max
        
        # splitter variables
        self.side = side
        self.rotate = rotate
        self.crop = crop
        
        # get _input_ frame dimensions
        self._w = int(self._cap.get(CVFlag.CAP_PROP_FRAME_WIDTH))
        self._h = int(self._cap.get(CVFlag.CAP_PROP_FRAME_HEIGHT))
        
        # load up the buffer
        for i in xrange(0, buff_max):
            self.buff.append(self._cap.read()[1])
        
        if len(self.buff) == 0 or self.buff[0] is None:
            raise IOError("Empty/missing video file")
        
        self._frame = self.buff[0]
        self.shape = self._frame.shape
        self.total = int(self._cap.get(CVFlag.CAP_PROP_FRAME_COUNT))
        
    # internal routine - runs transformations on a single frame
    def _transform(self, frame, side, rotate, crop):
        # crop and split
        if side == self.left:
            frame = frame[0-crop[0]:self._h-crop[2], 0-crop[3]:self._w/2-crop[1]]
        elif side == self.right:
            frame = frame[0-crop[0]:self._h-crop[2], self._w/2-crop[3]:self._w-crop[1]]
        else: # both
            frame = frame[0-crop[0]:self._h-crop[2], 0-crop[3]:self._w-crop[1]]
        
        # rotate and return
        return np.rot90(frame, rotate)
    
    #   side   = 0,1 or left, right
    #   rotate = 0-4 or r0, r90, r180, r270
    #   crop   = (North, East, South, West) as integers
    # specify None if the defaults (in the constructor) are to be used
    def frame(self, side=None, rotate=None, crop=None):
        return self._transform(self._frame.copy(), 
                                side if side is not None else self.side, 
                                rotate if rotate is not None else self.rotate, 
                                crop if crop is not None else self.crop)
    
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
        
    def get(self, flag):
        return self._cap.get(flag)
    
    def at(self):
        return self._frame_at + self.buff_at - self.buff_max
    
    def status(self):
        return "frame: {:0>2d}/{:d} buffer: {:0>2d}/{:0>2d}"\
            .format(self.at(), self.total, self.buff_at+1, self.buff_max)

# testing script
if __name__ == "__main__":
    import sys
    
    # sanity checks
    if len(sys.argv) < 3:
        print "testing script aborted. Requries args"
        print "usage: python2 buff_split_cap.py <video path> <left|right>"
        exit(1)
    
    # open reader, window, etc
    cap = BuffSplitCap(sys.argv[1])
    side = cap.left if sys.argv[2] == 'left' else cap.right
    
    window_name = "SplitCap test"
    cv2.namedWindow(window_name)
    
    # loop
    while cap.isOpened():
        cv2.imshow(window_name, cap.frame(side))
        
        # controls
        key = cv2.waitKey(0)
        if key == 0xFF & ord('q'):
            break
        elif key == 0xFF & ord('.'):
            cap.next()
        elif key == 0xFF & ord(','):
            cap.back()
    
    # clean up
    cap.release()
    cv2.destroyWindow(window_name)
    exit(0)
