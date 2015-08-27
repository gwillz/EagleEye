#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1
# 
# Adds rewind buffering to the dataset class
#

from dataset import *

class Buffset(Dataset):
    def __init__(self, path, id, deci_places=2, delimiter=",", buff_max=30):
        self.buff_max = buff_max
        self.buff = []
        self.buff_at = 0
        self.rows = buff_max
        self.total = sum(1 for row in open(path, 'r'))
        
        Dataset.__init__(self, path, id, deci_places=deci_places, delimiter=delimiter)
        
        for i in xrange(0, buff_max):
            Dataset.next(self)
            self.buff.append(self._row)
        
    def row(self):
        return self.buff[self.buff_at]
        
    def next(self):
        if self.buff_at >= self.buff_max-1:
            ret = Dataset.next(self)
            self.rows += 1
            self.buff.append(self._row)
            self.buff.pop(0)
            return ret
        else:
            self.buff_at += 1
            return True
    
    def back(self):
        if self.buff_at > 0: self.buff_at -= 1
        return True
    
    def at(self):
        return self.rows + self.buff_at - self.buff_max
        
    def status(self):
        return "row: {:0>2d}/{:d} buffer: {:0>2d}/{:0>2d}"\
            .format(self.at(), self.total, self.buff_at+1, self.buff_max)
