#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.3.18
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
#  ESC to quit
# 
# Note:
#   add 'mark in and out' values to args to skip 'Process 1'
#
#
# TODO:
#   - add key navigation to Process 2
#   - add zoomer to Process 2 (probs requires QT)
#   - resize video to screen size in Process 1
#   - 

import sys, cv2, numpy as np, time, os
from eagleeye import BuffCap, Memset, CVFlag, Key, EasyConfig, EasyArgs, marker_tool
from elementtree.SimpleXMLWriter import XMLWriter

def usage():
    print "usage: python2 trainer.py <video file> <csv file> <data out file> {<mark_in> <mark_out> | --clicks <num_clicks> | --config <file>}"

def main(sysargs):
    # settings
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.config, group="trainer")
    max_clicks = args.clicks or cfg.default_clicks
    font = CVFlag.FONT_HERSHEY_SIMPLEX
    window_name = "EagleEye Trainer"

    # grab marks from args
    if args.verifyLen(6):
        mark_in = args[4]
        mark_out = args[5]
        
        # test integer-ness
        try: int(mark_in) and int(mark_out)
        except: 
            usage()
            return 1
        
    elif args.verifyLen(4):
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
            params['count'] += 1
            params['pos'] = (x, y)
            params['status'] = 1
            
        # right click to skip
        elif event == cv2.EVENT_RBUTTONDOWN:
            params['status'] = 2

    # load video (again)
    in_vid = BuffCap(args[1], cfg.buffer_size)
    cv2.namedWindow(window_name)

    # status: 
    #   0 = exit (break loop)
    #   1 = left click (record pos)
    #   2 = right click or key (skip forward frame)
    #   3 = left key (skip back frame)
    #   5 = wait for input
    params = {'count':0, 'status': 2, 'pos': None}
    cv2.setMouseCallback(window_name, on_mouse, params)

    # load csv (with appropriate ratio)
    in_csv = Memset(args[2])
    in_csv.restrict()
    in_csv.setRatio(cropped_total)

    # prepare XML Writer
    out_xml = XMLWriter(args[3])
    out_xml.declaration()
    doc = out_xml.start("TrainingSet")
    out_xml.element("video", file=os.path.basename(args[1]))
    out_xml.element("csv", file=os.path.basename(args[2]))
    out_xml.start("frames")

    # status
    print ""
    print "Writing to:", args[3]
    print "Number of clicks at:", max_clicks
    print ""

    # grab clicks (Process 2)
    count = 0
    while in_vid.isOpened():
        count += 1
        
        # restrict to flash marks
        if count <= mark_in: 
            in_vid.next()
            continue
        if count > mark_out: 
            print "end of video."
            break
        
        # load frame
        frame = in_vid.frame()
        
        # add CSV data and show
        textrow = "{:.3f}".format(float(in_csv.row()[0]))
        for cell in in_csv.row()[2:]: 
            textrow += ", {:.4f}".format(float(cell))
        cv2.putText(frame, textrow,
                    (5,15), font, cfg.font_size, cfg.font_colour, cfg.font_thick, CVFlag.LINE_AA)
        
        textstatus = "{}/{} clicks".format(params['count'], max_clicks)
        cv2.putText(frame, textstatus,
                    (5,35), font, cfg.font_size, cfg.font_colour, cfg.font_thick, CVFlag.LINE_AA)
        
        cv2.imshow(window_name, frame)
        
        # pause for input
        while params['status'] >= 5:
            key = cv2.waitKey(10)
            if key == Key.esc:
                print "process aborted!\nData was still written."
                params['status'] = 0
            elif key == Key.right:
                params['status'] = 2
            elif key == Key.left:
                params['status'] = 3
            
        # catch exit status
        if params['status'] <= 0: break
        
        # print data
        if params['status'] == 1:
            # write data
            out_xml.start("frame", num=str(count))
            out_xml.element("plane", 
                            x=str(params['pos'][0]), 
                            y=str(params['pos'][1]))
            out_xml.element("vicon", 
                            x=str(in_csv.row()[2]), y=str(in_csv.row()[3]), z=str(in_csv.row()[4]))
            out_xml.end()
            print textstatus
        # else status == 2 (do nothing, next frame)
        
        # stop on max clicks
        if params['count'] == max_clicks:
            print "all clicks done"
            break
        
        # load next csv frame
        if params['status'] in (1, 2):
            if in_vid.next():
                in_csv.next()
        elif params['status'] == 3:
            if in_vid.back():
                in_csv.back()
        params['status'] = 5

    # clean up
    cv2.destroyAllWindows()
    out_xml.end()
    out_xml.close(doc)

    print "\nDone."
    return 0

if __name__ == '__main__':
    exit(main(sys.argv))
