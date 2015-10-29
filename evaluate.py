#!/usr/bin/env python2
# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# 
# Gwilyn Saunders, Kin Kuen Liu
# version 0.1.0
#
# Compares mapped centroid to annotated centroid produced by annotation tool
# And calculate reprojction error frame by frame
#

import sys, os, cv2
import csv
import numpy as np
from eagleeye import Xmlset, EasyArgs, EasyConfig
from elementtree.SimpleXMLWriter import XMLWriter
from matplotlib import pyplot as plt

def usage():
    print "usage: python2 evaluate.py <mapper xml> <annotated xml> <output file> { <mark_in> <mark_out> }"

def main(sysargs):
    args = EasyArgs(sysargs)
    cfg = EasyConfig(args.cfg, group="evaluate")
    window_name = "EagleEye Evaluation Tool"

    # check output path
    path = ""
    if args[3] == "":
        return 1
    else:
        path = args[3]
    
    # grab marks from args
    if len(args) > 4:
        mark_in = args[4]
        mark_out = args[5]
        
    # test integer-ness
    try: int(mark_in) and int(mark_out)
    except: 
        usage()
        return 1

    # open input files
    mapper_xml = Xmlset(args[1], readmode="mapper")
    annotated_xml = Xmlset(args[2], readmode="annotated")

    # status
    print "Evaluating Mapper: {} | Annoated: {}".format(os.path.basename(args[1]), os.path.basename(args[2]))
    print ""

    if(mapper_xml.total != annotated_xml.total):
        print "Warning: Mismatched size of Mapper and Annotated: Mapper {} | Annotated{}".format(mapper_xml.total, annotated_xml.total)

    # Compare frames, start from the frame after 1st flash
    frameStart = mark_in +1
    frameEnd = mark_out -1

    # list of compared frames for export
    compare_frames = {}

    # vars for plots
    obj_plotdata = {}   # id should be based on object, then frame number and its projection error

    print "Number of frames to compare {} | From Frame no. {} - {}".format((frameEnd) - (frameStart) + 1, frameStart, frameEnd)

    for f in range(mark_in+1, mark_out):
        sys.stdout.write("Reading Mapper Frame: {}".format(f) + " | XML Frame number: {}\r".format(f))
        sys.stdout.flush()
        
        # check if frame exists in xml, if not skip to next
        if (mapper_xml.data(f) == None):
            continue
        if (annotated_xml.data(f) == None):
            continue
        
        mapper_data = mapper_xml.data(f)
        annotated_data = annotated_xml.data(f)

        # initialise frame
        compare_frames[f] = {}

        for obj in mapper_data.keys():
            if obj not in obj_plotdata.keys():
                obj_plotdata[obj] = {}  # initialise obj in dictionary
            
            if obj in annotated_data.keys():
                # check sides
                if mapper_data[obj]["lens"] == mapper_data[obj]["lens"]:
                    mapper_x = int(float(mapper_data[obj]["centre"]["x"]))
                    mapper_y = int(float(mapper_data[obj]["centre"]["y"]))

                    annotated_x = int(float(annotated_data[obj]["centre"]["x"]))
                    annotated_y = int(float(annotated_data[obj]["centre"]["y"]))

                    mapper_centroid = (mapper_x, mapper_y)
                    annotated_centroid = (annotated_x, annotated_y)
                    
                    reproj_err = calReprojError(mapper_centroid, annotated_centroid)
                    
                    # for export
                    compare_frames[f][obj] = {}     # initialise compared object 
                    compare_frames[f][obj]["lens"] = mapper_data[obj]["lens"]
                    compare_frames[f][obj]["map_x"] = mapper_x
                    compare_frames[f][obj]["map_y"] = mapper_y
                    compare_frames[f][obj]["ann_x"] = annotated_x
                    compare_frames[f][obj]["ann_y"] = annotated_y
                    compare_frames[f][obj]["err"] = float(reproj_err)
                    
                    obj_plotdata[obj].update({f: reproj_err})
                    

    print "\n\nFound {} frames with matched objects".format(len(compare_frames))
    print "Mean Error (Full Set): {} \n".format(calMean(compare_frames))
    
    if path != "":
        if path.find(".xml") is not -1:
            print "\nOutputing comparion in xml to {}".format(path)
            writeXML(compare_frames, path, args)
        elif cfg.outputformat == "csv":
            path = path.replace(".xml",".csv")
            print "Outputing comparison in csv to {}".format(path)
            writeCSV(compare_frames, path)
        else:
            print "\nUnkown file format, please specify file extension as .xml or .csv"

    else:
        print "\nNo output path has been specified"


    # plot!
    if cfg.plot:
        print "\nPlotting frame by frame comparison..."
        plot("Difference between Annotated Centroid and Mapped Centroid (Ground Truth) \n {}".format(os.path.basename(path)), dict_data=obj_plotdata) 
    

# calculate the difference between 2 points
def calReprojError(img_pt, reproj_pt):
    if img_pt and reproj_pt is not None:
        if not(img_pt < 0) and not(reproj_pt < 0):
            return cv2.norm(img_pt, reproj_pt, cv2.NORM_L2) # Euclidean distance
    return -1.0

def calMean(frames):
    total_error = 0.0
    size = 0
    for f in frames.keys():
        for obj in frames[f]:
            total_error += float(frames[f][obj]["err"])
            size += 1
    
    return float(total_error)/float(size)

# write to XML
def writeXML(frames, path, args):
    out_xml = XMLWriter(path)
    out_xml.declaration()
    doc = out_xml.start("AnnotationEvaluation")
    
    # source information
    out_xml.element("video", mark_in=str(args[4]), mark_out=str(args[5]))
    out_xml.element("mapper", os.path.basename(args[1]))
    out_xml.element("annotation", os.path.basename(args[2]))
    out_xml.element("comparison", mean_err=str(calMean(frames)))
    # compared points
    out_xml.start("frames", total=str((args[5]-1) - (args[4]+1)+1), compared=str(len(frames)))
    for f in frames.keys():
        out_xml.start("frame", num=str(f))
        for key in frames[f]:
            out_xml.start("object", lens=str(frames[f][key]["lens"]), name=key, err=str(frames[f][key]["err"])) # TODO: if lens in string form is preferred
            out_xml.element("annotatedCentroid", x=str(frames[f][key]["ann_x"]), y=str(frames[f][key]["ann_y"]))
            out_xml.element("mappedCentroid", x=str(frames[f][key]["map_x"]), y=str(frames[f][key]["map_y"]))
            out_xml.end() # object
        out_xml.end() # frames
    
    # clean up
    out_xml.close(doc)
        
# write to csv
def writeCSV(frames, path):
    with open(path, "wb") as csvFile:
        c = csv.writer(csvFile)
        for f in frames.keys():
            for key in frames[f]:
                c.writerow([f,                              # frame number
                            frames[f][key]["map_x"],        # mapped centroid x
                            frames[f][key]["map_y"],        # mapped centroid y
                            frames[f][key]["ann_x"],        # annotated centroid x
                            frames[f][key]["ann_y"],        # annotated centroid y
                            frames[f][key]["lens"],         # lens (based on Theta class) TODO: if lens in string form is preferred
                            frames[f][key]["err"]])         # reprojection error


def plot(title, xlabel="Frames", ylabel="Euclidean Distance \n (Pixels)", dict_data={}, width=18, height=9):
    if len(dict_data) > 0:
        fig = plt.figure(figsize=(width, height))
        fig.suptitle(title, fontsize=18)             # set overall title

        # Base plot to contian subplots and common x,y labels for subplots
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xticks([0])
        ax.set_yticks([0])
        ax.set_xlabel(xlabel, fontsize=16)
        ax.set_ylabel(ylabel, fontsize=16)

        # Strip base plot axes, base plot won't be visible when exported
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        
        # plots in this method cannot be contained by a base plot initialised above
        #fig, axs = plt.subplots(len(subplot_titles), 1, figsize=(width, height), sharex=True) # sizes in inches

        plot_index = 1
        for obj, data in sorted(dict_data.items()):
            frames = data.keys()
            framesErr = data.values()
            # TODO: seems to be plotting fine, must re-confirm if it's plotting the correct data !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            obj_plot = fig.add_subplot(len(dict_data), 1, plot_index)
            obj_plot.plot(frames, framesErr)
            obj_plot.grid()
            obj_plot.set_title(obj)
            obj_plot.set_ylim(0, max(framesErr)+5)
            obj_plot.set_xlim(min(frames)-5 if min(frames) > 5 else 0,max(frames)+5)
            obj_plot.set_xticks(np.arange(start=min(frames), stop=max(frames), step=10))
            plot_index += 1

        fig.tight_layout(rect=[0, 0.03, 1, 0.925])  # packs the plots neatly
        plt.show()
        plt.close(fig)  # clean memory
    else:
        print "No objects to plot"

if __name__ == '__main__':
    exit(main(sys.argv))
