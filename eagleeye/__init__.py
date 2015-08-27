#
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# magical init file that makes everything work!
# 

import os, sys
_eagleeye = os.path.join(os.path.dirname(sys.argv[0]), "eagleeye")

if os.path.isfile(os.path.join(_eagleeye, "image.py")): from image import Image
if os.path.isfile(os.path.join(_eagleeye, "buff_cap.py")): from buff_cap import BuffCap
if os.path.isfile(os.path.join(_eagleeye, "dataset.py")): from dataset import Dataset
if os.path.isfile(os.path.join(_eagleeye, "buff_dataset.py")): from buff_dataset import Buffset
if os.path.isfile(os.path.join(_eagleeye, "cv_keys.py")): from cv_keys import Key
if os.path.isfile(os.path.join(_eagleeye, "mem_dataset.py")): from mem_dataset import Memset
if os.path.isfile(os.path.join(_eagleeye, "cv_flags.py")): from cv_flags import CVFlag
if os.path.isfile(os.path.join(_eagleeye, "easyconfig.py")): from easyconfig import EasyConfig
if os.path.isfile(os.path.join(_eagleeye, "viconsocket.py")): from viconsocket import ViconSocket
if os.path.isfile(os.path.join(_eagleeye, "sleeper.py")): from sleeper import Sleeper
if os.path.isfile(os.path.join(_eagleeye, "easyargs.py")): from easyargs import EasyArgs
