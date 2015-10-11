#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders, Kin Kuen Liu
# version 0.1.7
#
# Compares any corresponding image points to reprojected points
# And calculate and display the reprojection error
# 

import sys, cv2, numpy as np, time, os
from eagleeye import BuffSplitCap, Xmlset, Xmltrainer, EasyArgs, EasyConfig, Key, marker_tool
from eagleeye.display_text import *
from math import sqrt
import csv

def usage():
    print "usage: python2 compare_trainer.py <video file> <mapper xml> <trainer xml> {<mark_in> <mark_out> | -config <file> | -video_export <file> | -compare_export <file>}"

def main(sysargs):
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.cfg, group="compare_trainer")
    font = cv2.FONT_HERSHEY_SIMPLEX
    window_name = "EagleEye Comparator"
    
    # grab marks from args
    if len(args) > 5:
        mark_in = args[4]
        mark_out = args[5]
        
        # test integer-ness
        try: int(mark_in) and int(mark_out)
        except: 
            usage()
            return 1
    
    # or grab them from a marker tool
    elif len(args) > 3:
        ret, mark_in, mark_out = marker_tool(args[1], 50, window_name)
        if not ret:
            print "Not processing - exiting."
            return 1
    else:
        usage()
        return 1
    
    # open inouts files
    vid = BuffSplitCap(args[1], buff_max=cfg.buffer_size)
    mapper_xml = Xmlset(args[2], offset=cfg.offset, offmode=Xmlset.__dict__[cfg.offset_mode])
    trainer_xml = Xmltrainer(args[3])
    reprojerror_list = {}     # list of reprojection error of all frames
    lastframe = False
    
    # reject mapper_xml if it doesn't contain the trainer_target
    if cfg.trainer_target not in mapper_xml.data(0):
        print "Mapping file must contain training target:", cfg.trainer_target
        print mapper_xml.data(0)
        return 1
    
    # sync the video and xml
    vid.restrict(mark_in, mark_out)
    cropped_total = mark_out - mark_in
    mapper_xml.setRatio(cropped_total)
    
    # status
    print "ratio at:", mapper_xml.ratio()
    print "offset by:", cfg.offset, "in", cfg.offset_mode, "mode"
    print ""
    
    # open export (if specified)
    if args.video_export:
        in_fps  = vid.get(cv2.CAP_PROP_FPS)
        in_size = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        out_vid = cv2.VideoWriter(args.video_export,
                                  cv2.VideoWriter_fourcc(*cfg.fourcc),
                                  in_fps, vid.shape[:2])
        print "exporting to:", args.video_export
    else:
        cv2.namedWindow(window_name)
        print "interactive mode"
    
    
    # main loop
    while vid.isOpened():
        frame = vid.frame()
        reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
        
        # export or navigate
        if args.video_export:
            sys.stdout.write("Reading Video Frame: {} / {}\r".format(vid.at(), mark_out))
            sys.stdout.flush()
            
            out_vid.write(frame)
            
            if vid.next():
                reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
                mapper_xml.next()
            else:
                calReprojList(reprojerror_list)
                print "\nend of video"
                break
        else:
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(0)
            showAll = False     # toggle to show all training points in one frame
                
            # controls
            if key == Key.esc:
                print "\nexiting."
                break
            elif key == Key.right:
                if vid.next():
                    mapper_xml.next()
                else:
                    if lastframe is False:
                        print "\nEnd of video"
                        calReprojList(reprojerror_list)
                    lastframe = True
                    
            elif key == Key.left:
                if vid.back():
                    mapper_xml.back()
            
            elif key == Key.enter:
                while True:
                    reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
                    cv2.imshow(window_name, frame)
                    
                    if vid.next():
                        mapper_xml.next()
                        frame = vid.frame()
                    
                    # break when over
                    else: break
                
                calReprojList(reprojerror_list)
                print "\nFast forwarded to end of video"
                
                if args.compare_export:
                    print "Output to file"
                    writeFile(args.compare_export, reprojerror_list)
                break
            
            elif key == Key.space:
                ''' TODO: display all training points, may be abandoned
                problems:
                frame is not refreshed after imshow
                if showAll is False:
                    displayTrainPts(frame, mark_in, mark_out, trainer_xml, cfg)
                    #
                    #except:
                    #    print "Error in displaying training points. Exiting..."
                    #    return 1
                    #
                    
                    showAll = True
                else:
                    frame, reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
                    showAll = False
                '''
                pass
    
    # clean up
    vid.release()
    if args.video_export:
        out_vid.release()
    else:
        cv2.destroyAllWindows()
        
    return 0


# display original trainer point
def compareReproj(cvframe, vidframe_no, mapper_xml, trainer_xml, reprojerror_list, cfg):
    
    xmlframe_no = mapper_xml.at()
    sys.stdout.write("Reading Video Frame: {}".format(vidframe_no) + " | XML Frame number: {}\r".format(xmlframe_no))
    sys.stdout.flush()
    
    trainer_object = mapper_xml.data(xmlframe_no)[cfg.trainer_target]
    
    # Prepare Repojected Point
    pt1 = (int(float(trainer_object['box']['x'])), 
            int(float(trainer_object['box']['y'])))
    
    pt2 = (pt1[0] + int(float(trainer_object['box']['width'])), 
            pt1[1] + int(float(trainer_object['box']['height'])))
    
    centre = (int(float(trainer_object['centre']['x'])), 
                int(float(trainer_object['centre']['y'])))
    
    visible = int(trainer_object['visibility']['visible'])
    max_visible =  int(trainer_object['visibility']['visibleMax'])
    
    
    # Render Reprojected Point
    cv2.rectangle(cvframe, pt1, pt2, cfg.mapper_colour, 1)
    cv2.circle(cvframe, centre, 1, cfg.mapper_colour, 2)
    
    # Display Object Info
    frameObj_Txt = "Frame: {} | Trained Object: {}".format(vidframe_no, cfg.trainer_target)
    displayText(cvframe, frameObj_Txt, top=True)
    
    reprojCentroid_txt = "Reprojected Centroid - x: {}, y: {}".format(centre[0],centre[1])
    displayText(cvframe, reprojCentroid_txt)
    
    visibility_txt = "Visible: {} , Max Visible: {}".format(visible, max_visible)
    displayText(cvframe, visibility_txt)
    
    dataText = " - Good data!!"
    dataText_colour = (0, 255, 0) # green
    if visible < cfg.min_reflectors:           # for when there isn't a matching trainer
        dataText = " - Bad data!!"
        dataText_colour = (0, 0, 255) # red
        if cfg.ignore_baddata:
            dataText += " Ignored."
    
    # Get trainer point if it exists at current frame
    vicon_txt = "VICON - x: ?, y: ?, z: ?"
    trainer_txt = "Trained Point: x: ?, y: ?"
    reprojErr_txt = "Reprojection Error: No Data"
    
    if vidframe_no in trainer_xml.data():
        trainer_frame = trainer_xml.data()[vidframe_no]
    
        vicon_txt = "VICON - x: {:.4f}, y: {:.4f}, z: {:.4f}".format(
                            float(trainer_frame["vicon"]["x"]),
                            float(trainer_frame["vicon"]["y"]),
                            float(trainer_frame["vicon"]["z"]))
        trainer_txt = "Trained Point: x: {}, y: {}".format(
                            int(float(trainer_frame["plane"]["x"])),
                            int(float(trainer_frame["plane"]["y"])))
        
        # visualise trainer point
        trainer_pt = (int(float(trainer_frame["plane"]["x"])),
                        int(float(trainer_frame["plane"]["y"])))
        cv2.circle(cvframe, trainer_pt, 1, cfg.trainer_colour, 2)

        # Calculate Reprojection Error at this frame
        # Still display bad data reprojection error but not used in calculation of mean
        reprojErr = calReprojError(centre, trainer_pt)
        reprojErr_txt = "Reprojection Error: {} pixels".format(str(reprojErr))
        
        if cfg.ignore_baddata:
            if visible >= cfg.min_reflectors:
                reprojerror_list.update({vidframe_no: {
                                            "rms": reprojErr,
                                            "x1": trainer_pt[0],
                                            "y1": trainer_pt[1],
                                            "x2": pt1[0],
                                            "y2": pt1[1]}})
    
    displayText(cvframe, dataText, endl=True, colour=dataText_colour)
    displayText(cvframe, trainer_txt)
    displayText(cvframe, vicon_txt)
    displayText(cvframe, reprojErr_txt)
    
    return reprojerror_list


def writeFile(filepath, reprojList):
    with open(filepath, "wb") as csvFile:
        c = csv.writer(csvFile)
        for data in reprojList:
            c.writerow([data,
                        reprojList[data]["x1"],
                        reprojList[data]["x2"],
                        reprojList[data]["y1"],
                        reprojList[data]["y2"],
                        reprojList[data]["rms"]])


# calculate the difference between 2 points (manually picked & reprojected)
def calReprojError(img_pt, reproj_pt):
    if img_pt and reproj_pt is not None:
        if not(img_pt < 0) and not(reproj_pt < 0):
            return cv2.norm(img_pt, reproj_pt, cv2.NORM_L2) # Euclidean distance
    return -1.0


def calReprojList(reprojerror_list):
    # print reprojection error at end of vid
    print "\n"
    total_error = 0.0
    error_sq = 0.0
    if len(reprojerror_list) > 0:
        for frm in reprojerror_list:
            total_error += float(reprojerror_list[frm]["rms"]) # I hope this is Euclidean and not "RMS". RMS of a single number is still the single number!
            error_sq += (float(reprojerror_list[frm]["rms"]))*(float(reprojerror_list[frm]["rms"])) # Each error squared before accumulating.          
        mean = total_error / len(reprojerror_list) # = average
        rootMS = sqrt(error_sq / len(reprojerror_list)) # RMS is sqrt((a^2+b^2...N^2)/N)
        print "Re-projection Error:\n"
        print "\tMean:\t{} pixels".format(mean)
        print "\tRMS:\t{} pixels\n".format(rootMS)
    else:
        print "Re-projection Error: No Data"


# display all training points used
def displayTrainPts(frame, mark_in, mark_out, trainerxml, cfg):
    for i in range(mark_in +1, mark_out):
        if i in trainerxml.data():
            
            train_pt = trainerxml.data()[i]
            trainer_pt = (int(float(train_pt["plane"]["x"])),
                            int(float(train_pt["plane"]["y"])))
            # visualise trainer point
            cv2.circle(frame, trainer_pt, 1, cfg.trainer_colour, 2)
            

if __name__ == '__main__':
    exit(main(sys.argv))
