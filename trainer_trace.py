#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.1.8
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

# extra stuff
magnitude = lambda x: np.sqrt(np.vdot(x, x))
unit = lambda x: x / magnitude(x)
invert_colour = lambda x: 255 - x

def usage():
    print "usage: trainer_trace.py <calib xml> <trainer xml>  {-height <mm> | -width <mm> | -max_height <px> | -singlemode | -config <file> | -export <file>}"

#arrow drawing function
def draw_arrow(frame, position, direction, colour, length=750):
    global scale, img_h
    
    end = position + length * direction
    
    x, y, z = position
    pt1 = (int(x*scale), img_h-int(y*scale))
    x, y, z = end
    pt2 = (int(x*scale), img_h-int(y*scale))
    
    # draw
    cv2.circle(frame, pt1, 2, colour, 2)
    cv2.arrowedLine(frame, pt1, pt2, colour, 2)

def main(sysargs):
    args = EasyArgs(sysargs)
    global scale, img_h
    
    if 'help' in args:
        usage()
        return 0
    
    # arg sanity checks
    if len(args) < 3:
        usage()
        return 1
    
    # default args
    height = args.height or 3000        # milimetres
    width = args.width or 8000          # milimetres
    max_height = args.max_height or 400  # pixels
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
    
    # load appropriate mappers
    if not args.singlemode:
        mappers = [Mapper(args[1], args[2], cfg, Theta.Buttonside),
                   Mapper(args[1], args[2], cfg, Theta.Backside)]
    else:
        mappers = [Mapper(args[1], args[2], cfg, Theta.NonDual)]

    for m in mappers:
        colour = (55+random.random()*200,
                  55+random.random()*200,
                  55+random.random()*200)
        
        # calculate world camera pos
        Rt = np.matrix(m.R).T
        tv = -Rt.dot(np.matrix(m.tv))
        rv = unit(cv2.Rodrigues(-Rt)[0])
        
        unvis = 0
        pts = m.obj_pts
        
        for i in pts:
            # draw circle around it if not-visible
            x, y, z = i
            p = (int(x*scale), img_h-int(y*scale))
            cv2.circle(baseframe, p, 1, colour, 2)
            
            # circle the point if not visible
            if not m.isVisible((x,y,z)):
                unvis += 1
                cv2.circle(baseframe, p, 6, colour, 1)
        
        # draw direction of lens
        draw_arrow(baseframe, tv, rv, colour)
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
    return 0
    
if __name__ == "__main__":
    exit(main(sys.argv))
