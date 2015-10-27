from PIL import Image, ImageTk
import cv2
import numpy as np
import eagleeye as ee
from numpy import *
import pickle
import time
import sys
import os
from glob import glob
import itertools as it
import PyQt4
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QMessageBox
from PyQt4.Qt import *
import xml.etree.ElementTree as ET
import xml.dom.minidom
import StringIO
import tkFileDialog
from tkFileDialog import *

#marks_in : begin frame of the flash, marks_out : finish frame of the flash
args = ee.EasyArgs(sys.argv)
mark_in = 0
mark_out = 0
if args.mark_in and args.mark_out:
    mark_in = args.mark_in
    mark_out = args.mark_out
    
# annotation = 0 : annotation is not finished yet, 1 : finished
annotation = 0
location = ""       # store location directory.
numframe = 0
centerx = 0
centery = 0
frame2 = cv2.VideoCapture(0)
countinframe = 0  # index of current image
maxframes = 0 #maximum number of frames
x = 0
y = 0
width = 0
height = 0
# file accepts .jpg file
fileformat = ".jpg"
# 1 if the annotation has been saved.
annotationsaved = 0                                  
# store bounding boxes (rectangles) into the list
rectangles = []
# store undo or redo actions into the list
uraction = []
# store the result of changing of images from the annotation, true if it has been changed, false if its not.
updateant = []
# modes to drag or draw. If drag button is clicked, this will be changed to drag.
modes = "draw"
framenum = []
xmlimported = 0
xmlfilename = ""
undoredo = 0
# count number of frames in autoamtic tool.
countautoframe = 0

class ICTProject(QtGui.QMainWindow):    
    def __init__(self):
        super(ICTProject, self).__init__()
        
        self.initUI()
        
    def initUI(self):
       
        btn1 = QtGui.QPushButton("Automatic annotation", self)
        btn1.move(30, 50)
        btn1.resize(270, 30)
        btn2 = QtGui.QPushButton("Annotation from XML", self)
        btn2.move(30, 80)
        btn2.resize(270, 30)
        btn3 = QtGui.QPushButton("Show result Image/Video", self)
        btn3.move(30, 110)
        btn3.resize(270, 30)
        btn4 = QtGui.QPushButton("Open semi-automatic tool", self)
        btn4.move(30, 140)
        btn4.resize(270, 30)
        btn5 = QtGui.QPushButton("Help", self)
        btn5.move(30, 170)
        btn5.resize(270, 30)        
        btn6 = QtGui.QPushButton("About", self)
        btn6.move(30, 200)
        btn6.resize(270, 30)
        btn7 = QtGui.QPushButton("Exit", self)
        btn7.move(30, 230)
        btn7.resize(270, 30)   
      
        btn1.clicked.connect(self.button1)            
        btn2.clicked.connect(self.button2)
        btn3.clicked.connect(self.button3)            
        btn4.clicked.connect(self.button4)
        btn5.clicked.connect(self.button5)            
        btn6.clicked.connect(self.button6)
        btn7.clicked.connect(self.button7)
        
        self.statusBar()
        
        self.setGeometry(350, 300, 350, 300)
        self.setWindowTitle('ICT Project Annotation Tool V2.0')
        self.statusBar().showMessage('Annotation Tool V2.0 Made by ManJung Kim')
        self.show()       

    def button1(self):
        
        dataset = ET.Element("dataset")        
        QMessageBox.about(self, "Automatic annotation", "Please select your file.")    
        file2 = str(QtGui.QFileDialog.getOpenFileName(self, "Please select your video or image file.", ".")) 
        countautoframe = 0        
        
        # Convert the image to Gray if file is exist
        if (file2 != ""):
            # if the file is MOV (if last three character is 'MOV')
            if (file2[-3:] in ['MOV']):                
                xmlfile = str(QtGui.QFileDialog.getOpenFileName(self, "Please select your previous XML file if possible.", "."))
                filetosave = str(QtGui.QFileDialog.getSaveFileName(self, "Please select output filename to save the file.", "."))
                cap = cv2.VideoCapture(file2)
                fgbg = cv2.createBackgroundSubtractorMOG2()
                ret, frame1 = cap.read()
                countautoframe = countautoframe + 1
                # the total number of object of the frame.
                
                objectnumberofframe = []
                totalnumframe = 0
                objecttotalnumbers = 0
                
                # if the file is xml file
                if (xmlfile[-3:] in ['xml']):
                        import xml.dom.minidom
                        xml = xml.dom.minidom.parse(str(xmlfile)) 
                        xmlstring = xml.toprettyxml()
                        bufferedR = StringIO.StringIO(xmlstring)
                        frameindex = 0
                        
                        while True:
                                strings = bufferedR.readline()
                                if (strings == ''):
                                        break
                                if "frame number" in strings:
                                        numobject = 0
                                        # get numbers only, (i.e last element from the string)
                                        str2 = strings.split("=")[-1]
                                        str3 = str2.split("\'",1)[-1]
                                        #frame number
                                        aframe = str3.split("\'",1)[0]
                                        aframe = aframe.replace("\'", "")
                                        aframe = aframe.replace(">", "")
                                        aframe = aframe.replace("<", "") 
                                        aframe = aframe.replace("\"", "")
                                        aframe = aframe.replace("/", "")
                                        frameindex = int(aframe)
                                        totalnumframe = frameindex
                        # maximum 50 objects specified.
                        xmlx = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        xmly = [[0 for x in range(50)] for x in range(totalnumframe)]  
                        xmlw = [[0 for x in range(50)] for x in range(totalnumframe)]  
                        xmlh = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        cenx = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        ceny = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        print totalnumframe
                        bufferedR2 = StringIO.StringIO(xmlstring)
                        loop = True
                        while loop == True:                             
                                strings = bufferedR2.readline()                                
                                if (strings == ''):
                                        break
                                if "frame number" in strings:
                                        numobject = 0
                                        # get numbers only, (i.e last element from the string)
                                        str2 = strings.split("=")[-1]
                                        str3 = str2.split("\'",1)[-1]
                                        #frame number
                                        aframe = str3.split("\'",1)[0]
                                        aframe = aframe.replace("\'", "")
                                        aframe = aframe.replace(">", "")
                                        aframe = aframe.replace("<", "") 
                                        aframe = aframe.replace("\"", "")
                                        aframe = aframe.replace("/", "")
                                        frameindex = int(aframe)                                        
                                        objectnumberofframe.append(frameindex)        
                                if "boxinfo" in strings:
                                        numobject = numobject + 1
                                        if (numobject > objecttotalnumbers):
                                            objecttotalnumbers = numobject
                                            #print numobject
                                        objectnumberofframe[frameindex-1] = numobject
                                        #print objectnumberofframe[frameindex-1]
                                        # y
                                        str2 = strings.split(" ")[-1]
                                        stry = str2.split("=")[-1]
                                        stry = stry.replace("\'", "")
                                        stry = stry.replace(">", "")
                                        stry = stry.replace("<", "") 
                                        stry = stry.replace("\"", "")
                                        stry = stry.replace("/", "")
                                        xmly[frameindex-1][numobject] = int(stry)
                                        #print xmly[frameindex-1][numobject]
                                        #print stry
                                        # x
                                        str3 = strings.split(" ")[-2]
                                        strx = str3.split("=")[-1]
                                        strx = strx.replace("\'", "")
                                        strx = strx.replace(">", "")
                                        strx = strx.replace("<", "") 
                                        strx = strx.replace("\"", "")
                                        strx = strx.replace("/", "")
                                        xmlx[frameindex-1][numobject] = int(strx)
                                        #print xmlx[frameindex-1][numobject]
                                        #print strx
                                        # width
                                        str4 = strings.split(" ")[-3]
                                        strw = str4.split("=")[-1]
                                        strw = strw.replace("\'", "")
                                        strw = strw.replace(">", "")
                                        strw = strw.replace("<", "") 
                                        strw = strw.replace("\"", "")
                                        strw = strw.replace("/", "")
                                        xmlw[frameindex-1][numobject] = int(strw)
                                        #print xmlw[frameindex-1][numobject]
                                        #print strw
                                        # height
                                        str5 = strings.split(" ")[-4]
                                        strh = str5.split("=")[-1]
                                        strh = strh.replace("\'", "")
                                        strh = strh.replace(">", "")
                                        strh = strh.replace("<", "") 
                                        strh = strh.replace("\"", "")
                                        strh = strh.replace("/", "")
                                        xmlh[frameindex-1][numobject] = int(strh)
                                        #print xmlh[frameindex-1][numobject]
                                if "centroid" in strings:                                                                                    
                                        # y
                                        str2 = strings.split(" ")[-1]
                                        stry = str2.split("=")[-1]
                                        stry = stry.replace("\'", "")
                                        stry = stry.replace(">", "")
                                        stry = stry.replace("<", "") 
                                        stry = stry.replace("\"", "")
                                        stry = stry.replace("/", "")
                                        cenx[frameindex-1][numobject] = int(stry)
                                        #print cenx[frameindex-1][numobject]
                                        #print stry
                                        # x
                                        str3 = strings.split(" ")[-2]
                                        strx = str3.split("=")[-1]
                                        strx = strx.replace("\'", "")
                                        strx = strx.replace(">", "")
                                        strx = strx.replace("<", "") 
                                        strx = strx.replace("\"", "")
                                        strx = strx.replace("/", "")
                                        ceny[frameindex-1][numobject] = int(strx)
                                        #print ceny[frameindex-1][numobject]
                                        
##                avgcenx = {}
##                avgceny = {}
##                avgxvalue = 0
##                avgyvalue = 0     
##                print cenx[0][1]
##                for objectindexloop in range(1, objecttotalnumbers+1):
##                    for frameindexloop in range(1, totalnumframe):
##                                                # cenx[frameindexloop][objectindexloop] is the single x value.
##                        avgxvalue = avgxvalue + cenx[frameindexloop-1][objectindexloop]
##                        avgyvalue = avgyvalue + ceny[frameindexloop-1][objectindexloop]
##                        
##                    avgxvalue = avgxvalue / totalnumframe
##                    avgyvalue = avgyvalue / totalnumframe
##                    print avgxvalue
##                    print avgyvalue
##                    avgcenx[objectindexloop] = avgxvalue
##                    avgceny[objectindexloop] = avgyvalue
##                # print each average values.
##                # The avgcenx is y value actually, avgceny is the x value
##                # avgceny: average value of centerx
##                # avgcebx: average value of centery
##                print avgceny
##                print avgcenx

                print mark_in
                print mark_out
                
                Y = [[0 for x in range(50)] for x in range(totalnumframe)] 
                U = [[0 for x in range(50)] for x in range(totalnumframe)] 
                V = [[0 for x in range(50)] for x in range(totalnumframe)] 
                r = [[0 for x in range(50)] for x in range(totalnumframe)]
                h = [[0 for x in range(50)] for x in range(totalnumframe)]
                c = [[0 for x in range(50)] for x in range(totalnumframe)]
                w = [[0 for x in range(50)] for x in range(totalnumframe)]                           
                
                if (objectnumberofframe[0] != 0):
                    for x in range(1, objectnumberofframe[0]+1):                       
                            coordx = cenx[0][x]
                            coordy = ceny[0][x]                       
                            colorvalue = frame1[coordx,coordy]
                            Y[0][x] = colorvalue[0]
                            U[0][x] = colorvalue[1]
                            V[0][x] = colorvalue[2]
                            r[0][x] = xmlx[0][x]
                            h[0][x] = xmlh[0][x]
                            c[0][x] = xmly[0][x]
                            w[0][x] = xmlw[0][x]                        
                        
                        #print r,h,c,w
                                       
                
                fps = cv2.VideoCapture(file2).get(cv2.CAP_PROP_FPS)
                framewidth = cv2.VideoCapture(file2).get(cv2.CAP_PROP_FRAME_WIDTH)
                frameheight = cv2.VideoCapture(file2).get(cv2.CAP_PROP_FRAME_HEIGHT)
                # hardcode the kind of codec to "DIVX" because OpenCV does not support the codec from camera. 
                output2 = cv2.VideoWriter(filetosave,cv2.VideoWriter_fourcc(*'DIVX'),fps,(int(framewidth),int(frameheight)))
                QMessageBox.about(self, "Automatic annotation", "Reading the video file... please wait. \n It may takes few minutes. \n Do not quit the program, you will get message once it finishes. \n Click OK button below to start annotation.")
                dataset = ET.Element("dataset")              
                loopnumobject = 0
                loopnumobject = objectnumberofframe[0]
                previousindex = 0
                term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
                
                if (mark_in == 0 and mark_out == 0):
                    frameinfo = ET.SubElement(dataset, "frameInformation")
                    ET.SubElement(frameinfo, "frame", number="%d"%1)  
                    for loopx in range(1, loopnumobject+1):                           
                        object1 = ET.SubElement(frameinfo, "object", name="Robot %d"%loopx,id="0%d"%loopx)
                        ET.SubElement(object1, "boxinfo", x="%d"%xmlx[0][loopx],y="%d"%xmly[0][loopx],height="%d"%xmlh[0][loopx],width="%d"%xmlw[0][loopx])
                        ET.SubElement(object1, "centroid",x="%d"%cenx[0][loopx],y="%d"%ceny[0][loopx])
                
                while(cap.isOpened()):
                    ret, frame2 = cap.read()                    
                    if ret==True:
                        bgr = cv2.cvtColor(frame2, cv2.COLOR_YUV2BGR)
                        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
                        #mask = cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))

                        # add 1 to the frame number
                        countautoframe = countautoframe + 1
                        if (mark_in > 0 and mark_out > mark_in and mark_in < countautoframe < mark_out):
                            frameinfo = ET.SubElement(dataset, "frameInformation")
                            currentframe = int(countautoframe) - int(mark_in)
                            ET.SubElement(frameinfo, "frame", number="%d"%currentframe)
                        x,y,w,h = 0,0,0,0
                        # if nothing changed in xml file of that frame
                        
                        if (countautoframe < totalnumframe):                            
                            if (cenx[countautoframe][1] == 0):                            
                                for loopx in range(1, loopnumobject+1):
                                    if (xmlw[previousindex][loopx] != 0):
                                        color_lower = np.array([Y[previousindex][loopx]-5, U[previousindex][loopx]-5, V[previousindex][loopx]-5],np.uint8)
                                        color_upper = np.array([Y[previousindex][loopx]+5, U[previousindex][loopx]+5, V[previousindex][loopx]+5],np.uint8) 
                                        colordetect = cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
                                        x,y,w,h = xmlx[previousindex][loopx],xmly[previousindex][loopx],xmlw[previousindex][loopx],xmlh[previousindex][loopx]
                                        track_window = (x,y,w,h)
                                        x1 = x+w
                                        y1 = y+h
                                        hsv_roi = hsv[y:y1, x:x1]
                                        mask_roi = colordetect[y:y1, x:x1]
                                        hist = cv2.calcHist([hsv_roi], [0], mask_roi, [16], [0, 180])
                                        cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
                                        hist2 = hist.reshape(-1)
                                        prob = cv2.calcBackProject([hsv], [0], hist2, [0, 180], 1)
                                        prob &= colordetect
                                        track_box, track_window = cv2.CamShift(prob, track_window, term_crit)
                                        track_box2, track_window2 = cv2.meanShift(prob, track_window, term_crit)
                                        a,b,w,h = track_window
                                        x,y,c,d = track_window2
                                        cv2.rectangle(frame2,(x,y),(x+w,y+h),(0,255,0),2)
                                        cv2.circle(frame2,(int(x+0.5*w),int(y+0.5*h)),2,(0,0,255),2)
                                        centerx = x+0.5*w
                                        centery = y+0.5*h                                
                                      
                                        xpos = "x: %d" % x
                                        ypos = "y: %d" % y
                                        zpos = "height: %d" % h
                                        width = "width: %d" % w                  
                                        font = cv2.FONT_HERSHEY_SIMPLEX
                                        robotname = "EE %d" % loopx
                                        cv2.putText(frame2,robotname,(int(x+0.5*w),int(y+0.5*h)+30), font, 1,(255,255,255),2)
                                        cv2.putText(frame2,xpos,(int(x+0.5*w),int(y+0.5*h)+70), font, 1,(255,255,255),2)
                                        cv2.putText(frame2,ypos,(int(x+0.5*w),int(y+0.5*h)+110), font, 1,(255,255,255),2)
                                        cv2.putText(frame2,zpos,(int(x+0.5*w),int(y+0.5*h)+150), font, 1,(255,255,255),2)
                                        cv2.putText(frame2,width,(int(x+0.5*w),int(y+0.5*h)+190), font, 1,(255,255,255),2)    
                                        cv2.putText(frame2,"frame number: %d"%countautoframe,(int(0),int(60)), font, 1,(255,255,255),2)
                                        if (mark_in > 0 and mark_out > mark_in and mark_in < countautoframe < mark_out):
                                            object1 = ET.SubElement(frameinfo, "object", name="Robot %d"%loopx,id="0%d"%loopx)
                                            ET.SubElement(object1, "boxinfo", x="%d"%x,y="%d"%y,height="%d"%h,width="%d"%w)
                                            ET.SubElement(object1, "centroid",x="%d"%centerx,y="%d"%centery)
                                        if (mark_in == 0 and mark_out == 0):
                                            object1 = ET.SubElement(frameinfo, "object", name="Robot %d"%loopx,id="0%d"%loopx)
                                            ET.SubElement(object1, "boxinfo", x="%d"%x,y="%d"%y,height="%d"%h,width="%d"%w)
                                            ET.SubElement(object1, "centroid",x="%d"%centerx,y="%d"%centery)
                                            
                            # if something changed in the xml file of that frame
                            else:
                                previousindex = countautoframe
                                loopnumobject = objectnumberofframe[previousindex]                                
                               
                                for x in range(1, objectnumberofframe[previousindex]+1):                       
                                    coordx = cenx[previousindex][x]
                                    coordy = ceny[previousindex][x]
                                    #print frame1[coordx,coordy]
                                    colorvalue = frame1[coordx,coordy]
                                    Y[previousindex][x] = colorvalue[0]
                                    U[previousindex][x] = colorvalue[1]
                                    V[previousindex][x] = colorvalue[2]
                                    
                                for loopx in range(1, loopnumobject+1):
                                    x,y,w,h = 0,0,0,0
                                    color_lower = np.array([Y[previousindex][loopx]-5, U[previousindex][loopx]-5, V[previousindex][loopx]-5],np.uint8)
                                    color_upper = np.array([Y[previousindex][loopx]+5, U[previousindex][loopx]+5, V[previousindex][loopx]+5],np.uint8)                           
                                    colordetect = cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
                                    x,y,w,h = xmlx[previousindex][loopx],xmly[previousindex][loopx],xmlw[previousindex][loopx],xmlh[previousindex][loopx]
                                    track_window = (x,y,w,h)
                                    x1 = x+w
                                    y1 = y+h
                                    hsv_roi = hsv[y:y1, x:x1]
                                    mask_roi = colordetect[y:y1, x:x1]
                                    hist = cv2.calcHist([hsv_roi], [0], mask_roi, [16], [0, 180])
                                    cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
                                    hist2 = hist.reshape(-1)
                                    prob = cv2.calcBackProject([hsv], [0], hist2, [0, 180], 1)
                                    prob &= colordetect
                                    track_box, track_window = cv2.CamShift(prob, track_window, term_crit)
                                    track_box2, track_window2 = cv2.meanShift(prob, track_window, term_crit)
                                    a,b,w,h = track_window
                                    x,y,c,d = track_window2
                                    cv2.rectangle(frame2,(x,y),(x+w,y+h),(0,255,0),2)
                                    cv2.circle(frame2,(int(x+0.5*w),int(y+0.5*h)),2,(0,0,255),2)
                                    centerx = x+0.5*w
                                    centery = y+0.5*h                               
                                  
                                    xpos = "x: %d" % x
                                    ypos = "y: %d" % y
                                    zpos = "height: %d" % h
                                    width = "width: %d" % w                  
                                    font = cv2.FONT_HERSHEY_SIMPLEX
                                    robotname = "EE %d" % loopx
                                    cv2.putText(frame2,robotname,(int(x+0.5*w),int(y+0.5*h)+30), font, 1,(255,255,255),2)
                                    cv2.putText(frame2,xpos,(int(x+0.5*w),int(y+0.5*h)+70), font, 1,(255,255,255),2)
                                    cv2.putText(frame2,ypos,(int(x+0.5*w),int(y+0.5*h)+110), font, 1,(255,255,255),2)
                                    cv2.putText(frame2,zpos,(int(x+0.5*w),int(y+0.5*h)+150), font, 1,(255,255,255),2)
                                    cv2.putText(frame2,width,(int(x+0.5*w),int(y+0.5*h)+190), font, 1,(255,255,255),2)                                
                                    cv2.putText(frame2,"frame number: %d"%countautoframe,(int(0),int(60)), font, 1,(255,255,255),2)           
                                    if (mark_in > 0 and mark_out > mark_in and mark_in < countautoframe < mark_out):
                                        object1 = ET.SubElement(frameinfo, "object", name="Robot %d"%loopx,id="0%d"%loopx)
                                        ET.SubElement(object1, "boxinfo", x="%d"%x,y="%d"%y,height="%d"%h,width="%d"%w)
                                        ET.SubElement(object1, "centroid",x="%d"%centerx,y="%d"%centery)
                                    if (mark_in == 0 and mark_out == 0):
                                            object1 = ET.SubElement(frameinfo, "object", name="Robot %d"%loopx,id="0%d"%loopx)
                                            ET.SubElement(object1, "boxinfo", x="%d"%x,y="%d"%y,height="%d"%h,width="%d"%w)
                                            ET.SubElement(object1, "centroid",x="%d"%centerx,y="%d"%centery)
                                           
                        output2.write(frame2)
                                           
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    else:
                        break
                
                cap.release()
                output2.release()
                tree = ET.ElementTree(dataset)                
                annotation = 1
                QMessageBox.about(self, "Automatic annotation", "Annotation has been finished! \n annotated video is created in the folder.")
                xmlsave = str(QtGui.QFileDialog.getSaveFileName(self, "Please write output xml filename to save the dataset.", "."))
                tree.write(xmlsave)
                print countautoframe
            else:
                print "If the file is image, Please use semi-automatic tool to annotate object."
          

    def button2(self):
        sender = self.sender()
        dataset = ET.Element("dataset")        
        QMessageBox.about(self, "Convert XML to Video", "Please select your initial video file.")    
        file2 = str(QtGui.QFileDialog.getOpenFileName(self, "Please select your initial video file.", ".")) 
        countautoframe = 0        

        if (file2 != ""):            
            if (file2[-3:] in ['MOV']):                
                xmlfile = str(QtGui.QFileDialog.getOpenFileName(self, "Please select your XML file.", "."))
                filetosave = str(QtGui.QFileDialog.getSaveFileName(self, "Please select output filename to save the file.", "."))
                cap = cv2.VideoCapture(file2)
                fgbg = cv2.createBackgroundSubtractorMOG2()
                ret, frame1 = cap.read()
                countautoframe = countautoframe + 1
                # the total number of object of the frame.
                objectnumberofframe = []
                totalnumframe = 0
                
                # if the file is xml file
                if (xmlfile[-3:] in ['xml']):
                        import xml.dom.minidom
                        xml = xml.dom.minidom.parse(str(xmlfile)) 
                        xmlstring = xml.toprettyxml()
                        bufferedR = StringIO.StringIO(xmlstring)
                        frameindex = 0
                        
                        while True:
                                strings = bufferedR.readline()
                                if (strings == ''):
                                        break
                                if "frame number" in strings:
                                        numobject = 0
                                        # get numbers only, (i.e last element from the string)
                                        str2 = strings.split("=")[-1]
                                        str3 = str2.split("\'",1)[-1]
                                        #frame number
                                        aframe = str3.split("\'",1)[0]
                                        aframe = aframe.replace("\'", "")
                                        aframe = aframe.replace(">", "")
                                        aframe = aframe.replace("<", "") 
                                        aframe = aframe.replace("\"", "")
                                        aframe = aframe.replace("/", "")
                                        frameindex = int(aframe)
                                        totalnumframe = frameindex
                        # maximum 50 objects specified.
                        xmlx = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        xmly = [[0 for x in range(50)] for x in range(totalnumframe)]  
                        xmlw = [[0 for x in range(50)] for x in range(totalnumframe)]  
                        xmlh = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        cenx = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        ceny = [[0 for x in range(50)] for x in range(totalnumframe)] 
                        print totalnumframe
                        bufferedR2 = StringIO.StringIO(xmlstring)
                        loop = True
                        while loop == True:                             
                                strings = bufferedR2.readline()                                
                                if (strings == ''):
                                        break
                                if "frame number" in strings:
                                        numobject = 0
                                        # get numbers only, (i.e last element from the string)
                                        str2 = strings.split("=")[-1]
                                        str3 = str2.split("\'",1)[-1]
                                        #frame number
                                        aframe = str3.split("\'",1)[0]
                                        aframe = aframe.replace("\'", "")
                                        aframe = aframe.replace(">", "")
                                        aframe = aframe.replace("<", "") 
                                        aframe = aframe.replace("\"", "")
                                        aframe = aframe.replace("/", "")
                                        frameindex = int(aframe)                                        
                                                        
                                if "boxinfo" in strings:
                                                numobject = numobject + 1                                                
                                                objectnumberofframe.append(frameindex)
                                                objectnumberofframe[frameindex-1] = numobject
                                                #print objectnumberofframe[frameindex-1]
                                                # y
                                                str2 = strings.split(" ")[-1]
                                                stry = str2.split("=")[-1]
                                                stry = stry.replace("\'", "")
                                                stry = stry.replace(">", "")
                                                stry = stry.replace("<", "") 
                                                stry = stry.replace("\"", "")
                                                stry = stry.replace("/", "")
                                                xmly[frameindex-1][numobject] = int(stry)
                                                #print xmly[frameindex-1][numobject]
                                                #print stry
                                                # x
                                                str3 = strings.split(" ")[-2]
                                                strx = str3.split("=")[-1]
                                                strx = strx.replace("\'", "")
                                                strx = strx.replace(">", "")
                                                strx = strx.replace("<", "") 
                                                strx = strx.replace("\"", "")
                                                strx = strx.replace("/", "")
                                                xmlx[frameindex-1][numobject] = int(strx)
                                                #print xmlx[frameindex-1][numobject]
                                                #print strx
                                                # width
                                                str4 = strings.split(" ")[-3]
                                                strw = str4.split("=")[-1]
                                                strw = strw.replace("\'", "")
                                                strw = strw.replace(">", "")
                                                strw = strw.replace("<", "") 
                                                strw = strw.replace("\"", "")
                                                strw = strw.replace("/", "")
                                                xmlw[frameindex-1][numobject] = int(strw)
                                                #print xmlw[frameindex-1][numobject]
                                                #print strw
                                                # height
                                                str5 = strings.split(" ")[-4]
                                                strh = str5.split("=")[-1]
                                                strh = strh.replace("\'", "")
                                                strh = strh.replace(">", "")
                                                strh = strh.replace("<", "") 
                                                strh = strh.replace("\"", "")
                                                strh = strh.replace("/", "")
                                                xmlh[frameindex-1][numobject] = int(strh)
                                                #print xmlh[frameindex-1][numobject]
                                if "centroid" in strings:                                                                                    
                                                # y
                                                str2 = strings.split(" ")[-1]
                                                stry = str2.split("=")[-1]
                                                stry = stry.replace("\'", "")
                                                stry = stry.replace(">", "")
                                                stry = stry.replace("<", "") 
                                                stry = stry.replace("\"", "")
                                                stry = stry.replace("/", "")
                                                cenx[frameindex-1][numobject] = int(stry)
                                                #print cenx[frameindex-1][numobject]
                                                #print stry
                                                # x
                                                str3 = strings.split(" ")[-2]
                                                strx = str3.split("=")[-1]
                                                strx = strx.replace("\'", "")
                                                strx = strx.replace(">", "")
                                                strx = strx.replace("<", "") 
                                                strx = strx.replace("\"", "")
                                                strx = strx.replace("/", "")
                                                ceny[frameindex-1][numobject] = int(strx)
                                                #print ceny[frameindex-1][numobject]                     

               
                
                                       
                fps = cv2.VideoCapture(file2).get(cv2.CAP_PROP_FPS)
                framewidth = cv2.VideoCapture(file2).get(cv2.CAP_PROP_FRAME_WIDTH)
                frameheight = cv2.VideoCapture(file2).get(cv2.CAP_PROP_FRAME_HEIGHT)
                output2 = cv2.VideoWriter(filetosave,cv2.VideoWriter_fourcc(*'XVID'),fps,(int(framewidth),int(frameheight)))
                dataset = ET.Element("dataset")              
                loopnumobject = 0
                loopnumobject = objectnumberofframe[0]
                previousindex = 0
                #term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
          
                
                while(cap.isOpened()):
                    ret, frame2 = cap.read()                    
                    if ret==True:
                        # add 1 to the frame number
                        countautoframe = countautoframe + 1
                        frameinfo = ET.SubElement(dataset, "frameInformation")
                        ET.SubElement(frameinfo, "frame", number="%d"%countautoframe)
                        x,y,w,h = 0,0,0,0
                        # if nothing changed in xml file of that frame                        
                        if (countautoframe < totalnumframe):                                              
                            for loopx in range(1, loopnumobject+1):                 
                                x,y,w,h = xmlx[countautoframe][loopx],xmly[countautoframe][loopx],xmlw[countautoframe][loopx],xmlh[countautoframe][loopx]
                                cv2.rectangle(frame2,(x,y),(x+w,y+h),(0,255,0),2)
                                cv2.circle(frame2,(int(x+0.5*w),int(y+0.5*h)),2,(0,0,255),2)
                                centerx = x+0.5*w
                                centery = y+0.5*h                             
                                xpos = "x: %d" % x
                                ypos = "y: %d" % y
                                zpos = "height: %d" % h
                                width = "width: %d" % w                  
                                font = cv2.FONT_HERSHEY_SIMPLEX
                                robotname = "EE %d" % loopx
                                cv2.putText(frame2,robotname,(int(x+0.5*w),int(y+0.5*h)+30), font, 1,(255,255,255),2)
                                cv2.putText(frame2,xpos,(int(x+0.5*w),int(y+0.5*h)+70), font, 1,(255,255,255),2)
                                cv2.putText(frame2,ypos,(int(x+0.5*w),int(y+0.5*h)+110), font, 1,(255,255,255),2)
                                cv2.putText(frame2,zpos,(int(x+0.5*w),int(y+0.5*h)+150), font, 1,(255,255,255),2)
                                cv2.putText(frame2,width,(int(x+0.5*w),int(y+0.5*h)+190), font, 1,(255,255,255),2)    
                                cv2.putText(frame2,"frame number: %d"%countautoframe,(int(0),int(60)), font, 1,(255,255,255),2) 
                                object1 = ET.SubElement(frameinfo, "object", name="Robot %d"%loopx,id="0%d"%loopx)
                                ET.SubElement(object1, "boxinfo", x="%d"%x,y="%d"%y,height="%d"%h,width="%d"%w)
                                ET.SubElement(object1, "centroid",x="%d"%centerx,y="%d"%centery)
                   
                        output2.write(frame2)
                                           
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    else:
                        break
                
                cap.release()
                output2.release()
                tree = ET.ElementTree(dataset)                
                annotation = 1
                QMessageBox.about(self, "Open images/video", "Annotation has been finished! \n annotated video is created in the folder.")
                
                print countautoframe
            else:
                print "If the file is image, Please use semi-automatic tool to annotate object." 
           
            
    def button3(self):
        sender = self.sender()       
        file2 = str(QtGui.QFileDialog.getOpenFileName(self, "Please select your video or image file.", "."))
        cap = cv2.VideoCapture(file2)           
                  
        while(cap.isOpened()):
            ret, resultframe = cap.read()
            cv2.imshow("Output Result", resultframe)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
       
        
    def button4(self):      
        main = MyPopup()
        main.setGeometry(QRect(100, 100, 1400, 600))        
        main.show()
        
    def button5(self):      
        sender = self.sender()
        QMessageBox.about(self, "Help", "Click the Automatic annotation button to begin automatic annotation. \n Open the MOV file or jpeg file. \n You need to wait few minutes depends on the size of the file.\n Once you finish annotation, you may create XML file, and \n click the annotation from XML button to directly convert XML to video file.\n click the Show result Image/Video button to see the result output in python. \n click Open semi-automatic tool to semi-automatically fix the annotations. \n Click About button to see the background of this project. \n Click Exit to quit this program.")

    def button6(self):      
        sender = self.sender()
        QMessageBox.about(self, "About", "File name: ICTproject1_final.py \n Author: ManJung Kim \n This software is made by uniSA student, This is my own work as defined by the University's Academic Misconduct policy. \n This is an annotation tool which is required from the ICT Project. \n This is second version which is made by ManJung Kim during the second semester. \n This project is about Quantifiable Visual Tracking, \n this annotation tool will be used after the calibration process from other team mates. \n If you have any questions, email to kimmy016@mymail.unisa.edu.au." )

    def button7(self):      
        sender = self.sender()
        sys.exit()

class MyPopup(QtGui.QMainWindow):
    def __init__(self):
        
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle('Semi-automatic Tool V2.0 by ManJung Kim')
        #Stacking for undo and redo
        self.urstacks = []
        
        #number of annotated frame      
        btn1 = QtGui.QPushButton("Import image frames" , self)
        btn1.move(1030, 270)
        btn1.resize(270, 30)
        btn2 = QtGui.QPushButton("Drag" , self)
        btn2.move(1130, 130)
        btn2.resize(50, 30)
        btn22 = QtGui.QPushButton("Draw" , self)
        btn22.move(1180, 130)
        btn22.resize(50, 30)        
        btn3 = QtGui.QPushButton("Prev" , self)
        btn3.move(1030, 80)
        btn3.resize(100, 30)
        btn32 = QtGui.QPushButton("Next" , self)
        btn32.move(1130, 80)
        btn32.resize(100, 30)
        btn4 = QtGui.QPushButton("Import XML File", self)
        btn4.move(1030, 340)
        btn4.resize(270, 30)
        btn5 = QtGui.QPushButton("Split frames from a video", self)
        btn5.move(1030, 190)
        btn5.resize(270, 30)        
        btn6 = QtGui.QPushButton("Update XML File", self)
        btn6.move(1030, 420)
        btn6.resize(270, 30)
        btn7 = QtGui.QPushButton("Exit", self)
        btn7.move(1030, 490)
        btn7.resize(270, 30)
        btn8 = QtGui.QPushButton("Undo", self)
        btn8.move(1030, 130)
        btn8.resize(50, 30)
        btn9 = QtGui.QPushButton("Redo", self)
        btn9.move(1080, 130)
        btn9.resize(50, 30)
        
      
        btn1.clicked.connect(self.button1)            
        btn2.clicked.connect(self.button2)
        btn22.clicked.connect(self.button22)
        btn3.clicked.connect(self.button3)
        btn32.clicked.connect(self.button32) 
        btn4.clicked.connect(self.button4)
        btn5.clicked.connect(self.button5)            
        btn6.clicked.connect(self.button6)
        btn7.clicked.connect(self.button7)
        btn8.clicked.connect(self.button8)
        btn9.clicked.connect(self.button9)

        # 0 if dragging is disabled, 1 if dragging is enabled.
        self.dragable = 0
        # 0 if drawing is disabled, 1 if drawing is enabled.
        self.drawable = 0
        # 0 if resizing is not ready, 1 if resizing is ready to enable.
        self.ready = 0
        # 0 if resizing is disabled, 1 if resizing is enabled.
        self.resizable = 0        
        self.direction = ""
        
        self.textcoord = QtGui.QLabel(self)
   
        self.pixmap = QtGui.QPixmap(self)
        self.frame = QtGui.QFrame(self)        
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setGeometry(QtCore.QRect(10, 10, 960, 540))        
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 960, 540))
        #self.scrollArea.setMouseTracking(False)
        #self.scrollArea.setWidgetResizable(True)
        self.pic2 = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.pic2.setCursor(QtCore.Qt.CrossCursor)
        self.pic2.setWordWrap(True)
        self.pic2.setMouseTracking(True)
        self.scrollArea.setWidget(self.pic2)
        self.pic2.pen = QtGui.QPen(Qt.green)
        self.pic2.paint = QtGui.QPainter()
        self.pic2.pen = QtGui.QPen(Qt.green)                
        self.rectPen = QtGui.QPen(Qt.green)
       
        self.pic2.paintEvent = self.imagePaintEvent
        self.pic2.mousePressEvent = self.imageMousePressEvent
        self.pic2.mouseReleaseEvent = self.imageMouseReleaseEvent
        self.pic2.mouseMoveEvent = self.imageMouseMoveEvent             
        self.show()   

    def imageMouseMoveEvent(self, event):
        global rectangles, countinframe
        
        x,y = event.pos().x(),event.pos().y()
        if (self.dragable == 1):
                (i,j,k,m) = self.previous
                dx,dy = x-self.rectDragPoint.x(),y-self.rectDragPoint.y()
                currentx,currenty = i+dx, j+dy
                if 0 <= x < self.pic2.width() and 0 <= y < self.pic2.height() \
                                        and 0 <= currentx < self.pic2.width()-k and 0 <= currenty < self.pic2.height()-m:
                        rectangles[countinframe][self.rectToDrag] = (currentx,currenty,k,m)
                        self.pic2.repaint()
                                                
        elif (self.resizable == 1):
                (i,j,w,h) = rectangles[countinframe][self.resizeboxes]
                # North west direction
                if self.direction == "NW":
                        dx,dy = x-i, y-j
                        currentx, currenty = x,y
                        currentw, currenth = w-dx,h-dy
                # South west direction
                if self.direction == "SW":
                        dx,dy = x-i, y-j-h
                        currentx, currenty = i+dx, j
                        currentw, currenth = w-dx,h+dy
                # North east direction
                if self.direction == "NE":
                        dx,dy = x-i-w, y-j
                        currentx, currenty = i,j+dy
                        currentw, currenth = w+dx,h-dy
                # South east direction
                if self.direction == "SE":
                        dx,dy = x-i-w, y-j-h
                        currentx, currenty = i,j
                        currentw, currenth = w+dx,h+dy
                # west direction
                if self.direction == "W":
                        dx = x-i
                        currentx, currenty = i+dx,j
                        currentw, currenth = w-dx,h
                # east direction
                if self.direction == "E":
                        dx = x-i-w
                        currentx, currenty = i,j
                        currentw, currenth = w+dx,h
                # north direction
                if self.direction == "N":
                        dy = y-j
                        currentx, currenty = i,j+dy
                        currentw, currenth = w,h-dy
                # south direction
                if self.direction == "S":
                        dy = y-j-h
                        currentx, currenty = i,j
                        currentw, currenth = w,h+dy

                rectangles[countinframe][self.resizeboxes] = (currentx,currenty,currentw,currenth)
                self.pic2.repaint()

        #when mode is equal to draw.
        elif (modes == "draw"):
                self.ready = 0
                for (i,j,k,m) in rectangles[countinframe]:
                        if abs(x-i)<=2:
                                if abs(y-j)<=2:   
                                        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))
                                        # North west direction
                                        self.direction = "NW"
                                        self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                        self.ready = 1
                                        break
                                elif abs(y-j-m)<=2:   
                                        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeBDiagCursor))
                                        # South west direction
                                        self.direction = "SW"
                                        self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                        self.ready = 1
                                        break
                                elif -2<=y-j<=m+2:  
                                        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
                                        # west direction
                                        self.direction = "W"
                                        self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                        self.ready = 1
                                        break
                        elif abs(x-i-k)<=2:
                                if abs(y-j)<=2:  
                                        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeBDiagCursor))
                                        # North east direction
                                        self.direction = "NE"
                                        self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                        self.ready = 1
                                        break
                                elif abs(y-j-m)<=2:   
                                        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))
                                        # South east direction
                                        self.direction = "SE"
                                        self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                        self.ready = 1
                                        break
                                elif -2<=y-j<=m+2:  
                                        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
                                        # east direction
                                        self.direction = "E"
                                        self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                        self.ready = 1
                                        break
                        elif abs(y-j)<=2 and -2<=x-i<=k+2:   
                                self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeVerCursor))
                                # north direction
                                self.direction = "N"
                                self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                self.ready = 1
                                break
                        elif abs(y-j-m)<=2 and -2<=x-i<=k+2:   
                                self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeVerCursor))
                                # south direction
                                self.direction = "S"
                                self.resizeboxes = rectangles[countinframe].index((i,j,k,m))
                                self.ready = 1
                                break
                                
                if not (self.ready == 1):
                        if self.pic2.cursor().shape() != QtCore.Qt.CrossCursor:
                                        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
                                
        if self.pic2.pixmap():
                if (self.drawable == 1):
                        (x,y) = self.clickedpoint
                        (self.tempWidth, self.tempHeight) = ((event.pos().x() - x), (event.pos().y() - y))
                        self.pic2.repaint()
                                

    def imageMousePressEvent(self, event):
        global modes, currentTool, countinframe
        x,y = event.pos().x(),event.pos().y()
        # if image files are imported
        if self.pic2.pixmap():
                if modes == "draw":
                        if (self.ready == 1):
                                self.resizable = 1
                                self.previous = rectangles[countinframe][self.resizeboxes]
                                        
                        else:
                                self.drawable = 1

                        # Clicked point x,y.
                        self.clickedpoint = (x,y)
                                
                if modes == "drag":
                        self.dragable = 0
                        for (i,j,k,m) in rectangles[countinframe]:
                                if ((abs(x-i)<=2 or abs(x-i-k)<=2) and -2<=y-j<=m+2) or ((abs(y-j)<=2 or abs(y-j-m)<=2) and -2<=x-i<=k+2):
                                                #print "x:%d y:%d i:%d j:%d w:%d h:%d" % (x,y,i,j,k+i,m+j)
                                        self.rectToDrag = rectangles[countinframe].index((i,j,k,m))
                                        self.rectDragPoint = event.pos()
                                        self.dragable = 1
                                        self.previous = (i,j,k,m)
                                        self.next = (-1,-1,-1,-1)

    def imageMouseReleaseEvent(self, event):
        global modes, countinframe
        # if image files are imported
        if self.pic2.pixmap():
                if modes == "draw":
                        # if the box is resized
                        if (self.resizable == 1):
                                (i,j,w,h) = rectangles[countinframe][self.resizeboxes]
                                if w < 0:
                                        i += w
                                        w = abs(w)
                                if h < 0:
                                        j += h
                                        h = abs(h)
                                rectangles[countinframe][self.resizeboxes] = self.next = (i,j,w,h)
                                # i,j,w,h : resized rectangle x,y,w,h order.
                                
                                command = resize(countinframe, self.previous, self.next, "Draw a rectangle")
                                self.urstacks[countinframe].push(command)
                                self.resizable = 0
                                updateant[countinframe] = True
                                self.pic2.repaint()
                                
                        # if the box is not resized.
                        else:
                                #x,y : coming from click event.
                                (x,y) = self.clickedpoint
                                        
                                width, height = (event.pos().x() - x), (event.pos().y() - y)
                                if width != 0 and height != 0:  
                                        if width < 0:
                                                width = abs(width)
                                                x = event.pos().x()
                                        if height < 0:
                                                height = abs(height)
                                                y = event.pos().y()
                                        command = add(countinframe, (x,y,width,height), "Add a rectangle")                                                
                                        self.urstacks[countinframe].push(command)                                           
                                        updateant[countinframe] = True
                                if (self.drawable == 1):
                                        self.drawable = 0
                                        self.pic2.repaint()
                if (modes == "drag") and (self.dragable == 1):
                        updateant[countinframe] = True
                        self.pic2.repaint()
                        self.dragable = 0
                        if self.next == (-1,-1,-1,-1):
                                (i,j,k,m) = self.previous
                                dx,dy = event.pos().x()-self.rectDragPoint.x(),event.pos().y()-self.rectDragPoint.y()
                                self.next = (i+dx,j+dy,k,m)
                        command = drag(countinframe, self.previous, self.next, "Drag a rectangle")
                        self.urstacks[countinframe].push(command)
    
    def imagePaintEvent(self, event):
        global countinframe
        if self.pic2.pixmap():          
            self.pic2.paint.begin(self.pic2)
            self.pic2.paint.setPen(self.pic2.pen)
            self.pic2.paint.drawImage(self.pic2.rect(), QtGui.QImage(self.pic2.pixmap()))            
            if (self.drawable == 1):
                        self.pic2.paint.setPen(self.rectPen)
                        (x,y) = self.clickedpoint
                        self.pic2.paint.drawRect(x,y,self.tempWidth,self.tempHeight)
            if (len(rectangles)>0):
                        for index,(i,j,k,m) in enumerate(rectangles[countinframe]):
                                self.pic2.paint.setPen(self.rectPen)
                                self.pic2.paint.drawRect(i,j,k,m)
                                #number of object, if draw one rectangle, index+1 is 1, if draw two, index+1 is 2.
                                self.pic2.paint.drawText(i+3,j+12, QtCore.QString.number(index+1))
            self.pic2.paint.end()

    # import image frames button        
    def button1(self, path=None):         
        global location, rectangles, updateant, maxframes
        sender = self.sender()
        if path:
            path = location
        else:  
            location = str(QtGui.QFileDialog.getExistingDirectory(self, "Please select Folder directory", "."))
        if (location != ""):            
                allFiles = os.listdir(location)
                imageFrames = sorted([x for x in allFiles if os.path.splitext(x)[-1] in fileformat])
                # leave only numbers from the string list
                tofindmaxframes = [i.replace("frame","") for i in imageFrames]
                tofindmaxframes = [i.replace("jpg","") for i in tofindmaxframes]
                tofindmaxframes = [i.replace(".","") for i in tofindmaxframes]
                tofindmaxframes = [i.replace("\'","") for i in tofindmaxframes]
                # and convert the string list to int list
                tofindmaxframes = map(int, tofindmaxframes)
                # then get max numbers from the int list by using max function
                maxframes = max(tofindmaxframes)               
                rectangles = []
                rectangles.append([])
                self.stack = QtGui.QUndoStack(self)
                self.urstacks.append(self.stack)
                updateant.append(False)
                if len(imageFrames) > 0: 
                    self.pixmap = QtGui.QPixmap(location+"\\frame%d.jpg" % countinframe)                    
                    self.pic2.setPixmap(self.pixmap)
                    self.pic2.setFixedSize(1920,1080)
                    self.painter = QtGui.QPainter(self.pixmap)        
                    self.painter.setBrush(QBrush("#004fc5"))
                    self.painter.setPen(Qt.green)
                    
                else:
                    self.statusBar().showMessage("No image frames are found in this directory.")
       
        self.pic2.repaint()
        self.show()
        
    # drag button
    def button2(self):
        global modes
        sender = self.sender()
        modes = "drag"
        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.SizeAllCursor))
        #print modes
        self.show()

    # draw button
    def button22(self):   
        global modes
        sender = self.sender()
        modes = "draw"
        self.pic2.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        #print modes
        self.show()

    # prev button
    def button3(self):        
        global countinframe, pixmap, rectangles, pic2    
        sender = self.sender()
        if (countinframe > 0):
            countinframe -= 1            
            self.pic2.clear()           
            rectangles.append([])       
            uraction.append([False,False])
            updateant.append(False)
            self.stack = QtGui.QUndoStack(self)
            self.urstacks.append(self.stack)
            pixmap = QtGui.QPixmap(location+"\\frame%d.jpg" % countinframe)  
            self.pic2.setPixmap(pixmap)            
            self.pic2.repaint()
            print "Frame number: %d"%countinframe            
            
    # next button
    def button32(self):      
        global countinframe, pixmap, rectangles, pic2, maxframes     
        sender = self.sender()
        countinframe += 1        
        rectangles.append([])       
        uraction.append([False,False])
        updateant.append(False)
        self.stack = QtGui.QUndoStack(self)
        self.urstacks.append(self.stack)        
        self.pic2.clear()
        pixmap = QtGui.QPixmap(location+"\\frame%d.jpg" % countinframe)        
        self.pic2.setPixmap(pixmap)
        self.pic2.repaint()
        print "Frame number: %d"%countinframe        
        
    # Split frames from a video button
    def button5(self, path=None):      
        sender = self.sender()
        # ask input video file dynamically
        file2 = str(QtGui.QFileDialog.getOpenFileName(self, "Please select the video file to split.", "."))
        
        # Convert the image to Gray if file is exist
        if (file2 != ""):            
            #if the file is image file.
            if (file2[-3:] in ['jpg'] or file2[-3:] in ['png']):
                QMessageBox.about(self, "Split frames from a video button", "The file is imagefile already, no need to do this. Just import image folder.")
            #if the input file is video file.
            else:
                location2 = str(QtGui.QFileDialog.getExistingDirectory(self, "Please select output Folder directory", "."))
                vidcap = cv2.VideoCapture(file2)               
                success,image = vidcap.read()                
                count = 0
                while success:
                    success,image = vidcap.read()
                    cv2.imwrite(location2+"\\frame%d.jpg" % count, image)
                    if cv2.waitKey(10) == 27:                    
                        break
                    count += 1
        else:
                QMessageBox.about(self, "Split frames from a video button", "Please import the MOV file or avi file!")   
                

    # Undo button
    def button8(self):
        global countinframe, annotationsaved
        sender = self.sender()
        self.urstacks[countinframe].undo()
        if self.urstacks[countinframe].index() == annotationsaved:
              updateant[countinframe] = False
        else:
              updateant[countinframe] = True
        
        self.pic2.repaint()
        
    # Redo button
    def button9(self):
        global countinframe, annotationsaved
        sender = self.sender()
        self.urstacks[countinframe].redo()
        if self.urstacks[countinframe].index() == annotationsaved:
            updateant[countinframe] = False
        else:
            updateant[countinframe] = True
        
        self.pic2.repaint()    

    # Import XML File button
    def button4(self):      
        sender = self.sender()
        global xmlimported, xmlfilename, rectangles, updateant, framenum, maxframes
        # if images are imported
        if self.pic2.pixmap():
                xmlfilename = QtGui.QFileDialog.getOpenFileName(self, "Please select XML file", ".")                
                if (xmlfilename != ""):
                        # if the file is xml file
                        if (xmlfilename[-3:] in ['xml']):
                                rectangles = []
                                updateant = []
                                self.urstacks = []                                
                                #tree = ET.parse(xmlfilename)
                                #root = tree.getroot()
                                import xml.dom.minidom
                                xml = xml.dom.minidom.parse(str(xmlfilename)) 
                                xmlstring = xml.toprettyxml()
                                bufferedR = StringIO.StringIO(xmlstring)
                                frameindex = 0
                                objectperframe = 1                                
                                intindex = 0
                                while True:
                                        strings = bufferedR.readline()
                                        if (strings == ''):
                                                break
                                        if "frame number" in strings:                                               
                                                
                                                # get numbers only, (i.e last element from the string)
                                                str2 = strings.split("=")[-1]
                                                str3 = str2.split("\'",1)[-1]
                                                #frame number
                                                aframe = str3.split("\'",1)[0]
                                                aframe = aframe.replace("\'", "")
                                                aframe = aframe.replace(">", "")
                                                aframe = aframe.replace("<", "") 
                                                aframe = aframe.replace("\"", "")
                                                aframe = aframe.replace("/", "")
                                                frameindex = int(aframe)
                                                intindex = frameindex-1
                                                # 255 is the maximum line of the xml file (assumed that 50 datasets are given)
                                                #for x in range(0, 255):
                                                        #strings2 = bufferedR.readline()
                                                        
                                        if "boxinfo" in strings:
                                                
                                                # y
                                                str2 = strings.split(" ")[-1]
                                                stry = str2.split("=")[-1]
                                                stry = stry.replace("\'", "")
                                                stry = stry.replace(">", "")
                                                stry = stry.replace("<", "") 
                                                stry = stry.replace("\"", "")
                                                stry = stry.replace("/", "")                                                
                                                #print stry
                                                # x
                                                str3 = strings.split(" ")[-2]
                                                strx = str3.split("=")[-1]
                                                strx = strx.replace("\'", "")
                                                strx = strx.replace(">", "")
                                                strx = strx.replace("<", "") 
                                                strx = strx.replace("\"", "")
                                                strx = strx.replace("/", "")    
                                                #print strx
                                                # width
                                                str4 = strings.split(" ")[-3]
                                                strw = str4.split("=")[-1]
                                                strw = strw.replace("\'", "")
                                                strw = strw.replace(">", "")
                                                strw = strw.replace("<", "") 
                                                strw = strw.replace("\"", "")
                                                strw = strw.replace("/", "")    
                                                #print strw
                                                # height
                                                str5 = strings.split(" ")[-4]
                                                strh = str5.split("=")[-1]
                                                strh = strh.replace("\'", "")
                                                strh = strh.replace(">", "")
                                                strh = strh.replace("<", "") 
                                                strh = strh.replace("\"", "")
                                                strh = strh.replace("/", "")    
                                                #print strh
                                

                                                #framenum.append(aframe)  
                                                #print aframe                                                
                                                intx = int(strx)
                                                inty = int(stry)
                                                intw = int(strw)
                                                inth = int(strh)
                                                
                                                #print str(intindex) + "  "+str(inty)+ "  "+str(intx)+ "  "+str(intw)+ "  "+str(inth)                                                            
                                                rects = []
                                                try:
                                                        command = add(intindex, (intx,inty,intw,inth), "Add a rectangle")                                                
                                                        self.urstacks[intindex].push(command)                                           
                                                        updateant[intindex] = True
                                                except:                                                        
                                                        rects.append((intx, inty, intw, inth))
                                                        rectangles.append(rects)
                                                
                                                uraction.append([False,False])
                                                updateant.append(False)
                                                self.stack = QtGui.QUndoStack(self)
                                                self.urstacks.append(self.stack)                                                
                                                if self.pic2.pixmap():  
                                                        self.pic2.repaint()                               
                                
                                xmlimported = 1
                                
                        # if the file is not xml file
                        else:
                                QMessageBox.about(self, "import XML file", "The file is not xml file, please import a xml file.")
                                xmlfilename = QtGui.QFileDialog.getOpenFileName(self, "Please select XML file", ".")
        else:
             QMessageBox.about(self, "import XML file", "Please import image frames first!")   
    
    # Update XML File button
    def button6(self):      
        sender = self.sender()        
        dataset = ET.Element("dataset")
        frameinfo = ET.SubElement(dataset, "frameInformation")
        numobjects = 1       
        # loop for each frame.        
        for x in range(0, maxframes):
                numtoadd = x+1
                ET.SubElement(frameinfo, "frame", number="%d"%numtoadd)
                # if the x index exists in the rectangle list
                if (0 <= x) and (x < len(rectangles)):
                        # loop for each rectangles (i.e objects). For example, if there are 3 rectangles, there should be 3 objects.                                               
                        for (i,j,k,m) in rectangles[x]:
                                object1 = ET.SubElement(frameinfo, "object", name="Robot %d"%numobjects,id="0%d"%numobjects)
                                centx = i+(0.5*m)
                                centy = j+(0.5*k)
                                ET.SubElement(object1, "boxinfo", x="%d"%i,y="%d"%j,height="%d"%m,width="%d"%k)
                                ET.SubElement(object1, "centroid",x="%d"%centx,y="%d"%centy)
                                numobjects = numobjects + 1
                # reset the number of object to 1, for the next frame
                numobjects = 1
                
        # if xml file is imported, update xml file with that location
        if (xmlimported == 1):
                QMessageBox.about(self, "update XML file", "The xml file" +xmlfilename+"is updated. \n Please wait a minute.")
                tree = ET.ElementTree(dataset)
                tree.write(xmlfilename)                
                
        # if there is no xml file, create a new one and ask folder to save.
        else:
                QMessageBox.about(self, "update XML file", "no xml file is imported. Please select location to save and wait a minute.")
                filetosave = QtGui.QFileDialog.getSaveFileName(self, "Please select XML file", ".") 
                tree = ET.ElementTree(dataset)
                tree.write(filetosave)                
                
                    
    # Exit button
    def button7(self):      
        sender = self.sender()
        sys.exit()

        
class drag(QtGui.QUndoCommand):
        global rectangles
        def __init__(self, index, prev, nexts, description):
                super(drag, self).__init__(description)
                self.currentbox = rectangles[index]
                self.prevbox = prev
                self.nextbox = nexts

        def redo(self):
                try:
                        self.currentbox[self.currentbox.index(self.prevbox)] = self.nextbox

                except ValueError:
                        undoredo = 0
                
        def undo(self):
                try:
                        self.currentbox[self.currentbox.index(self.nextbox)] = self.prevbox

                except ValueError:
                        undoredo = 0
                        
class resize(QtGui.QUndoCommand):
        global rectangles
        def __init__(self, index, prev, nexts, description):
                super(resize, self).__init__(description)
                self.currentbox = rectangles[index]
                self.prevbox = prev
                self.nextbox = nexts

        def redo(self):
                try:
                        self.currentbox[self.currentbox.index(self.prevbox)] = self.nextbox

                except ValueError:
                        undoredo = 0
                
        def undo(self):
                try:
                        self.currentbox[self.currentbox.index(self.nextbox)] = self.prevbox

                except ValueError:
                        undoredo = 0 

class add(QtGui.QUndoCommand):
        global rectangles
        def __init__(self, index, rectangle, description):
                super(add, self).__init__(description)
                self.currentbox = rectangles[index]
                self.rectangle = rectangle

        def redo(self):
                self.currentbox.append(self.rectangle)
                
        def undo(self):
                self.currentbox.pop()

        
def main():
    app = QtGui.QApplication(sys.argv)
    ex = ICTProject()
    sys.exit(app.exec_())            

main()

