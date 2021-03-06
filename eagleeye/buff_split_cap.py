#
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version: 0.2.3
# 
# Implements features from both BuffCapture and SplitCapture
# Can buffer and split, rotate, crop frames on-the-fly
# Also include dataset limiting via restrict()
#

import cv2, numpy as np
from theta_sides import Theta

class BuffSplitCap:
    r0 = 0
    r90 = 1
    r180 = 2
    r270 = 3
    
    # open a path, set the default transformations
    def __init__(self, path, side=Theta.Both, rotate=r0, crop=(0, 0, 0, 0), buff_max=30):
        self._cap = cv2.VideoCapture(path)
        
        # buffer variables
        self._buff_max = buff_max
        self._buff = []
        self._buff_at = 0
        self._frame_at = buff_max
        
        # splitter variables
        self.side = side
        self.rotate = rotate
        self.crop = crop
        
        # get _input_ frame dimensions
        self._w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # load up the buffer
        for i in xrange(0, buff_max):
            self._buff.append(self._cap.read()[1])
        
        if len(self._buff) == 0 or self._buff[0] is None:
            raise IOError("Empty/missing video file")
        
        self._frame = self._buff[0]
        self.shape = self._frame.shape
        self.total = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # default mark values
        self.mark_in = 0
        self.mark_out = self.total
        self.marked = False
        
    
    # internal routine - runs transformations on a single frame
    def _transform(self, frame, side, rotate, crop):
        # crop and split
        if side == Theta.Left:
            frame = frame[0-crop[0]:self._h-crop[2], 0-crop[3]:self._w/2-crop[1]]
        elif side == Theta.Right:
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
        if self._buff_at >= self._buff_max -1 and self._cap.isOpened():
            ret, img = self._cap.read()
            
            if img is not None \
                    and self.at() < self.mark_out:
                self._frame_at += 1
                self._buff.append(img)
                self._buff.pop(0)
                self._frame = img
                return True
            else:
                return False
        
        # otherwise read from within the buffer
        else: 
            self._buff_at += 1
            self._frame = self._buff[self._buff_at]
            return True
    
    def back(self):
        # read backwards through the stack
        if self._buff_at > 0 \
                and self.at() > self.mark_in:
                
            self._buff_at -= 1
            self._frame = self._buff[self._buff_at]
            return True
        else:
            return False
    
    # restrict back/next navigation within these marks
    def restrict(self, mark_in, mark_out):
        # only allow restrict once
        if self.marked:
            print "cannot restrict() twice"
            return
        
        if self.at() > 0:
            print "restrict() must be called before next()"
            return
        
        # reel up to the first frame
        while True:
            if mark_in >= self.at():
                self.next()
            else:
                break
        
        # set marks, exclusive style (without flashes)
        self.mark_in = mark_in + 1
        self.mark_out = mark_out - 1
        self.marked = True
    
    def isOpened(self):
        return self._cap.isOpened()
        
    def release(self):
        self._cap.release()
        
    def get(self, flag):
        return self._cap.get(flag)
    
    def at(self):
        return self._frame_at + self._buff_at - self._buff_max
    
    def status(self):
        return "frame: {:0>2d}/{:d} buffer: {:0>2d}/{:0>2d}"\
            .format(self.at(), self.total, self._buff_at+1, self._buff_max)

# testing script
if __name__ == "__main__":
    import sys
    
    # sanity checks
    if len(sys.argv) < 3:
        print "testing script aborted. Requries args"
        print "usage: python2 buff_split_cap.py <video path> <left|right>"
        exit(1)
    
    # open reader, window, etc
    side = Theta.resolve(sys.argv[2])
    cap = BuffSplitCap(sys.argv[1], side=side, rotate=BuffSplitCap.r270)
    
    window_name = "SplitCap test"
    cv2.namedWindow(window_name)
    
    # loop
    while cap.isOpened():
        cv2.imshow(window_name, cap.frame(side))
        sys.stdout.write(cap.status() + "\r")
        sys.stdout.flush()
        
        # controls
        key = cv2.waitKey(0)
        if key == 0xFF & ord('q'):
            break
        elif key == 0xFF & ord(' '):
            cap.restrict(27, 1267)
        elif key == 0xFF & ord('.'):
            cap.next()
        elif key == 0xFF & ord(','):
            cap.back()
    
    # clean up
    cap.release()
    cv2.destroyWindow(window_name)
    exit(0)
