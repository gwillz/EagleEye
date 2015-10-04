# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.2.4
# 
# Reads an XML Dataset file into memory
# Provides synchronisation techniques - via setRatio()
# 

import xml.etree.ElementTree as ET
from math import ceil, floor

class Xmlset:
    def __init__(self, path=None, offset=0):
        self.offset = offset
        if path is not None:
            self.open(path)
    
    def open(self, path):
        self.path = path
        tree = ET.parse(path)
        self.root = tree.getroot()
        
        self._frames = {}
        self._at = 0.0
        self._ratio = 1.0
        
        for frm in self.root.findall('frameInformation'):
            num = int(frm.find('frame').attrib['number'])
            
            objects = {}
            for obj in frm.findall('object'):
                name = obj.attrib['name']
                objects[name] = {}
                objects[name]["box"] = obj.find('boxinfo').attrib
                objects[name]["centre"] = obj.find('centroid').attrib
                objects[name]["visibility"] = obj.find("visibility").attrib
            
            self._frames[num] = objects
        
        self.total = len(self._frames)
    
    # Gets current frame, or a specific frame if 'at' option is > 0
    def data(self, at=-1, mode=0):
        if at == -1:
            return self._frames[self.at(mode)] # TODO: are we just assuming all frames are filled in?
        else:
            return self._frames[at]
    
    def next(self):
        i = self._at + self._ratio
        if i < self.total and i < self.total-1: # what?
            self._at = i
            return True
        return False
            
    def back(self):
        i = self._at - self._ratio
        if i >= 0:
            self._at = i
            return True
        return False
    
    def at(self, mode=0):
        if mode == 0:
            return int(round(self._at, 0)) + self.offset
        if mode == 1:
            return int(ceil(self._at)) + self.offset
        else:
            return int(floor(self._at)) + self.offset
    
    # calculate appropriate ratio from the matching video frames
    def setRatio(self, video_frames):
        self._ratio = self.total / float(video_frames)
    
    def resetRatio(self):
        self._ratio = 1.0
    
