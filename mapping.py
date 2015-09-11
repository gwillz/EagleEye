#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.2.11
# 
# Runs mapping routines on multiple CSV files and combines them into a single XML format.
#
# usage: python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> {<multiple csv files>}
#

import sys, os
from elementtree.SimpleXMLWriter import XMLWriter
from eagleeye import Memset, EasyArgs, Mapper

def usage():
    print "python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> [<multiple csv files>] {--config <file>}"

def main(sysargs):
    args = EasyArgs(sysargs)

    if ["calib", "trainer", "output"] not in args:
        print "Must specify: -calib, -trainer, -output files"
        usage()
        return 1
        
    if len(args) == 1:
        print "Not enough input CSV files"
        usage()
        return 1
    
    # working vars
    csvs = {}
    frame_num = 1
    
    # open source CSV datasets
    for i in range(1, len(args)):
        print args[i]
        csvs[i] = Memset(args[i])
    
    
    # reel all the files up to their first flash
    for i in csvs:
        csvs[i].restrict()
        if len(csvs[i].row()) < 10:
            print "CSV file:", args[i], "contains no marker data!\nAborting."
            return 1
    
    # open calib files
    mapper = Mapper(args.calib, args.trainer)

    # open destination XML
    with open(args.output, "w") as xmlfile:
        w = XMLWriter(xmlfile)
        w.declaration()
        xmlfile.write("<!DOCTYPE dataset SYSTEM \"http://storage.gwillz.com.au/eagleeye_v2.dtd\">")
        doc = w.start("dataset")
        
        # main loop
        while True:
            w.start("frameInformation")
            w.element("frame", number=str(frame_num))
            
            for i in csvs:
                c = csvs[i]
                # run projection/mapping on data
                points = mapper.calpts((
                                float(c.row()[2]),
                                float(c.row()[3]),
                                float(c.row()[4])
                                ))
                
                # determine marker quality
                quality = float(c.row()[9]) / float(c.row()[8])
                
                w.start("object", id=str(i), name=c.name())
                w.element("boxinfo", height="99", width="99", x=str(points[0]-50), y=str(points[1]-50))
                w.element("centroid", x=str(points[0]), y=str(points[1]))
                w.element("quality", str(quality))
                w.end()
                
            w.end()
            
            # test end of files
            eofs = 0
            for i in csvs:
                if csvs[i].eof(): eofs += 1
            
            if len(csvs) == eofs:
                print "end of all datasets"
                break
            
            
            # load next frame
            frame_num += 1
            for i in csvs:
                csvs[i].next()
        
        w.close(doc)
        
    return 0

if __name__ == '__main__':
    exit(main(sys.argv))
