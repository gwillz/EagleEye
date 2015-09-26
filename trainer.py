#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders
# version 0.3.28
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
from eagleeye import BuffCap, Memset, Key, EasyConfig, EasyArgs, marker_tool
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
    trainer_points = {}
    write_xml = False
    lastframe = False
    qMode = cfg.quality_mode
    quality_threshold = cfg.quality_threshold
    min_reflectors = cfg.min_reflectors
    # ensure minimum is 4 as required by VICON system
    if (min_reflectors < 4):
        min_reflectors = 4
    qModeText = ""
    # Minimum points of reflectors, must be at least 4
    if qMode == 1:      qModeText = "min of {} visible".format(min_reflectors)
    # Quality Threshold (No. of visible reflectors / Max reflectors on object)
    elif qMode == 2:    qModeText = "threshold of {}".format(quality_threshold)
    # 1 or 2
    elif qMode == 3:    qModeText = "min of {} visible & threshold of {}".format(min_reflectors, quality_threshold)
    # Both 1 & 2
    elif qMode == 4:    qModeText = "min of {} visible & threshold of {}".format(min_reflectors, quality_threshold)
    else:               qModeText = "No quality control mode has been set."
    print "Trainer Quality Mode: {}. | Ignore Negative xyz: {}".format(qModeText, cfg.check_negatives)
    
        
    # load video (again)
    in_vid = BuffCap(args[1], cfg.buffer_size)
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
    
    # grab clicks (Process 2)
    while in_vid.isOpened():
        # restrict to flash marks
        if in_vid.at() < mark_in:
            in_vid.next()
            continue
        if in_vid.at() >= (mark_in + cropped_total) or in_vid.at() >= mark_out:
            write_xml = True
            print "\nend of video: {}/{}".format(in_vid.at(), mark_out -1)
            break

        sys.stdout.write("Current Video Frame: {} / {}".format(in_vid.at(), mark_out -1)
                 + " | Clicks {} / {}\r".format(len(trainer_points), max_clicks))
        sys.stdout.flush()
        
        # load frame
        frame = in_vid.frame()
        
        # prepare CSV data, click data
        textOffset = (5, 0)
        textrow = "{:.3f}".format(float(in_csv.row()[0]))

        vicon_x = float(in_csv.row()[2])
        vicon_y = float(in_csv.row()[3])
        vicon_z = float(in_csv.row()[4])
        pitch = float(in_csv.row()[5])
        row = float(in_csv.row()[6])
        yaw = float(in_csv.row()[7])

        # TODO: CHECK PITCH ROw YAw
        textrow = "VICON - x: {:.4f} y: {:.4f} z: {:.4f} | pitch: {:.4f} row: {:.4f} yaw: {:.4f}".format(vicon_x, vicon_y, vicon_z, pitch, row, yaw)
        textstatus = "{}/{} clicks".format(len(trainer_points), max_clicks)
        textstatus_size, baseline = cv2.getTextSize(textstatus, font, cfg.font_scale, cfg.font_thick)

        # data quality status
        dataStatus = ""
        dataStatus_colour = (255,255,255)
        visible = int(in_csv.row()[9])
        max_visible = int(in_csv.row()[8])
        quality = float(visible) / float(max_visible)

        if(cfg.check_negatives == "on"):
            if(vicon_x < 0 or vicon_y < 0 or vicon_z < 0):
                dataStatus += " - Bad data!!"
                dataStatus_colour = (0, 0, 255) # red

        dataStatus = " - Good data!!"
        dataStatus_colour = (0, 255, 0) # green
        # Minimum points of reflectors, must be at least 4
        if qMode == 1:
            if (visible < min_reflectors):
                dataStatus = " - Bad data!!"
                dataStatus_colour = (0, 0, 255) # red
        # Quality Threshold (No. of visible reflectors / Max reflectors on object)
        elif qMode == 2:
            if (quality < quality_threshold):
                dataStatus = " - Bad data!!"
                dataStatus_colour = (0, 0, 255) # red
        # 1 or 2
        elif qMode == 3:
            if ((visible < min_reflectors) or (quality < quality_threshold)):
                dataStatus = " - Bad data!!"
                dataStatus_colour = (0, 0, 255) # red
        # Both 1 & 2
        elif qMode == 4:
            if ((visible < min_reflectors) and (quality < quality_threshold)):
                dataStatus = " - Bad data!!"
                dataStatus_colour = (0, 0, 255) # red
        else:
            dataStatus = " - No quality control."
            dataStatus_colour = (0, 0, 0)
        
        # draw the trainer dot (if applicable)
        if in_vid.at() in trainer_points:
            cv2.circle(frame, trainer_points[in_vid.at()][0], 1, cfg.font_colour, 2)
            cv2.circle(frame, trainer_points[in_vid.at()][0], 15, cfg.font_colour, 1)
            
        # draw text and show
        frame, textOffset, _toptextSize = displayText(frame, textrow, textOffset, cfg)
        frame, _textOffset, _textSize = displayText(frame, textstatus, textOffset, cfg)
        frame, dataStatus_offset, _textSize = displayText(frame, dataStatus, (_textSize[0], textOffset[1]), cfg, dataStatus_colour)
            
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
            
        # catch exit status
        if params['status'] == Status.stop:
            print "\nprocess aborted!"
            break
        
        # write data
        if params['status'] == Status.record:
            trainer_points[in_vid.at()] = (params['pos'], in_csv.row()[2:5], in_csv.row()[8:10], quality)
            params['status'] = Status.skip
        
        # or remove it
        elif params['status'] == Status.remove:
            if (trainer_points.has_key(in_vid.at()) is True):
                del trainer_points[in_vid.at()]
                print "\nremoved dot"
        
        # stop on max clicks - end condition 2
        if len(trainer_points) == max_clicks:
            print "\nall clicks done"
            trainer_points[in_vid.at()] = (params['pos'], in_csv.row()[2:5], in_csv.row()[8:10], quality)
            write_xml = True
            break
        
        # load next csv frame
        if params['status'] == Status.skip:
            if in_vid.next():
                in_csv.next()
        elif params['status'] == Status.back:
            if(in_vid.at() - 1 != mark_in):    # prevents going back to the frame with first flash (mark_in)
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
        out_xml.start("frames")
        for i in trainer_points:
            pos, data, visibility, quality = trainer_points[i]
            
            out_xml.start("frame", num=str(i), maxVisible=str(visibility[0]), visible=str(visibility[1]), quality=str(quality))
            out_xml.element("plane", 
                            x=str(pos[0]), 
                            y=str(pos[1]))
            out_xml.element("vicon", 
                            x=str(data[0]), y=str(data[1]), z=str(data[2]))
            out_xml.end()
        
        # clean up
        out_xml.end()
        out_xml.close(doc)
        
        print "Data was written."
    else:
        print "No data was written"
    
    print "\nDone."
    return 0

# calculate height offset of a line of text and display on top left
def displayText(frame, text, offset, cfg, customColour=None):
    if(customColour is None):
        customColour = cfg.font_colour

    font = cv2.FONT_HERSHEY_SIMPLEX
    y_extraOffset = 2
    x_offset = 5
    y_offset = 0
    if(len(offset) == 2):
        x_offset = offset[0]
        y_offset = offset[1]

    textSize, baseLine = cv2.getTextSize(text, font, cfg.font_scale, cfg.font_thick)
    y_offset += textSize[1] + baseLine + y_extraOffset
    cv2.putText(frame, text,
        (x_offset, y_offset), font, cfg.font_scale, customColour, cfg.font_thick, cv2.LINE_AA)
    return frame, (x_offset, y_offset), textSize


if __name__ == '__main__':
    exit(main(sys.argv))
