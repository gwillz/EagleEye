# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders, Kin Kuen Liu
# version 0.1
# 
# A small function to automate a whole bunch of onscreen text calculations
# Loads font config from current working directory
# 

import cv2
from easyconfig import EasyConfig

__text_cfg__ = EasyConfig(group="fonts")
__text_pos__ = {}
__text_gap__ = 2

# calculate height offset of a line of text and display on top left
def displayText(frame, text, top=False, endl=False, colour=None):
    # dirty globals
    global __text_cfg__
    global __text_pos__
    global __text_gap__
    
    # load some settings
    if colour is None:
        colour = __text_cfg__.font_colour
    font = cv2.__dict__[__text_cfg__.font_family]
    
    # set first position
    if top or not 'next' in __text_pos__:
        textSize, baseLine = cv2.getTextSize(text, font, __text_cfg__.font_scale, __text_cfg__.font_thick)
        y_offset = textSize[1] + baseLine + __text_gap__
        __text_pos__ = {'next': (__text_gap__, y_offset), 'endl': (__text_gap__,y_offset)}
    
    # load positions
    if endl: x_offset, y_offset = __text_pos__['endl']
    else: x_offset, y_offset = __text_pos__['next']
    
    # draw text
    cv2.putText(frame, text, (x_offset, y_offset), 
                font, __text_cfg__.font_scale, colour, __text_cfg__.font_thick, cv2.LINE_AA)
    
    # calculate next positions
    textSize, baseLine = cv2.getTextSize(text, font, 
                                         __text_cfg__.font_scale, __text_cfg__.font_thick)
    
    x_offset += __text_gap__ + textSize[0]
    __text_pos__['endl'] = (x_offset, y_offset) # endl uses previous y_offset
    
    y_offset += textSize[1] + baseLine + __text_gap__
    __text_pos__['next'] = (__text_gap__, y_offset) # next resets the x_offset
    

if __name__ == "__main__":
    import numpy as np
    
    img_h, img_w = (500, 500)
    frame = np.zeros((img_h,img_w,3), np.uint8)
    
    displayText(frame, "hello")
    displayText(frame, "second line")
    displayText(frame, "third line")
    displayText(frame, "third again - but green!", endl=True, colour=(0, 255, 0))
    displayText(frame, "fourth line")
    displayText(frame, "red", endl=True, colour=(0, 0, 255))
    displayText(frame, "yellow", endl=True, colour=(0, 255, 255))
    
    cv2.imshow("test", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    exit(0)