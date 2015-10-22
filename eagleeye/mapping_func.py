#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 3 - UniSA 2015
# Gwilyn Saunders & Kin Kuen Liu
# version 0.3.15
# 

import cv2, xml.etree.ElementTree as ET, numpy as np
from theta_sides import Theta
from xml_trainer import Xmltrainer

magnitude = lambda x: np.sqrt(np.vdot(x, x))
unit = lambda x: x / magnitude(x)

class Mapper:
    
    def __init__(self, intrinsic, trainer, cfg, mode=Theta.NonDual):
        # variables
        self.rv = np.asarray([], dtype=np.float32)  # rotation
        self.tv = np.asarray([], dtype=np.float32)  # translation
        self.mode = mode
        
        # load some configs, required by solvePnP eventually
        self.cfg = cfg
        self.halfcos_fov = np.cos(np.radians(cfg.camera_fov) / 2)
        self.half_fov = np.radians(cfg.camera_fov) / 2
        
        # open intrinsic, trainer files
        self.cam, self.distort = self.parseCamIntr(intrinsic)
        self.img_pts, self.obj_pts = self.parseTrainer(trainer)
        
        print "\nside:", Theta.name(mode)
        print "img_pts {}".format(len(self.img_pts))
        print "obj_pts {}".format(len(self.obj_pts))
        
        #calculate pose
        self.rv, self.tv = self.calPose()
        self.rv_unit = unit(self.rv)
    
    # opens the Intrinsic calib xml file
    def parseCamIntr(self, xmlpath):
        
        cm, dc = [], []
        cm_dict = {'fx': None, 'fy': None, 'cx': None, 'cy': None}
        dc_dict = {'k1': 0.0, 'k2': 0.0,
                   'k3': 0.0, 'k4': 0.0,
                   'k5': 0.0, 'k6': 0.0,
                   'p1': 0.0, 'p2': 0.0,
                   'c1': 0.0, 'c2': 0.0,
                   'c3': 0.0, 'c4': 0.0
                   }
        
        if xmlpath is None:
            raise IOError('Invalid file path to XML file.')
        
        tree = ET.parse(xmlpath)
        root = tree.getroot()
        
        if len(root) == 0:
            raise IOError('XML file is empty.')
        
        if root.tag != "StdIntrinsic" and self.mode == Theta.NonDual:
            raise IOError("Wrong input file, needs a StdIntrinsic xml file.")
        elif root.tag != "dual_intrinsic" and self.mode != Theta.NonDual:
            raise IOError("Wrong input file, needs a dual_intrinsic xml file.")
        
        if self.mode == Theta.Buttonside:
            root = root.find("Buttonside")
        elif self.mode == Theta.Backside:
            root = root.find("Backside")
        
        for elem in root:
            if elem.tag == 'CamMat':
                cm_dict.update(elem.attrib)
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
        trainer = Xmltrainer(xmlpath, self.mode)
        self.num_training = trainer.total
        
        img_pts = np.asarray(trainer.img_pts(), np.float32)
        obj_pts = np.asarray(trainer.obj_pts(), np.float32)
        
        return img_pts, obj_pts
    
    
    def calPose(self):
        if len(self.img_pts) < 4 or len(self.obj_pts) < 4:
            raise Exception("Must have at least 4 training points.")
            
        if len(self.img_pts) != len(self.obj_pts):
            raise Exception("Training image points and object points must be equal in size. "
                            "image pts {}, obj pts {}".format(len(self.img_pts), len(self.obj_pts)))
        
        # TODO: customised solvePnP flags from config
        # levenberg-marquardt iterative method
        retval, rv, tv = cv2.solvePnP(
                            self.obj_pts, self.img_pts, 
                            self.cam, self.distort,
                            None, None, cv2.SOLVEPNP_ITERATIVE)
        '''
        NOT RUNNING
        http://stackoverflow.com/questions/30271556/opencv-error-through-calibration-tutorial-solvepnpransac
        rv, tv, inliners = cv2.solvePnPRansac(
                            self.obj_pts, self.img_pts, 
                            self.cam, self.distort)
        '''
        
        # check, print, return
        if rv is None or rv is None or not retval:
            raise Exception("Error occurred when calculating rotation and translation vectors.")
        
        print 'Rotation Vector:\n', rv
        print 'Translation Vector:\n', tv
        
        return rv, tv
    
    def isVisible(self, pt):
        obj = np.array(pt).reshape(3, 1)
        
        # determine line and direction to object
        cam_to_obj = obj - self.tv
        obj_dir = unit(cam_to_obj)
        
        # test within FOV
        cosTheta = np.vdot(self.rv_unit, obj_dir)
        
        #print np.rad2deg(np.arccos(cosTheta)), "<", np.rad2deg(np.arccos(self.halfcos_fov))
        
        # are 'cos' comparisons backwards?
        #return np.arccos(cosTheta) < self.half_fov
        return cosTheta > self.halfcos_fov
    
    def reprojpts(self, obj_pts):
        if len(obj_pts) == 0:
            raise Exception('No points to project.')
        
        proj_imgpts, jac = cv2.projectPoints(np.asarray([obj_pts], dtype=np.float32), self.rv, self.tv, self.cam, self.distort)
        proj_imgpts = proj_imgpts.reshape((len(proj_imgpts), -1))
        
        return proj_imgpts[0]

