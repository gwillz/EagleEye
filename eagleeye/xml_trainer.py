# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Kin Kuen Liu, Gwilyn Saunders
# version 0.2.4

import xml.etree.ElementTree as ET
from theta_sides import Theta

class Xmltrainer:
    def __init__(self, path=None, side=Theta.NonDual):
        self.side = side
        if path is not None:
            self.open(path)
        
    def open(self, path):
        self.path = path
        
        if path is None:
            raise IOError('Invalid file path to XML file.')
        
        tree = ET.parse(path)
        self.root = tree.getroot()
        
        # some more error checking
        if len(self.root) == 0:
            raise IOError('XML file is empty.')
        if self.root.tag != "TrainingSet":
            raise IOError("Wrong input file, needs a TrainingSet xml file.")
        
        # determine side
        if self.side == Theta.Backside:
            frames = self.root.find("backside")
        elif self.side == Theta.Buttonside:
            frames = self.root.find("buttonside")
        else:
            frames = self.root.find("frames")
        
        # even more error checking
        if frames is None:
            raise Exception("Wrong input file for {} mode".format(Theta.name(self.side)))
        
        # TODO ignore this one for now
        #if "num" not in frames.attrib:
        #    raise Exception("Outdated trainer file, missing num attrib.")
            
        # storage vars
        self.frames = {}
        self._img = []
        self._obj = []
        
        # loop through everything, sort into frames and seperate img/obj vars
        for frame in frames:
            frame_no = int(frame.attrib["num"])
            plane = frame.find("plane").attrib
            vicon = frame.find("vicon").attrib
            
            self.frames[frame_no] = {}
            self.frames[frame_no]["plane"] = plane
            self.frames[frame_no]["vicon"] = vicon
            self.frames[frame_no]["visibility"] = frame.find("visibility").attrib
            
            self._img.append((float(vicon['x']), float(vicon['y'])))
            self._obj.append((float(vicon['x']), float(vicon['y']), float(vicon['z'])))
        
        self.total = len(self.frames)
    
    def data(self):
        return self.frames
    
    def img_pts(self):
        return self._img
        
    def obj_pts(self, side=None):
        return self._obj
