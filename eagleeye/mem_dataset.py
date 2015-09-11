#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.2.4
# 
# Loads the whole dataset into memory
#

import os, csv

class Memset:
    def __init__(self, path, id=None, delimiter=","):
        self.data = []
        self.total = 0
        self.start_set = 0
        self.end_set = 0
        self._at = 0.0
        
        self._delim = delimiter
        self._path = path
        self._name = os.path.basename(path).split("_")[-1].split(".")[0].replace("-", " ")
        self._ratio = 1.0
        
        # determine set parameters
        flash = 0
        with open(path, 'r') as f:
            reader = csv.reader(f, delimiter=delimiter)
            
            while True:
                try:
                    row = reader.next()
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
        # +1 because the set marks are indexes, not sizes
        self.data = self.data[self.start_set:self.end_set+1]
        self.total = self.end_set+1 - self.start_set
    
    def row(self, at=-1):
        if at == -1:
            return self.data[self.at()]
        else:
            return self.data[at]
        
    def next(self):
        i = self._at + self._ratio
        if i < self.total:
            self._at = i
            return True
        return False
    
    def back(self):
        i = self._at - self._ratio
        if i >= 0:
            self._at = i
            return True
        return False
    
    def setRatio(self, video_frames):
        self._ratio = self.total / float(video_frames)
        
    def at(self):
        return int(round(self._at, 0))
    
    def eof(self):
        return self._at >= (self.total - self._ratio)
    
    def status(self):
        return "row: {:0>2d}/{:d}"\
            .format(self.at(), self.total)
    
    def name(self):
        return self._name
