#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders & Kin Kuen Liu
# version 0.2.8
# 

import cv2, xml.etree.ElementTree as ET, numpy as np

class Mapper:
    def __init__(self, intrinsic, trainer):
        # open intrinsic, trainer files
        self.cam, self.distort = self.parseCamIntr(intrinsic)
        self.img_pts, self.obj_pts = self.parseTrainer(trainer)
        
        #calculate pose
        self.rv, self.tv = self.calPose()
    
    # opens the Intrinsic calib xml file
    def parseCamIntr(self, xmlpath):
        if xmlpath is None:
            raise IOError('Invalid file path to XML file.')
        
        cm_dict = {'fx': None, 'fy': None, 'cx': None, 'cy': None}
        dc_dict = {'k1': 0.0, 'k2': 0.0,
                   'k3': 0.0, 'k4': 0.0,
                   'k5': 0.0, 'k6': 0.0,
                   'p1': 0.0, 'p2': 0.0,
                   'c1': 0.0, 'c2': 0.0,
                   'c3': 0.0, 'c4': 0.0
                   }
        
        cm, dc = [], []
        
        tree = ET.parse(xmlpath)
        root = tree.getroot()
        
        if len(root) == 0:
            raise IOError('XML file is empty.')
        
        for elem in root.iter():
            if elem.tag == 'CamMat':
                cm_dict.update(elem.attrib) # TODO: check if update only replaces existing elements
            if elem.tag =='DistCoe':
                dc_dict.update(elem.attrib)
            
        ### TODO: CHECK None Values !!!!
        
        if cm_dict['fx'] and cm_dict['fy'] and cm_dict['cx'] and cm_dict['cy'] is not None:
            # build a 3x3 camera matrix
            cm = np.matrix([[float(cm_dict['fx']), 0, float(cm_dict['cx'])],
                            [0, float(cm_dict['fy']), float(cm_dict['cy'])],
                            [0, 0, 1]
                            ])
            
        if cv2.__version__ >= '3.0.0':
            dc = np.asarray([float(dc_dict['k1']), float(dc_dict['k2']),
                                float(dc_dict['p1']), float(dc_dict['p2']),
                                float(dc_dict['k3']), float(dc_dict['k4']),
                                float(dc_dict['k5']), float(dc_dict['k6']),
                                float(dc_dict['c1']), float(dc_dict['c2']),
                                float(dc_dict['c3']), float(dc_dict['c4'])
                            ])
        else:
            dc = np.asarray([float(dc_dict['k1']), float(dc_dict['k2']),
                                float(dc_dict['p1']), float(dc_dict['p2']),
                                float(dc_dict['k3']), float(dc_dict['k4']),
                                float(dc_dict['k5']), float(dc_dict['k6'])
                            ])
        return cm, dc
    
    
    def parseTrainer(self, xmlpath):
        if xmlpath is None:
            raise IOError('Invalid file path to XML file.')
        
        tree = ET.parse(xmlpath)
        root = tree.getroot()
        
        if len(root) == 0:
                raise IOError('XML file is empty.')
        
        img_pos = []
        obj_pos = []
        
        for f in root.find('frames'):
            plane = f.find('plane').attrib
            vicon = f.find('vicon').attrib
            
            img_pos.append((float(plane['x']), float(plane['y'])))
            obj_pos.append((float(vicon['x']), float(vicon['y']), float(vicon['z'])))
        
        return np.asarray(img_pos, dtype=np.float32), np.asarray(obj_pos, dtype=np.float32)
    
    
    def calPose(self, mode=0):
        # levenberg-marquardt iterative method
        if mode == 0:
            retval, rv, tv = cv2.solvePnP(
                                self.obj_pts, self.img_pts, 
                                self.cam, self.distort, # where do these come from??
                                None, None, cv2.SOLVEPNP_ITERATIVE)
            
        # alternate, loopy style iterative method (could be the same, idk)
        else:
            rv, tv = None, None
            for i in range(0, len(data)):
                retval, _rv, _tv = cv2.solvePnP(
                                    self.obj_pts[i], self.img_pts[i],
                                    self.cam, self.distort, # where do these come from??
                                    rv, tv, useExtrinsicGuess=True)
                #append if 'good'
                if retval: 
                    rv, tv = _rv, _tv
        
        # check, print, return
        if rv is None or rv is None or not retval:
            raise Error("Error producing rotation and translation vectors.")
        
        print 'Rotation Vector:\n', rv
        print 'Translation Vector:\n', tv
        
        return rv, tv
    
    
    def calpts(self, obj_pts):
        #if len(obj_pts) == 0:
        #    raise Error('No points to project.')
        
        proj_imgpts, jac = cv2.projectPoints(np.asarray([obj_pts], dtype=np.float32), self.rv, self.tv, self.cam, self.distort)
        proj_imgpts = proj_imgpts.reshape((len(proj_imgpts), -1))
        
        #print 'Project Point Coordinates:'
        #for n in range(0, len(proj_imgpts)):
        #    print 'Point', n+1, ':', proj_imgpts[n]
        
        return proj_imgpts[0]

