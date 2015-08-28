#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.2.9
# 
# Runs mapping routines on multiple CSV files and combines them into a single XML format.
#
# usage: python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> {<multiple csv files>}
#

import sys, os
from elementtree.SimpleXMLWriter import XMLWriter
from eagleeye import Dataset, EasyArgs, Mapper

def usage():
    print "python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> [<multiple csv files>] {--config <file>}"

def main(sysargs):
    args = EasyArgs(sysargs)

    if not args.verifyOpts("calib", "trainer", "output"):
        print "Must specify: -calib, -trainer, -output files"
        usage()
        return 1
        
    if not args.verifyLen(2):
        print "Not enough input CSV files"
        usage()
        return 1

    # open calib files
    mapper = Mapper(args.calib, args.trainer)

    # open destination XML
    with open(args.output, "w") as xmlfile:
        w = XMLWriter(xmlfile)
        w.declaration()
        xmlfile.write("<!DOCTYPE dataset SYSTEM \"http://storage.gwillz.com.au/eagleeye_v2.dtd\">")
        doc = w.start("dataset")
        
        # working vars
        csvs = {}
        frame_num = 1
        
        # open source CSV datasets
        for i in range(1, len(args._noops)):
            print args[i]
            csvs[i] = Dataset(args[i])
        
        
        # reel all the files up to their first flash
        for i in csvs:
            csvs[i].reel()
        
        while True:
            w.start("frameInformation")
            w.element("frame", number=str(frame_num))
            
            for c in csvs:
                c = csvs[i]
                # run projection/mapping on data
                points = mapper.calpts((
                                float(c.row()[2]),
                                float(c.row()[3]),
                                float(c.row()[4])
                                ))
                
                w.start("object", id=str(c), name=c.name())
                w.element("boxinfo", height="99", width="99", x=str(points[0]-50), y=str(points[1]-50))
                w.element("centroid", x=str(points[0]), y=str(points[1]))
                w.end()
                
            w.end()
            
            # test flashes
            flashes = 0
            for i in csvs:
                if csvs[i].flash(): flashes += 1
            
            if len(csvs) == flashes:
                print "end of all datasets"
                break
            
            frame_num += 1
            
            # load next frame, remove when they finish
            for i in csvs:
                c = csvs[i]
                
                if not c.next():
                    c.close()
                    print "end of file:", c.name()
                    del csvs[i]
            
            # break if all files have ended
            if len(csvs) == 0:
                print "all datasets exhausted!"
                break
        
        w.close(doc)
        
    return 0

if __name__ == '__main__':
    exit(main(sys.argv))
