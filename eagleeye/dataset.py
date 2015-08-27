#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.2
# 
# Wraps a CSV reader and stores additional data
# Automates routine functions
#

import os, csv

class Dataset:
    def __init__(self, path, id, deci_places=2, delimiter=","):
        # file ojects
        self.f = open(path, 'r')
        self.r = csv.reader(self.f, delimiter=delimiter)
        
        # properties
        self._delim = delimiter
        self._path = path
        self._id = "{{:0>{0}d}}".format(deci_places).format(id)
        self._name = os.path.basename(path).split("_")[-1].split(".")[0].replace("-", " ")
        
        # working vars
        self._row = None
        self._flash = False
        self._line = 0
    
    # getters
    def name(self):  return self._name
    def path(self):  return self._path
    def id(self):    return self._id
    def line(self):  return self._line
    def flash(self): return self._flash
    
    def verifyFlash(self):
        if self._flash and self._row[1] != 'F':
            self._flash = False
    
    def row(self):
        if self._row == None:
            self.next()
        return self._row
    
    def next(self):
        try:
            self._row = self.r.next()
            self._line += 1
            return True
        except StopIteration:
            return False
    
    def reel(self):
        while True:
            if not self.next():
                print "bad dataset:", self._name, ": EOF too soon at line:", self._line
                raise StopIteration
            
            if self._row[1] == 'F':
                self._flash = True
                break
        
    def close(self):
        self.f.close()