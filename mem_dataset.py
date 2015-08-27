#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.1
# 
# Loads the whole dataset into memory
#

from dataset import *

class Memset:
    def __init__(self, path, id=None, delimiter=","):
        self.data = []
        self.total = 0
        self.start_set = 0
        self.end_set = 0
        self._at = 0.0
        
        self._ratio = 1.0
        
        # determine set parameters
        flash = 0
        with open(path, 'r') as f:
            while True:
                try:
                    row = f.next().split(delimiter)
                except StopIteration:
                    break
                
                if row[1] == 'F' and flash == 0:
                    flash = 1
                    self.start_set = self.total
                if row[1] != 'F' and flash == 1:
                    flash = 2
                if row[1] == 'F' and flash == 2:
                    flash = 3
                    self.end_set = self.total
                    
                self.data.append(row)
                self.total += 1
        
    def restrict(self):
        self.data = self.data[self.start_set:self.end_set]
        self.total = self.end_set - self.start_set
    
    def row(self, at=-1):
        if at == -1:
            return self.data[self.at()]
        else:
            return self.data[at]
        
    def next(self):
        i = self._at + self._ratio
        if i < self.total:
            self._at = i
    
    def back(self):
        i = self._at - self._ratio
        if i >= 0:
            self._at = i
    
    def setRatio(self, video_frames):
        self._ratio = self.total / float(video_frames)
        
    def at(self):
        return int(round(self._at, 0))
        
    def status(self):
        return "row: {:0>2d}/{:d}"\
            .format(self.at(), self.total)
