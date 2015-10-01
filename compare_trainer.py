#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders, Kin Kuen Liu
# version 0.0.1
#
# Compares any corresponding image points to reprojected points
# And calculate and display the reprojection error
# 

import sys, cv2, numpy as np, time, os
from eagleeye import BuffCap, Xmlset, Xmltrainer, Xmlframe, EasyArgs, EasyConfig, Key, marker_tool
from math import sqrt
import csv

def usage():
    print "usage: python2 compare_trainer.py <video file> <mapper xml> <trainer xml> {<mark_in> <mark_out> | -config <file> | -export <file>}"

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
    
    # open video files
    vid = BuffCap(args[1], buff_max=cfg.buffer_size)
    mapper_xml = Xmlframe(args[2])
    trainer_xml = Xmltrainer(args[3])
    reprojerror_list = {}     # list of reprojection error of all frames
    lastframe = False
    
    cropped_total = mark_out - mark_in
    mapper_xml.setRatio(cropped_total)
    print 'ratio at:', mapper_xml._ratio, "\n"
    
    # open export (if specified)
    if args.export:
        in_fps  = vid._cap.get(cv2.CAP_PROP_FPS)
        in_size = (int(vid._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(vid._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        out_vid = cv2.VideoWriter(args.export,
                                  cv2.VideoWriter_fourcc(*cfg.fourcc),
                                  in_fps, vid.shape[:2])
    else:
        cv2.namedWindow(window_name)
    
    while vid.isOpened():
        # restrict to flash marks
        if vid.at() <= mark_in: 
            vid.next()
            continue
        
        frame = vid.frame()
        frame, reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
        
        # elementtreet or navigate
        if args.export:
            sys.stdout.write("Reading Video Frame: {} / {}\r".format(vid.at(), mark_out))
            sys.stdout.flush()
            
            out_vid.write(frame)
            
            if(vid.at() < mark_out -1):
                if vid.next():
                    frame, reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
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
                return 1
            elif key == Key.right:
                if(vid.at() < mark_out -1):
                    if vid.next():
                        mapper_xml.next()
                else:
                    if lastframe is False:
                        print "\nEnd of video"
                        calReprojList(reprojerror_list)
                    lastframe = True
            elif key == Key.left:
                if(vid.at() - 1 != mark_in):
                    if vid.back():
                        mapper_xml.back()
            elif key == Key.enter:
                while (vid.at() < mark_out):
                    if (vid.at() > mark_out -1):
                        break

                    frame, reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
                    cv2.imshow(window_name, frame)
                    if vid.next():
                        mapper_xml.next()
                        frame = vid.frame()
                
                calReprojList(reprojerror_list)
                print "\nFast forwarded to end of video"
                print "Output to file"
                writeFile("C:\\Anaconda\\awork\\wizardtool\\data\\compare_frames.csv", reprojerror_list)
                break
                #return 1
            elif key == Key.space:
                ''' TODO: display all training points, may be abandoned
                problems:
                frame is not refreshed after imshow
                if showAll is False:
                    frame = displayTrainPts(frame, mark_in, mark_out, trainer_xml, cfg)
                    showAll = True
                else:
                    frame, reprojerror_list = compareReproj(frame, vid.at(), mapper_xml, trainer_xml, reprojerror_list, cfg)
                    showAll = False
                '''
    
    # clean up
    vid.release()
    if args.export:
        out_vid.release()
    else:
        cv2.destroyAllWindows()
        
    return 0

# Display 
def compareReproj(cvframe, vidframe_no, mapper_xml, trainer_xml, reprojerror_list, cfg):

    min_reflectors = int(cfg.min_reflectors)
    if min_reflectors < 4:
        min_reflectors = 4
    
    xmlframe_no = 0
    if len(mapper_xml.data().keys()) > 0:
        xmlframe_no = mapper_xml.data().keys()[0] # get first key, should rewrite mapper xml reader(?)
    else:
        print "Corresponding frame is missing in the mapping XML at vidio frame: {}".format(vidframe_no)
        return cvframe

    sys.stdout.write("Reading Video Frame: {}".format(vidframe_no) + " | XML Frame number: {}\r".format(xmlframe_no))
    sys.stdout.flush()
    objs = mapper_xml.data()[xmlframe_no]
    '''
    print "ALL OBJECTS", objs
    print "ALL OBJECTS KEY", xmlframe_no
    '''
    for obj in objs:

        '''
        print "Current Object is:", obj
        print "Object info is:",  mapper_xml.data()[xmlframe_no][obj]
        '''
        
        textOffset = (5, 0)

        # Prepare Repojected Point
        pt1 = (int(float(mapper_xml.data()[xmlframe_no][obj]['box']['x'])), 
                int(float(mapper_xml.data()[xmlframe_no][obj]['box']['y'])))
        pt2 = (pt1[0] + int(float(mapper_xml.data()[xmlframe_no][obj]['box']['width'])), 
                pt1[1] + int(float(mapper_xml.data()[xmlframe_no][obj]['box']['height'])))
        centre = (int(float(mapper_xml.data()[xmlframe_no][obj]['centre']['x'])), 
                int(float(mapper_xml.data()[xmlframe_no][obj]['centre']['y'])))
        visible = int(mapper_xml.data()[xmlframe_no][obj]['visibility']['visible'])
        max_visible =  int(mapper_xml.data()[xmlframe_no][obj]['visibility']['visibleMax'])
        
        # Render Reprojected Point
        cv2.rectangle(cvframe, pt1, pt2, cfg.mapper_colour, 1)
        cv2.circle(cvframe, centre, 1, cfg.mapper_colour, 2)

        # Display Object Info
        frameObj_Txt = "Frame: {} | Trained Object: {}".format(vidframe_no, str(obj))
        cvframe, textOffset, _topTextSize= displayText(cvframe, frameObj_Txt, textOffset, cfg)
        
        reprojCentroid_txt = "Reprojected Centroid - x: {}, y: {}".format(centre[0],centre[1])
        cvframe, textOffset, _topTextSize = displayText(cvframe, reprojCentroid_txt, textOffset, cfg)

        visibility_txt = "Visible: {} , Max Visible: {}".format(visible, max_visible)
        cvframe, _textOffset, _textSize = displayText(cvframe, visibility_txt, textOffset, cfg)

        dataText = " - Good data!!"
        dataText_colour = (0, 255, 0) # green
        if(visible < min_reflectors):           # for when there isn't a matching trainer
            dataText = " - Bad data!!"
            if(cfg.ignore_baddata == True):
                dataText += " Ignored."
            dataText_colour = (0, 0, 255) # red
        
        # Get trainer point if it exists at current frame
        vicon_txt = "VICON - x:{} y:{} z:{}".format("?", "?", "?")
        trainer_txt = "Trained Point: x:{} y: {}".format("?", "?")
        reprojErr_txt = "Reprojection Error: {}".format("No Data")
        trainer_frame = trainer_xml.data(str(vidframe_no))

        if obj == cfg.object_target:
            if trainer_frame is not None:
                trainer_pt = (int(float(trainer_frame["plane"]["x"])),
                              int(float(trainer_frame["plane"]["y"])))
                trainer_txt = "Trained Point: x:{} y: {}".format(int(float(trainer_frame["plane"]["x"])),
                                                                  int(float(trainer_frame["plane"]["y"])))
                # visualise trainer point
                cv2.circle(cvframe, trainer_pt, 1, cfg.trainer_colour, 2)

                # Calculate Reprojection Error at this frame
                # Still display bad data reprojection error but not used in calculation of mean
                reprojErr = calReprojError(centre, trainer_pt)
                reprojErr_txt = "Reprojection Error: {} pixels".format(str(reprojErr))
                if(cfg.ignore_baddata == True):
                    if(visible >= min_reflectors):
                        reprojerror_list.update({vidframe_no: {"rms": reprojErr,
                                                    "x1": trainer_pt[0],
                                                    "y1": trainer_pt[1],
                                                    "x2": pt1[0],
                                                    "y2": pt1[1]}})
                
                vicon_txt = "VICON - x:{} y:{} z:{}".format(float(trainer_frame["vicon"]["x"]),
                                                                float(trainer_frame["vicon"]["y"]),
                                                                float(trainer_frame["vicon"]["z"]))

        
        cvframe, textOffset, _textSize = displayText(cvframe, dataText, (_textSize[0], textOffset[1]), cfg, customColour=dataText_colour)
        cvframe, textOffset, _textSize = displayText(cvframe, trainer_txt, _textOffset, cfg)
        cvframe, textOffset, _textSize = displayText(cvframe, vicon_txt, textOffset, cfg)
        cvframe, textOffset, _textSize = displayText(cvframe, reprojErr_txt, textOffset, cfg)


    return cvframe, reprojerror_list

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
    if (len(reprojerror_list) > 0):
        for frm in reprojerror_list:
            total_error += float(reprojerror_list[frm]["rms"])
            
        arth_mean = total_error / len(reprojerror_list)
        rms = sqrt(arth_mean)      # according to opencv calibrateCamera2
        
        print "List of Reprojection Error:"
        for reproj in reprojerror_list:
            print "Frame: {} | Reprojection Error: {}".format(reproj, reprojerror_list[reproj]["rms"])
        print "\n"
        print "Number of matched training points: {}".format(len(reprojerror_list))
        print "RMS: {} pixels".format(rms)
        print "Arithmetical mean: {} pixels".format(arth_mean)
        print ""
    else:
        print "Reprojection Error: No Data"

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

# display all training points used
def displayTrainPts(frame, mark_in, mark_out, trainerxml, cfg):
    for i in range(mark_in +1, mark_out):
        train_pt = trainerxml.data(str(i))
        if train_pt is not None:
            try:
                trainer_pt = (int(float(train_pt["plane"]["x"])),
                              int(float(train_pt["plane"]["y"])))
                # visualise trainer point
                cv2.circle(frame, trainer_pt, 1, cfg.trainer_colour, 2)
            except:
                print "Error in displaying training points. Exiting..."
                return 1
            
    return frame

if __name__ == '__main__':
    exit(main(sys.argv))
