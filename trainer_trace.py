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
    mappers = [Mapper(args[1], args[2], cfg, Theta.Backside),
               Mapper(args[1], args[2], cfg, Theta.Buttonside)]
else:
    mappers = [Mapper(args[1], args[2], cfg, Theta.NonDual)]

# set fake camera pos
fake_tv = np.array((4250, 1550, 400), np.float32).reshape(3,1)
fake_rv = np.array((1, 0, 0)).reshape(3,1)

#mappers[0].tv = mappers[1].tv = fake_tv
#mappers[0].rv = fake_rv * -1
#mappers[1].rv = fake_rv

for m in mappers:
    colour = (55+random.random()*200,
              55+random.random()*200,
              55+random.random()*200)
    
    R = cv2.Rodrigues(m.rv)[0]
    Rt = np.matrix(R).T
    tv = -Rt * np.matrix(m.tv)
    
    
    #rv = -Rt[2].reshape(3,1)
    rv = cv2.Rodrigues(Rt)[0]
    
    # fake camera pos
    #m.rv_unit = unit(m.rv)
    #tv = m.tv
    #rv = m.rv
    
    vis = 0
    pts = m.obj_pts
    
    for i in pts:
        # draw points
        x, y, z = i
        p = (int(x*scale), img_h-int(y*scale))
        cv2.circle(baseframe, p, 1, colour, 2)
        
        # test visibility
        if m.isVisible((x,y,z)): vis += 1
        else: 
            cv2.circle(baseframe, p, 6, colour, 1)
            print "invisible:", x, y, z
    
    # draw
    draw_arrow(baseframe, tv, rv, colour)
    displayText(baseframe, "{}: {}, {}, {}".format(Theta.name(m.mode), *tv), colour=colour)
    displayText(baseframe, " visible: {}/{}".format(vis, len(pts)), endl=True, colour=colour)

# clean up
cv2.imshow(window_name, baseframe)
cv2.waitKey(0)

if args.export:
    cv2.imwrite(args.export, baseframe)

cv2.destroyAllWindows()

print "\ndone"
exit(0)
