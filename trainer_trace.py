#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.1
#
#
# Options:
#   -max_height      : to adjust the scaling (in pixels)
#   -width & -height : adjusts the bounds of the lab floor (in milimetres) 
#

import cv2, sys, os, numpy as np, random
from eagleeye import EasyArgs, EasyConfig, Key, Mapper, xml_trainer, Theta

def usage():
    print "usage: trace.py <calib xml> <trainer xml>  {-height | -width | -max_height | -config <file> | -export <file>}"

magnitude = lambda x: np.sqrt(np.vdot(x, x))
unit = lambda x: x / magnitude(x)

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

backside = Mapper(args[1], args[2], cfg, Theta.Backside)
buttonside = Mapper(args[1], args[2], cfg, Theta.Buttonside)
#single = Mapper(args[1], args[2], cfg, Mapper.SINGLE)

#for m in [single]:
for m in [backside, buttonside]:
    colour = (55+random.random()*200,
              55+random.random()*200,
              55+random.random()*200)
    
    tv = np.abs(m.tv)
    rv = unit(m.rv)
    pts = m.obj_pts
    
    end = tv + 750 * rv
    
    # draw
    x, y, z = tv
    pt1 = (int(x*scale), img_h-int(y*scale))
    x, y, z = end
    pt2 = (int(x*scale), img_h-int(y*scale))
    
    print pt1, pt2
    
    cv2.circle(baseframe, pt1, 2, colour, 2)
    cv2.arrowedLine(baseframe, pt1, pt2, colour, 2)
    
    
    for i in pts:
        print i
        x, y, z = i
        p = (int(x*scale), img_h-int(y*scale))
        cv2.circle(baseframe, p, 1, colour, 2)

cv2.imshow(window_name, baseframe)
cv2.waitKey(0)

if args.export:
    cv2.imwrite(args.export, baseframe)

cv2.destroyAllWindows()

print "\ndone"
exit(0)
