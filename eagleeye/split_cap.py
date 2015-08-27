#
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version: 0.1.7
# 
# A class that wraps VideoCapture, but also allows for 
# cropping, rotation and left/right cuts to be made on-the-fly.
#

import cv2, numpy as np
from cv_flags import CVFlag

class SplitCapture:
    left = 0
    right = 1
    both = 2
    r0 = 0
    r90 = 1
    r180 = 2
    r270 = 3
    
    # open a path, set the default transformations
    def __init__(self, path, side=right, rotate=r270, crop=(0, 0, 120, 0)):
        self._cap = cv2.VideoCapture(path)
        self.total = int(self._cap.get(CVFlag.CAP_PROP_FRAME_COUNT))
        
        self.side = side
        self.rotate = rotate
        self.crop = crop
        
        # get input frame dimensions
        self._w = int(self._cap.get(CVFlag.CAP_PROP_FRAME_WIDTH))
        self._h = int(self._cap.get(CVFlag.CAP_PROP_FRAME_HEIGHT))
        
        ### way broken, no idea why
        # determine output frame dimensions (on defaults)
        #blank = np.zeros((self._w, self._h, 3), np.uint8)
        #blank = self._transform(blank, side, rotate, crop)
        #self.shape = blank.shape
        
        ### workaround (loses first frame)
        self.shape = self.read()[1].shape
        
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
    
    # wraps the read function
    #   side   = 0,1 or left, right
    #   rotate = 0-4 or r0, r90, r180, r270
    #   crop   = (North, East, South, West) as integers
    # specify None if the defaults (in the constructor) are to be used
    def read(self, side=None, rotate=None, crop=None):
        ret, frame = self._cap.read()
        
        # catch nonetype before transformations
        if frame is None:
            return ret, None
        
        # transform and return
        return ret, self._transform(frame, 
                                side if side is not None else self.side, 
                                rotate if rotate is not None else self.rotate, 
                                crop if crop is not None else self.crop)
        
    def isOpened(self):
        return self._cap.isOpened()
        
    def release(self):
        self._cap.release()
        
    def get(self, flag):
        return self._cap.get(flag)


# testing script
if __name__ == "__main__":
    import sys
    
    # sanity checks
    if len(sys.argv) < 3:
        print "testing script aborted. Requries args"
        print "usage: python2 split_cap.py <video path> <left|right>"
        exit(1)
    
    # open reader, window, etc
    cap = SplitCapture(sys.argv[1])
    side = cap.left if sys.argv[2] == 'left' else cap.right
    
    window_name = "SplitCap test"
    cv2.namedWindow(window_name)
    
    # loop
    while cap.isOpened():
        _, frame = cap.read(side)
        cv2.imshow(window_name, frame)
        
        # break on key 'Q'
        if cv2.waitKey(5) == 0xFF & ord('q'):
            break
    
    # clean up
    cap.release()
    cv2.destroyWindow(window_name)
    exit(0)
