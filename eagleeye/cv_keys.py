#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
#

import locale as lc

class Key:
    if lc.getdefaultlocale()[1] == "UTF-8":
        enter = 10
        right = 65363
        left  = 65361
    else:
        enter = 13
        right = 2555904
        left  = 2424832
    space = 32
    esc   = 27
    up    = 2490368
    down  = 2621440
    
    @staticmethod
    def char(key, char):
        return key & 0xFF == ord(char)
