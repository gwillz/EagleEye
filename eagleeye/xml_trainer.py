# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Kin Kuen Liu, Gwilyn Saunders
# version 0.1.1

import xml.etree.ElementTree as ET

class Xmltrainer:
    def __init__(self, path=None):
        if path is not None:
            self.open(path)
        
    def open(self, path):
        self.path = path
        tree = ET.parse(path)
        self.root = tree.getroot()
        
        if len(self.root) == 0:
            raise IOError('XML file is empty.')
        
        if self.root.tag != "TrainingSet":
            raise IOError("Wrong input file, needs a TrainingSet xml file.")
        
        if "num" not in self.root.find('frames').attrib:
            raise Exception("Outdated trainer file, missing frame num attrib.")
        
        self.frames = {}
        self._at = 0
        self._ratio = 1.0
        
        # load frames
        for frame in self.root.findall('frames/frame'):
            frame_no = int(frame.attrib["num"])
            self.frames[frame_no] = {}
            self.frames[frame_no]["plane"] = frame.find("plane").attrib
            self.frames[frame_no]["vicon"] = frame.find("vicon").attrib
            self.frames[frame_no]["visibility"] = frame.find("visibility").attrib
        
        self.total = len(self.frames)
    
    def data(self):
        return self.frames
        
