#!/usr/bin/env python2
#
# Eagle Eye - Group 15 - UniSA
# Gwilyn Saunders - 2015
# version: 0.4.2
# 
# Opens image files from the ricoh theta, does stuff
# 
# TODO:
#  - video processing
#  - correct unwarping
#  - detailed class description/README (explain default settings)
# 

import cv2, numpy as np, sys, os

class Image:
    # status modes
    IMG_NONE = 0
    IMG_OPEN = 1
    IMG_SPLITS = 2
    IMG_UNWARP = 4
    IMG_STITCH = 8
    IMG_ALL = 16
    
    def __init__(self, path=None):
        self.DEBUG = False
        
        # auto open if a path is specified
        if path != None:
            self.path = path
            self.open(path)
        else:
            self.status = self.IMG_NONE
    
    def open(self, path):
        self._debug('opening... ', endl=False)
        
        # grab filename (for output names later)
        self.name = os.path.basename(path)
        self.img = cv2.imread(path)
        
        self.status = self.IMG_OPEN
        self._debug('done')
    
    def load(self, name, img): # UNTESTED
        if type(img) != "numpy.ndarray":
            sys.stderr.write("assert: 'img' not a numpy array")
            
        self.img = img
        self.name = name
        
        #if self.name[-3:] # TODO: check extension thingy
        
        self.status = self.IMG_OPEN
        self._debug('image loaded.')
    
    def split(self, crop=(120, 0, 0, 0)):
        if self.status < self.IMG_OPEN:
            print "split: must open first"
            return
        self._debug('splitting... ', endl=False)
        
        # split (and crop) at the same time
        h,w = self.img.shape[:2]
        self.left = self.img[0-crop[2]:h-crop[0], 0-crop[3]:w/2-crop[1]]
        self.right = self.img[0-crop[2]:h-crop[0], w/2-crop[3]:w-crop[1]]
        
        # reset/set map status on new image dimensions
        self.mapped = False
        
        self.status = self.IMG_SPLITS
        self._debug('done')
    
    def rotate(self, degree=3):
        if self.status < self.IMG_SPLITS:
            print "rotate: must split first"
            return
        self._debug('rotating... ', endl=False)
        
        # easy one here
        self.left = np.rot90(self.left, degree)
        self.right = np.rot90(self.right, degree)
        
        # reset mapping, rotations can change dimensions
        self.mapped = False
        
        self._debug('done')
    
    def scale(self, factor=1.0, mode=cv2.INTER_AREA):
        if self.status < self.IMG_SPLITS:
            print "scaling: must split first"
            return
        self._debug('scaling... ', endl=False)
        
        h, w = self.left.shape[:2]
        dim = (int(h*factor), int(w*factor))
        self.left = cv2.resize(self.left, dim, interpolation=mode)
        self.right = cv2.resize(self.right, dim, interpolation=mode)
        
        self._debug('done')
    
    def unwarp(self, mode=cv2.INTER_LINEAR):
        if self.status < self.IMG_SPLITS:
            print "unwarp: must split first"
            return
        self._debug('unwarping... ', endl=False)
        
        # only need to calculate the maps once
        if not self.mapped:
            # dimensions
            srcH, srcW = self.left.shape[:2]
            dstH = srcH
            dstW = srcW * (4.0/3.0)
            
            # build (or rebuild) the map
            self.map_x, self.map_y = self._buildMap(srcW, srcH, dstW, dstH)
            self.mapped = True
        
        # use the same map for both left/right (same dimensions anyway)
        self.left = cv2.remap(self.left, self.map_x, self.map_y, mode)
        self.right = cv2.remap(self.right, self.map_x, self.map_y, mode)
        
        self.status = self.IMG_UNWARP
        self._debug('done')
        
    def stitch(self):
        if self.status < self.IMG_UNWARP:
            print "stitch: must unwarp first"
            return
        self._debug('stitching... ', endl=False)
        
        # this often throws a seg fault if it can't stich
        # TODO: is there a try/except that can handle this..?
        h,w = self.left.shape[:2]
        st = cv2.createStitcher()
        stat, self.stitched = st.stitch([ \
                                self.left[0:h, 0:w/2], \
                                self.right, \
                                self.left[0:h, w/2:w]])
        
        if stat == None:
            self._debug('failed')
            return
        
        self.status = self.IMG_STITCH
        self._debug('done')
    
    def save(self, mode=-1, dest="./"):
        # define switch cases
        def s_none():
            sys.stderr.write("nothing is saved\n")
            sys.stderr.flush()
        def s_orig():
            cv2.imwrite(dest+"orig_"+self.name, self.img)
        def s_splits():
            cv2.imwrite(dest+"left_"+self.name, self.left)
            cv2.imwrite(dest+"right_"+self.name, self.right)
        def s_stitch():
            cv2.imwrite(dest+"final_"+self.name, self.stitched)
        def s_all():
            s_orig()
            s_splits()
            s_stitch()
        
        # allocate appropriate functions per status
        switch = {0: s_none,
                  1: s_orig,
                  2: s_splits,
                  4: s_splits,
                  8: s_stitch,
                  16: s_all}
        
        # default to wherever the status is at
        if mode == -1:
            mode = self.status
        
        # execute, or do nothing
        self._debug('saving... ', endl=False)
        try:
            switch[mode]()
            self._debug(switch[mode].__name__ + ' - done')
        except KeyError:
            s_none()
            self._debug('failed')
    
    def _debug(self, text, endl=True):
        if self.DEBUG:
            sys.stdout.write(text)
            if endl: sys.stdout.write("\n")
            sys.stdout.flush()
    
    # I think a bunch of these values are all mixed up. 
    # ie. (height for width, width for height)
    # nabbed from: http://www.kscottz.com/fish-eye-lens-dewarping-and-panorama-stiching/
    def _buildMap(self, wW, wH, unW, unH, hfovd=180.0, vfovd=180.0):
        # Build the fisheye mapping
        map_x = np.zeros((unH,unW),np.float32)
        map_y = np.zeros((unH,unW),np.float32)
        vfov = (vfovd/180.0)*np.pi
        hfov = (hfovd/180.0)*np.pi
        vstart = ((180.0-vfovd)/180.00)*np.pi/2.0
        hstart = ((180.0-hfovd)/180.00)*np.pi/2.0
        count = 0
        # need to scale to changed range from our
        # smaller cirlce traced by the fov
        xmax = np.sin(np.pi/2.0)*np.cos(vstart)
        xmin = np.sin(np.pi/2.0)*np.cos(vstart+vfov)
        xscale = xmax-xmin
        xoff = xscale/2.0
        zmax = np.cos(hstart)
        zmin = np.cos(hfov+hstart)
        zscale = zmax-zmin
        zoff = zscale/2.0
        # Fill in the map, this is slow but
        # we could probably speed it up
        # since we only calc it once, whatever
        for y in range(0,int(unH)):
            for x in range(0,int(unW)):
                count = count + 1
                phi = vstart+(vfov*((float(x)/float(unW))))
                theta = hstart+(hfov*((float(y)/float(unH))))
                xp = ((np.sin(theta)*np.cos(phi))+xoff)/zscale#
                zp = ((np.cos(theta))+zoff)/zscale#
                xS = wW-(xp*wW)
                yS = wH-(zp*wH)
                map_x.itemset((y,x),int(xS))
                map_y.itemset((y,x),int(yS))
        
        return map_x, map_y
