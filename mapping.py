#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.2.3
# 
# Runs mapping routines on multiple CSV files and combines them into a single XML format.
#
# usage: python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> {<multiple csv files>}
#

import sys, os
from elementtree.SimpleXMLWriter import XMLWriter
from eagleeye import Dataset, EasyArgs
from mapping_func import *

def usage():
    print "python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> {<multiple csv files>}"

args = EasyArgs()

if not args.verifyOpts("calib", "trainer", "output"):
    print "Must specify: -calib, -trainer, -output files"
    usage()
    exit(1)
    
if not args.verifyLen(2):
    print "Not enough input CSV files"
    usage()
    exit(1)

# open calib files
mapper = Mapper(args.calib, args.trainer)

# open destination XML
with open(args.output, "w") as xmlfile:
    w = XMLWriter(xmlfile)
    w.declaration()
    xmlfile.write("<!DOCTYPE dataset SYSTEM \"http://storage.gwillz.com.au/eagleeye_v2.dtd\">")
    doc = w.start("dataset")
    
    # working vars
    csvs = []
    frame_num = 1
    last_flash = True
    
    # open source CSV datasets
    for i in range(1, len(args._noops)):
        print args[i]
        csvs.append(Dataset(args[i], i))
    
    
    # reel all the files up to their first flash
    for c in csvs:
        c.reel()
    
    while True:
        w.start("frameInformation")
        w.element("frame", number=str(frame_num))
        
        for c in csvs:
            # run projection/mapping on data
            points = mapper.calpts((
                            float(c.row()[2]),
                            float(c.row()[3]),
                            float(c.row()[4])
                            ))
            
            w.start("object", id=c.id(), name=c.name())
            w.element("boxinfo", height="99", width="99", x=str(points[0]+50), y=str(points[1]+50))
            w.element("centroid", x=str(points[0]), y=str(points[1]))
            w.end()
            
            #verify the flash status
            c.verifyFlash() # TODO: this is silly, why do we do this?
            
        w.end()
        
        # test flashes
        # TODO: redundant? - new auto_flasher only has a single 'F' per flash
        flashes = 0
        for c in csvs:
            if c.flash(): flashes += 1
        all_flash = (len(csvs) == flashes)
        
        if last_flash and not all_flash: #end of flash
            last_flash = False
        elif not last_flash and all_flash: #second flash
            print "end of all datasets"
            break
        
        frame_num += 1
        
        # load next frame, remove when they finish
        for c in csvs:
            if not c.next():
                c.close()
                csvs.remove(c)
                print "end of file:", c.name()
        
        # break if all files have ended
        if len(csvs) == 0:
            print "all datasets exhausted!"
            break
    
    w.close(doc)
    
exit(0)
