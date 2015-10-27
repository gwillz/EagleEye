#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.2
# 
# Python interpretations of the c++ functions found in the OCamCalib toolbox at:
# https://sites.google.com/site/scarabotix/ocamcalib-toolbox/ocamcalib-toolbox-download-page
# 
# 

from ast import literal_eval
import math, numpy as np, cv2

class ocam_model:
    pol        = []
    invpol     = []
    xc         = 0.0
    yc         = 0.0
    c          = 0.0
    d          = 0.0
    width      = 0
    height     = 0
    len_pol    = 0
    len_invpol = 0
    path       = ""
    
    def __init__(self, path=None):
        if path is not None:
            self.open(path)
    
    def open(self, path):
        self.path = path
        
        with open(path, 'r') as file:
            # reader buffer
            buf = []
            at = 0
            
            while True: # load in the data
                line = file.readline()
                if line == "": break
                
                # convert all types appropriately
                split = literal_eval("[" + line.replace(" ", ",") + "]")
                if len(split) == 0: continue
                
                # add to a one biiiiig list
                buf += split
            
            # read poly length and values
            self.len_pol = buf[at]
            at += 1
            for pol in buf[at:at+self.len_pol]:
                self.pol.append(pol)
            at += self.len_pol
            
            # read inverse poly length and values
            self.len_invpol = buf[at]
            at += 1
            for ipol in buf[at:at+self.len_invpol]:
                self.invpol.append(ipol)
            at += self.len_invpol
            
            # center coords
            self.xc, self.yc = buf[at:at+2]
            at += 2
            
            # affine coefficients
            self.c, self.d, self.e = buf[at:at+3]
            at += 3
            
            # image size
            self.height, self.width = buf[at:at+2]
            at += 2
    
    
    def world2cam(self, point3D):
        norm  = np.sqrt(point3D[0]*point3D[0] + point3D[1]*point3D[1])
        point2D = (0, 0)
        
        if norm > 0:
            theta = math.atan(point3D[2]/norm)
            invnorm = 1/norm
            t  = theta
            rho = self.invpol[0]
            t_i = 1
            
            for ipol in self.invpol[1:]:
                t_i *= t
                rho += t_i*ipol
            
            x = point3D[0]*invnorm*rho
            y = point3D[1]*invnorm*rho
            
            return (x*self.c + y*self.d + self.xc, x*self.e + y + self.yc)
            
        else:
            return (self.xc, self.yc)
        
    
    def cam2world(self, point2D):
        invdet  = 1/(self.c-self.d*self.e) # 1/det(A), where A = [c,d;e,1] as in the Matlab file
        
        xp = invdet*(    (point2D[0] - self.xc) - self.d*(point2D[1] - self.yc) )
        yp = invdet*( -self.e*(point2D[0] - self.xc) + self.c*(point2D[1] - self.yc) )
        
        r   = np.sqrt(  xp*xp + yp*yp ) # distance [pixels] of  the point from the image center
        zp  = self.pol[0]
        r_i = 1
        
        for p in self.pol[1:]:
            r_i *= r
            zp  += r_i*p
        
        # normalize to unit norm
        invnorm = 1/np.sqrt( xp*xp + yp*yp + zp*zp )
        
        return  (invnorm*xp, invnorm*yp, invnorm*zp) #point3D
    
    
    def undistort_points(self, img_pts):
        out_pts = []
        
        for p in img_pts:
            M = (p[0], p[1], -1)
            out_pts.append(self.world2cam(M))
            
        return np.array(out_pts, np.float32)
    
    
    def perspective_undistort(self, mapx, mapy, sf=4.0):
        width, height = mapx.shape
        Nxc = height/2.0
        Nyc = width/2.0
        Nz = -width/sf
        
        for i in range(0, height):
            for j in range(0, width):
                M = ( (i-Nxc), (j-Nyc), Nz)
                m = self.world2cam(M)
                
                mapx[j,i] = m[1]
                mapy[j,i] = m[0]
        
        return mapx, mapy
    
    
    def __str__(self):
        return "poly: {}\ninvpoly: {}\ncentre: {}, {}\naffine:\n  c: {}\n  d: {}\n  e: {}\nimage: {} x {}".format(
                    self.pol,
                    self.invpol,
                    self.xc, self.yc,
                    self.c, self.d, self.e,
                    self.width, self.height)
    
    
if __name__ == "__main__":
    # open model file
    model = ocam_model("calib_results.txt")
    print "model: "
    print model
    print ""
    
    # test back and forth of cam2world and world2cam
    point2D = model.world2cam((100, 200, -300))
    point3D = model.cam2world(point2D) # not working..?
    print "test:"
    print point2D
    print point3D
    print ""
    
    # open an image with opencv
    image = cv2.imread("Backside_10_1.jpg")
    w,h = image.shape[:2]
    
    # fill mapx, mapy arrays
    mapx = np.zeros((h, w), np.float32)
    mapy = np.zeros((h, w), np.float32)
    
    # undisort and plug into opencv's remap function
    mapx, mapy = model.perspective_undistort(mapx, mapy, sf=10.0)
    undistort_image = cv2.remap(image, mapx, mapy, cv2.INTER_LINEAR)
    
    x, y = model.world2cam((0, 0, -100))
    cv2.circle(undistort_image, (int(x), int(y)), 2, (0,0,255), 2)
    
    # display, write, etc
    cv2.imshow("ocam_calib", undistort_image)
    cv2.imwrite("py_udisrort_persp.jpg", undistort_image)
    cv2.waitKey(0)
    
    print "done"
    exit(0)
