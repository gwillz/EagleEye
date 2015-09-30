#!/usr/bin/env python2
#
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.2.11
# 
# Runs mapping routines on multiple CSV files and combipnes them into a single XML format.
#
# usage: python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> {<multiple csv files>}
#

import sys, os
from elementtree.SimpleXMLWriter import XMLWriter
from eagleeye import Memset, EasyArgs, EasyConfig, Mapper

def usage():
    print "python2 mapping.py -c <calib xml> -t <trainer xml> -o <output dataset> [<multiple csv files>] {--config <file>}"

def main(sysargs):
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.cfg, group="mapper")

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
    frame_num = 0
    
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
    mapper = Mapper(args.calib, args.trainer, cfg)

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
                # determine marker quality
                try:
                    max_reflectors = int(c.row()[8])
                    visible_reflectors = int(c.row()[9])
                except:
                    print "Error in reading quality at row {}".format(i)
                    return 1

                try:
                    # read VICON data
                    x = float(c.row()[2])
                    y = float(c.row()[3])
                    z = float(c.row()[4])
                    
                    # TODO: Render Orientation Here
                    rx = float(c.row()[5])
                    ry = float(c.row()[6])
                    rz = float(c.row()[7])
                except:
                    print "Error occurred when converting VICON data at row {}".format(i)
                    return 1
                    mode = cfg.quality_mode
                
                # run projection/mapping on VICON data
                points = mapper.reprojpts((x, y, z))

                # TODO: Change DTD and double check with Manjung
                w.start("object", id=str(i), name=c.name())
                w.element("boxinfo", height="99", width="99", x=str(points[0]-50), y=str(points[1]-50))
                w.element("centroid", x=str(points[0]), y=str(points[1]), rx=str(rx), ry=str(ry), rz=str(rz))
                w.element("visibility", visible=str(visible_reflectors), visibleMax=str(max_reflectors))
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
