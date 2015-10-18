#
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# magical init file that makes everything work!
# 

import cv2
if cv2.__version__ < '3.0.0':
    raise Exception("EagleEye only supports OpenCV 3.0+")

from easyargs import EasyArgs
from easyconfig import EasyConfig
from cv_keys import Key
from buff_split_cap import BuffSplitCap
from xmlset import Xmlset
from mem_dataset import Memset
from sleeper import Sleeper
from marker_tool import marker_tool
from mapping_func import Mapper
from xml_trainer import Xmltrainer
from theta_sides import Theta
