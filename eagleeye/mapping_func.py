#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 3 - UniSA 2015
# Gwilyn Saunders & Kin Kuen Liu
# version 0.2.8
# 

import cv2, xml.etree.ElementTree as ET, numpy as np

class Mapper:
    def __init__(self, intrinsic, trainer, cfg):
        # variables
        self.rv = np.asarray([], dtype=np.float32)  # rotation
        self.tv = np.asarray([], dtype=np.float32)  # translation

        # open intrinsic, trainer files
        self.cam, self.distort = self.parseCamIntr(intrinsic)
        # first 2 are full sets of data
        # trainer pts are filtered by quality control for generating consistent PnP result
        self.img_pts, self.obj_pts, self.trainer_imgpts, self.trainer_objpts = self.parseTrainer(trainer, cfg)

        print "img_pts {}".format(len(self.img_pts))
        print "obj_pts {}".format(len(self.obj_pts))
        print "trainer img_pts {}".format(len(self.trainer_imgpts))
        print "trainer obj_pts {}".format(len(self.trainer_objpts))
        #calculate pose
        self.rv, self.tv = self.calPose(cfg, mode=0)
    
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
    
    
    def parseTrainer(self, xmlpath, cfg):
        if xmlpath is None:
            raise IOError('Invalid file path to XML file.')
        
        tree = ET.parse(xmlpath)
        root = tree.getroot()
        
        if len(root) == 0:
                raise IOError('XML file is empty.')
        img_pos = []
        obj_pos = []
        trainer_imgpos = []
        trainer_objpos = []
        min_reflectors = cfg.min_reflectors
        # ensure minimum is 4 as required by VICON system
        if (min_reflectors < 4):
            min_reflectors = 4
        
        qualityText = "min of {} visible \n".format(min_reflectors)
        print qualityText

        for f in root.find('frames'):
            # TODO: inconsistent get attrib names ??
            plane = f.find('plane').attrib
            vicon = f.find('vicon').attrib
            visibility = f.find('visibility').attrib
            
            x = float(plane['x'])
            y = float(plane['y'])
            vicon_x = float(vicon['x'])
            vicon_y = float(vicon['y'])
            vicon_z = float(vicon['z'])
            visible = int(visibility['visible'])
            max_visible = int(visibility['visibleMax'])

            # add to the complete set first
            img_pos.append((x, y))
            obj_pos.append((vicon_x, vicon_y, vicon_z))

            # Minimum points of reflectors, must be at least 4
            if (visible < min_reflectors):
                continue    # skip frame
            
            # Quality control for solvePnP, skip data/frame if criteria not met
            # check negative position values, if on skip mapping at this frame
            if(cfg.check_negatives == True):
                if(vicon_x < 0 or vicon_y < 0 or vicon_z < 0):
                    continue
                
            # Add to trainer set if good
            trainer_imgpos.append((x, y))
            trainer_objpos.append((vicon_x, vicon_y, vicon_z))
        
        return np.asarray(img_pos, dtype=np.float32), np.asarray(obj_pos, dtype=np.float32), np.asarray(trainer_imgpos, dtype=np.float32), np.asarray(trainer_objpos, dtype=np.float32)
    
    
    def calPose(self, cfg, mode=0):
        if(len(self.trainer_imgpts) < 4 or len(self.trainer_objpts) < 4):
            print "Must have at least 4 training points."
            return np.asarray([], dtype=np.float32), np.asarray([], dtype=np.float32)           # TODO: need to abort here, not a good abort atm
        if(len(self.trainer_imgpts) != len(self.trainer_objpts)):
            print "Training image points and object points must be equal in size. image pts {}, obj pts {}".format(len(self.trainer_imgpts), len(self.trainer_objpts))
            return np.asarray([], dtype=np.float32), np.asarray([], dtype=np.float32)           # TODO: need to abort here, not a good abort atm
        
        # TODO: customised solvePnP flags form config
        # levenberg-marquardt iterative method
        if mode == 0:
            retval, rv, tv = cv2.solvePnP(
                                self.trainer_objpts, self.trainer_imgpts, 
                                self.cam, self.distort,
                                None, None, cv2.SOLVEPNP_ITERATIVE)
            '''
            NOT RUNNING
            http://stackoverflow.com/questions/30271556/opencv-error-through-calibration-tutorial-solvepnpransac
            rv, tv, inliners = cv2.solvePnPRansac(
                                self.trainer_objpts, self.trainer_imgpts, 
                                self.cam, self.distort)
            '''
        # alternate, loopy style iterative method (could be the same, idk)
        else:
            rv, tv = None, None
            for i in range(0, len(data)):
                retval, _rv, _tv = cv2.solvePnP(
                                    self.trainer_objpts[i], self.trainer_imgpts[i],
                                    self.cam, self.distort,
                                    rv, tv, useExtrinsicGuess=True)
                #append if 'good'
                if retval: 
                    rv, tv = _rv, _tv
        
        # check, print, return
        if rv is None or rv is None or not retval:
            raise Error("Error occurred when calculating rotation and translation vectors.")
        
        print 'Rotation Vector:\n', rv
        print 'Translation Vector:\n', tv
        
        return rv, tv
    
    
    def reprojpts(self, obj_pts):
        #if len(obj_pts) == 0:
        #    raise Error('No points to project.')
        
        proj_imgpts, jac = cv2.projectPoints(np.asarray([obj_pts], dtype=np.float32), self.rv, self.tv, self.cam, self.distort)
        proj_imgpts = proj_imgpts.reshape((len(proj_imgpts), -1))
        
        #print 'Project Point Coordinates:'
        #for n in range(0, len(proj_imgpts)):
        #    print 'Point', n+1, ':', proj_imgpts[n]
        
        return proj_imgpts[0]

