# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.2.1

import xml.etree.ElementTree as ET

class Xmltrainer:
    def __init__(self, path=None):
        if path is not None:
            self.open(path)
        ''' 
        print "FINISHED READ TRAINER XML:"
        print self.frames
        for i in self.frames:
            print i
        '''
        
    def open(self, path):
        self.path = path
        tree = ET.parse(path)
        self.root = tree.getroot()
        
        self.frames = {}
        self._at = 0
        self._ratio = 1.0
        
        for frames in self.root:
            for frame in frames.findall('frame'):
                frame_no = frame.get("num")
                self.frames[frame_no] = {}
                self.frames[frame_no]["plane"] = frame.find("plane").attrib
                self.frames[frame_no]["vicon"] = frame.find("vicon").attrib
                self.frames[frame_no]["visibility"] = frame.find("visibility").attrib
            
            #self.frames.update(objects)
        
        self.total = len(self.frames)
    
    def data(self, key=-1):
        if key == -1:
            return self.frames          # return all data (?)
        else:
            return self.frames.get(key) # may have to use str(key)
    '''
    def next(self):
        i = self._at + self._ratio
        if i < self.total and i < self.total-1:
            self._at = i
            
    def back(self):
        i = self._at - self._ratio
        if i >= 0:
            self._at = i
    
    def at(self):
        return int(round(self._at, 0))
    
    def setRatio(self, video_frames):
        self._ratio = self.total / float(video_frames)
    '''
    
