#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.4.28
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
    font = cv2.FONT_HERSHEY_SIMPLEX
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
    trainer_points = {BuffSplitCap.left:{}, BuffSplitCap.right:{}}
    write_xml = False
    
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
    
    # TODO: frame_no is not accurate. But it's not used.
    
    # grab clicks (Process 2)   
    frame_no = 0
    lens = BuffSplitCap.left
    while in_vid.isOpened():
        # restrict to flash marks
        if frame_no <= mark_in:
            frame_no += 1
            in_vid.next()
            #print "Frame {} . {}".format(frame_no, mark_in)
            continue
        if frame_no >= mark_out:
            write_xml = True
            print "end of video: {}/{}".format(frame_no, cropped_total)
            break
        
        # load frame
        frame = in_vid.frame(side=lens)
        
        # prepare CSV data, click data
        textrow = "{:.3f}".format(float(in_csv.row()[0]))
        for cell in in_csv.row()[2:8]:
            textrow += ", {:.4f}".format(float(cell))
        textstatus = "{}/{} clicks".format(len(trainer_points[lens]), max_clicks)
        textstatus += " - back side" if lens == BuffSplitCap.left else " - button side"
        
        # data quality status
        quality = float(in_csv.row()[9]) / float(in_csv.row()[8])
        if quality > cfg.quality_threshold:
            textstatus += " - Good data"
        else:
            textstatus += " - Bad data!!"
        
        # draw the trainer dot (if applicable)
        if frame_no in trainer_points[lens]:
            cv2.circle(frame, trainer_points[lens][frame_no][0], 1, cfg.font_colour, 2)
            cv2.circle(frame, trainer_points[lens][frame_no][0], 15, cfg.font_colour, 1)
            
        # draw text and show
        cv2.putText(frame, textrow,
                    (5,15), font, cfg.font_size, cfg.font_colour, cfg.font_thick, cv2.LINE_AA)
        cv2.putText(frame, textstatus,
                    (5,35), font, cfg.font_size, cfg.font_colour, cfg.font_thick, cv2.LINE_AA)
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
            elif Key.char(key, '1'):
                params['status'] = Status.still
                lens = BuffSplitCap.left
            elif Key.char(key, '2'):
                params['status'] = Status.still
                lens = BuffSplitCap.right
            
        # catch exit status
        if params['status'] == Status.stop:
            print "process aborted!"
            break
        
        # write data
        if params['status'] == Status.record \
                and len(trainer_points[lens]) != max_clicks:
            print textstatus
            trainer_points[lens][frame_no] = (params['pos'], in_csv.row()[2:5], quality)
            params['status'] = Status.skip
        
        # or remove it
        elif params['status'] == Status.remove:
            print "removed dot"
            del trainer_points[lens][frame_no]
            params['status'] = Status.still
        
        # stop on max clicks - end condition 2
        if len(trainer_points[BuffSplitCap.left]) == max_clicks \
                and len(trainer_points[BuffSplitCap.right]) == max_clicks:
            print "all clicks done"
            
            # why record here? how can we know this a good training point?
            trainer_points[lens][frame_no] = (params['pos'], in_csv.row()[2:5], quality)
            write_xml = True
            break
        
        # load next csv frame
        if params['status'] == Status.skip:
            if in_vid.next():
                in_csv.next()
                frame_no += 1
        elif params['status'] == Status.back:
            if in_vid.back():
                in_csv.back()
                frame_no -= 1
        
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
            out_xml.start("buttonside" if lens == BuffSplitCap.left else "backside")
            out_xml.start("frames")
            
            for i in trainer_points[lens]:
                pos, row, quality = trainer_points[lens][i]
                
                out_xml.start("frame", num=str(i), quality=str(quality))
                out_xml.element("plane", 
                                x=str(pos[0]), 
                                y=str(pos[1]))
                out_xml.element("vicon", 
                                x=str(row[0]), y=str(row[1]), z=str(row[2]))
                out_xml.end()
                
            out_xml.end() # frames
            out_xml.end() # buttonside/backside
        
        # clean up
        out_xml.close(doc)
        
        print "Data was written."
    else:
        print "No data was written"
    
    print "\nDone."
    return 0

if __name__ == '__main__':
    exit(main(sys.argv))
