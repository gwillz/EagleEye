#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders & Kin Kuen Liu
# version 0.5.32
#
# Process 1:
#  Left/right arrow keys to navigate the video
#  [ and ] to mark in/out the flash
#  ENTER to confirm and start clicker (Process 2)
#  ESC to quit
#
# Process 2:
#  Left click to mark wand centre
#  Left/right arrow keys to navigate the video
#  BACKSPACE to remove a previous record
#  ENTER to save (write XML)
#  ESC to abort (don't write XML)
# 
# Note:
#   add 'mark in and out' values to args to skip 'Process 1'
#
#
# TODO:
#   - add zoomer to Process 2 (probs requires QT)
#   - resize video to screen size in Process 1
# 

import sys, cv2, numpy as np, time, os
from eagleeye import BuffSplitCap, Memset, Key, EasyConfig, EasyArgs, marker_tool
from eagleeye.display_text import *
from elementtree.SimpleXMLWriter import XMLWriter

def usage():
    print "usage: python2 trainer.py <video file> <csv file> <data out file> {<mark_in> <mark_out> | --clicks <num_clicks> | --config <file>}"

# clicker status
class Status:
    stop   = 0
    record = 1
    skip   = 2
    back   = 3
    remove = 4
    wait   = 5
    still  = 6

def main(sysargs):
    # settings
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.config, group="trainer")
    max_clicks = args.clicks or cfg.default_clicks
    window_name = "EagleEye Trainer"
    
    textstatus = ""
    
    # grab marks from args
    if len(args) > 5:
        mark_in = args[4]
        mark_out = args[5]
        
        # test integer-ness
        try: int(mark_in) and int(mark_out)
        except: 
            usage()
            return 1
        
    elif len(args) > 3:
        ret, mark_in, mark_out = marker_tool(args[1], cfg.buffer_size, window_name)
        if not ret:
            print "Not processing - exiting."
            return 1
    else:
        usage()
        return 1
    
    ## clicking time!
    cropped_total = mark_out - mark_in
    print "video cropped at:", mark_in, "to", mark_out, "- ({} frames)".format(cropped_total)
    
    # clicking function
    def on_mouse(event, x, y, flags, params):
        # left click to mark
        if event == cv2.EVENT_LBUTTONDOWN:
            params['pos'] = (x, y)
            params['status'] = Status.record
            
        # right click to skip
        elif event == cv2.EVENT_RBUTTONDOWN:
            params['status'] = Status.skip
    
    # working variables
    params = {'status': Status.skip, 'pos': None}
    write_xml = False
    if cfg.dual_mode:
        trainer_points = {BuffSplitCap.left:{}, BuffSplitCap.right:{}}
    else:
        trainer_points = {BuffSplitCap.both:{}}
    
    # ensure minimum is 4 as required by VICON system
    min_reflectors = cfg.min_reflectors if cfg.min_reflectors >= 4 else 4
    print "Minimum reflectors: {} | Ignore Negative xyz: {}".format(min_reflectors, cfg.check_negatives)
        
    # load video (again)
    in_vid = BuffSplitCap(args[1], crop=(0,0,0,0), rotate=BuffSplitCap.r0, buff_max=cfg.buffer_size)
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, on_mouse, params)
    
    # load csv (with appropriate ratio)
    in_csv = Memset(args[2])
    in_csv.restrict()
    in_csv.setRatio(cropped_total)
    
    # test for marker data
    if len(in_csv.row()) < 10:
        print "This CSV contains no marker data!\nAborting."
        return 1
    
    # status
    print ""
    print "Writing to:", args[3]
    print "Number of clicks at:", max_clicks
    print ""
    
    # default right side (buttonside)
    if cfg.dual_mode:
        lens = BuffSplitCap.right
    else:
        lens = BuffSplitCap.both
    
    # grab clicks (Process 2)
    while in_vid.isOpened():
        # restrict to flash marks
        if in_vid.at() < mark_in:
            in_vid.next()
            continue
        # TODO: Last frame prints wrong frame number in console, something to do with the print position and loop
        if in_vid.at() >= (mark_in + cropped_total) or in_vid.at() >= mark_out:
            write_xml = True
            print "\nend of video: {}/{}".format(in_vid.at(), mark_out -1)
            break
        
        sys.stdout.write("Current Video Frame: {} / {}".format(in_vid.at(), mark_out -1)
                 + " | Clicks {} / {}\r".format(len(trainer_points), max_clicks))
        sys.stdout.flush()
        
        # load frame
        frame = in_vid.frame(side=lens)
        
        # prepare CSV data, click data
        tx = float(in_csv.row()[2])
        ty = float(in_csv.row()[3])
        tz = float(in_csv.row()[4])
        rx = float(in_csv.row()[5])
        ry = float(in_csv.row()[6])
        rz = float(in_csv.row()[7])
        
        # data quality status
        visible = int(in_csv.row()[9])
        max_visible = int(in_csv.row()[8])
        
        # status text to write
        textrow = "VICON - x: {:.4f} y: {:.4f} z: {:.4f} | rx: {:.4f} ry: {:.4f} rx: {:.4f}".format(tx, ty, tz, rx, ry, rz)
        textquality = "Visible: {} , Max Visible: {}".format(visible, max_visible)
        textstatus = "{} | {}/{} clicks".format(in_vid.status(), len(trainer_points[lens]), max_clicks)
        if lens == BuffSplitCap.left:
            textstatus += " - back side"
        elif lens == BuffSplitCap.right:
            textstatus += " - button side"
        #else none
        
        # assume good data, unless it fails the following tests
        dataStatus = " - Good data!!"
        dataStatus_colour = (0, 255, 0) # green
        dataQuality = True      # True = good, False = bad
        
        # Minimum points of reflectors, must be at least 4 (or whatever the config specifies)
        if visible < min_reflectors:
            dataQuality = False
            dataStatus = " - Bad data!!"
            dataStatus_colour = (0, 0, 255) # red
        
        if cfg.check_negatives:
            if tx < 0 or ty < 0 or tz < 0:
                dataQuality = False
                dataStatus += " - Bad data!!"
                dataStatus_colour = (0, 0, 255) # red
                
        # draw the trainer dot (if applicable)
        if in_vid.at() in trainer_points[lens]:
            cv2.circle(frame, trainer_points[lens][in_vid.at()][0], 1, cfg.font_colour, 2)
            cv2.circle(frame, trainer_points[lens][in_vid.at()][0], 15, cfg.font_colour, 1)
        
        # draw text and show
        displayText(frame, textrow, top=True)
        displayText(frame, textquality)
        displayText(frame, textstatus)
        displayText(frame, dataStatus, endl=True, colour=dataStatus_colour)
        
        cv2.imshow(window_name, frame)
        
        # pause for input
        while params['status'] == Status.wait:
            key = cv2.waitKey(10)
            if key == Key.esc:
                params['status'] = Status.stop
            elif key == Key.enter:
                write_xml = True
                params['status'] = Status.stop
            elif key == Key.right:
                params['status'] = Status.skip
            elif key == Key.left:
                params['status'] = Status.back
            elif key == Key.backspace:
                params['status'] = Status.remove
            elif Key.char(key, '1') and cfg.dual_mode:
                params['status'] = Status.still
                lens = BuffSplitCap.left
            elif Key.char(key, '2') and cfg.dual_mode:
                params['status'] = Status.still
                lens = BuffSplitCap.right
            
        # catch exit status
        if params['status'] == Status.stop:
            print "\nprocess aborted!"
            break
        
        # write data
        if params['status'] == Status.record \
                and len(trainer_points[lens]) != max_clicks: # TODO: does this disable recording clicks on the last frame
                
            if not cfg.ignore_baddata or dataQuality:
                trainer_points[lens][in_vid.at()] = (params['pos'], in_csv.row()[2:5], in_csv.row()[8:10])
            params['status'] = Status.skip
        
        # or remove it
        elif params['status'] == Status.remove \
                and in_vid.at() in trainer_points:
            del trainer_points[lens][in_vid.at()]
            print "\nremoved dot"
        
        # load next csv frame
        if params['status'] == Status.skip:
            if in_vid.next():
                in_csv.next()
        
        # or load previous csv frame
        elif params['status'] == Status.back \
                and in_vid.at() > mark_in:
            # don't track before mark_in
            if in_vid.back():
                in_csv.back()
        
        # reset status
        params['status'] = Status.wait
    
    # clean up
    cv2.destroyAllWindows()
    
    
    ## write xml
    if write_xml:
        out_xml = XMLWriter(args[3])
        out_xml.declaration()
        doc = out_xml.start("TrainingSet")
        
        # source information
        out_xml.start("video", mark_in=str(mark_in), mark_out=str(mark_out))
        out_xml.data(os.path.basename(args[1]))
        out_xml.end()
        out_xml.element("csv", os.path.basename(args[2]))
        
        # training point data
        for lens in trainer_points:
            if lens == BuffSplitCap.right:
                out_xml.start("buttonside")
            elif lens == BuffSplitCap.left:
                out_xml.start("backside")
            else: # non dualmode
                out_xml.start("frames")
            
            for i in trainer_points[lens]:
                pos, row, markers = trainer_points[lens][i]
                x, y = pos
                
                # add 960 for rightside
                if lens == BuffSplitCap.right:
                    x =+ 960
                
                out_xml.start("frame", num=str(i))
                out_xml.element("plane", 
                                x=str(pos[0]), 
                                y=str(pos[1]))
                out_xml.element("vicon", 
                                x=str(row[0]), y=str(row[1]), z=str(row[2]))
                out_xml.element("visibility", 
                                visibleMax=str(markers[0]), 
                                visible=str(markers[1]))
                out_xml.end()
                
            out_xml.end() # frames
        
        # clean up
        out_xml.close(doc)
        
        print "Data was written."
    else:
        print "No data was written"
    
    print "\nDone."
    return 0

if __name__ == '__main__':
    exit(main(sys.argv))
