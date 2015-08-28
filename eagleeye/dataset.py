#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.2.3
# 
# Wraps a CSV reader and stores additional data
# Automates routine functions
#

import os, csv

class Dataset:
    def __init__(self, path, delimiter=","):
        # file ojects
        self.f = open(path, 'r')
        self.r = csv.reader(self.f, delimiter=delimiter)
        
        # properties
        self._delim = delimiter
        self._path = path
        self._name = os.path.basename(path).split("_")[-1].split(".")[0].replace("-", " ")
        
        # working vars
        self._row = None
        self._flash = False
        self._at = 0
    
    # getters
    def name(self):  return self._name
    def path(self):  return self._path
    def at(self):    return self._at
    def flash(self): return self._flash
    
    def row(self):
        # load first row
        if self._row == None:
            self.next()
        return self._row
    
    def next(self):
        try: # load row
            self._row = self.r.next()
            self._at += 1
            
            # show warning for old-style datasets
            if self._flash and self._row[1] == 'F':
                print "WARNING: use of old type datasets are not supported"
            
            # test for flash
            self._flash = (self._row[1] == 'F')
            
            return True
        except StopIteration:
            return False
    
    def reel(self):
        while True:
            if not self.next():
                print "bad dataset:", self._name, ": EOF too soon at line:", self._at
                raise StopIterations
            
            if self._flash:
                break
        self._flash = False
        
    def close(self):
        self.f.close()