#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.5
#
#
# Options:
#   -max_height      : to adjust the scaling (in pixels)
#   -width & -height : adjusts the bounds of the lab floor (in milimetres) 
#   -export          : save a png image 
#   -singlemode      : load a 

import cv2, sys, os, numpy as np, random
from eagleeye import EasyArgs, EasyConfig, Key, Mapper, xml_trainer, Theta
from eagleeye.display_text import *

def usage():
    print "usage: trainer_trace.py <calib xml> <trainer xml>  {-height <mm> | -width <mm> | -max_height <px> | -singlemode | -config <file> | -export <file>}"


# extra stuff
magnitude = lambda x: np.sqrt(np.vdot(x, x))
unit = lambda x: x / magnitude(x)
invert_colour = lambda x: 255 - x

rot_z = lambda x: np.matrix([[np.cos(x), np.sin(x), 0], [-np.sin(x), -np.cos(x), 0], [0,0,1]])

def draw_arrow(frame, position, direction, colour, length=750):
    end = position + length * direction
    
    x, y, z = position
    pt1 = (int(x*scale), img_h-int(y*scale))
    x, y, z = end
    pt2 = (int(x*scale), img_h-int(y*scale))
    
    # draw
    cv2.circle(frame, pt1, 2, colour, 2)
    cv2.arrowedLine(frame, pt1, pt2, colour, 2)



args = EasyArgs()

# arg sanity checks
if len(args) < 3:
    usage()
    exit(1)

# default args
height = args.height or 3000        # milimetres
width = args.width or 8000          # milimetres
max_height = args.max_height = 400  # pixels
cfg = EasyConfig(args.config, group="mapper")

# working vars
scale = float(max_height) / height
img_h = int(height * scale)
img_w = int(width * scale)

# open window
window_name = "Tracer"
cv2.namedWindow(window_name)

# settings
font = cv2.FONT_HERSHEY_SIMPLEX
text_size = 0.5
colour = (255,255,255)

# a frame to paste the trace on
baseframe = np.zeros((img_h,img_w,3), np.uint8)

if not args.singlemode:
    mappers = [Mapper(args[1], args[2], cfg, Theta.Buttonside),
               Mapper(args[1], args[2], cfg, Theta.Backside)]
else:
    mappers = [Mapper(args[1], args[2], cfg, Theta.NonDual)]

# set fake camera pos
fake_tv = np.array((4250, 1550, 400), np.float32).reshape(3,1)
fake_rv = np.array((1, 0, 0), np.float32).reshape(3,1)

# canon
#fake_tv = np.array((-14092.8, -5203.8, -9875.6)).reshape(3,1)
#fake_rv = np.array((-1.8478, -0.92707, -2.61688)).reshape(3,1)

print "fake_tv", fake_tv

#mappers[0].tv = fake_tv
#mappers[0].rv = fake_rv
#if len(mappers) > 1:
    #mappers[1].tv = fake_tv
    #mappers[1].rv = fake_rv * -1

for m in mappers:
    colour = (55+random.random()*200,
              55+random.random()*200,
              55+random.random()*200)
    
    
    #Rt = np.matrix(m.R).T
    #print "Rt", Rt
    #print np.linalg.inv(m.tv)
    #tv = -Rt.dot(np.matrix(m.tv))
    
    #print "rv_tv", tv
    #rv = cv2.Rodrigues(Rt)[0]
    
    tv = m.tv
    rv = m.rv
    
    #rv = Rt[1].reshape(3,1)
    #tv = np.add(Rt.dot(np.array([0.,0.,0.]).reshape(3,1)), m.tv)
    #print np.squeeze(m.tv)
    #tv = Rt * m.tv
    #print tv
    #tv = m.tv
    #print magnitude(tv)
    #print tv
    
    
    #print "R", R
    #print "Rt",  Rt
    
    #rv = cv2.Rodrigues(R)[0]
    
    #Rt - 
    
    #Rt = np.matrix(R).T
    
    #m.rv = _rv
    #m.tv = _tv
    #m.rv_unit = unit(_rv)
    
    #tv = np.array([0,0,0]).T
    #rv = np.array([0,0,1]).T
    
    # fake camera pos
    #m.rv_unit = unit(m.rv)
    #tv = m.tv
    #rv = m.rv
    
    # count how many points are visible
    unvis = 0
    pts = m.obj_pts
    
    for i in pts:
        # draw points
        #print "obj", i
        #print "apply R", R.dot(i)
        #print "squeeze", np.squeeze(m.tv)
        #i_cam = np.add(R.dot(i), np.squeeze(tv))
        #print "R x i", R.dot(i)
        #print "apply R and tv", i_cam
        
        #print "compare: 0 <", i_cam[2]
        
        #x, y, z = (i + _tv) * _rv
        #i_cam = R * i + m.tv
        #i_cam = + fake_tv
        
        #x, y, z = i
        
        ##print "r", r
        ##print "theta", np.degrees(theta)
        
        #r = np.linalg.norm(np.squeeze(i_cam))
        #theta = np.arctan2(i_cam[1], i_cam[0])
        #phi = np.arccos(i_cam[2]/r)
        #inv_phi = phi
        
        #print "obj    ", i
        #print "obj_cam", i_cam
        #print "inv_phi", np.degrees(inv_phi), "<", np.degrees(m.half_fov)
        
        # draw circle around it if not-visible
        x, y, z = i
        p = (int(x*scale), img_h-int(y*scale))
        cv2.circle(baseframe, p, 1, colour, 2)
        
        if not m.isVisible((x,y,z)):
        #if not inv_phi < m.half_fov:
            unvis += 1
            cv2.circle(baseframe, p, 6, colour, 1)
            #print "invisible:", x, y, z
    
    #tv = fake_tv
    #rv = m.rv
    # draw direction of lens
    draw_arrow(baseframe, fake_tv, fake_rv, colour)
    # and it's FOV
    #draw_arrow(baseframe, tv, rot_z(m.half_fov).dot(rv), colour, length=375)
    #draw_arrow(baseframe, tv, rot_z(-m.half_fov).dot(rv), colour, length=375)
    
    # and some text data stuff
    displayText(baseframe, "{}: {}, {}, {}".format(Theta.name(m.mode), *tv), colour=colour)
    displayText(baseframe, " visible: {}/{}".format(len(pts)-unvis, len(pts)), endl=True, colour=colour)

# clean up
cv2.imshow(window_name, baseframe)
cv2.waitKey(0)

if args.export:
    cv2.imwrite(args.export, baseframe)

cv2.destroyAllWindows()

print "\ndone"
exit(0)
