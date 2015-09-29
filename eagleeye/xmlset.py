# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.2.2
# 
# Reads an XML Dataset file into memory
# Provides synchronisation techniques - via setRatio()
# 

import xml.etree.ElementTree as ET

class Xmlset:
    def __init__(self, path=None):
        if path is not None:
            self.open(path)
    
    def open(self, path):
        self.path = path
        tree = ET.parse(path)
        self.root = tree.getroot()
        
        self.frames = []
        self._at = 0
        self._ratio = 1.0
        
        for frm in self.root:
            #num = el.find('frame').atrrib['number']
            objects = {}
            for obj in frm.findall('object'):
                name = obj.attrib['name']
                objects[name] = {}
                objects[name]["box"] = obj.find('boxinfo').attrib
                objects[name]["centre"] = obj.find('centroid').attrib
            
            self.frames.append(objects)
        
        self.total = len(self.frames)
    
    # Gets current frame, or a specific frame if 'at' option is > 0
    def data(self, at=-1):
        if at == -1:
            return self.frames[self.at()]
        else:
            return self.frames[at]
    
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
    
    def at(self):
        return int(round(self._at, 0))
    
    # calculate appropriate ratio from the matching video frames
    def setRatio(self, video_frames):
        self._ratio = self.total / float(video_frames)
    
    def resetRatio(self):
        self._ratio = 1.0
    
