# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class ConsoleText(QPlainTextEdit):
    following = pyqtSignal(bool, name="following")
    stateChanged = pyqtSignal(QProcess.ProcessState, name="stateChanged")
    
    def __init__(self, parent):
        QPlainTextEdit.__init__(self, parent)
        
        #settings
        self.process = QProcess()
        self.setFollow(True)
        
        #events
        self.verticalScrollBar().sliderPressed.connect(self.stopFollowing)
        self.process.readyReadStandardOutput.connect(self.readProcess)
        self.process.readyReadStandardError.connect(self.readProcess)
        self.process.stateChanged.connect(self.triggerStateChanged)
    
    @pyqtSlot(str, list)
    def start(self, executable, args):
        print "launching: ", QStringList(args).join(" ")
        self.process.start(executable, args)
    
    @pyqtSlot()
    def kill(self):
        self.process.kill()
    
    @pyqtSlot()
    def stopFollowing(self):
        self.setFollow(False)
    
    @pyqtSlot(QProcess.ProcessState)
    def triggerStateChanged(self, state):
        self.stateChanged.emit(state)
    
    @pyqtSlot(bool)
    def setFollow(self, follow):
        self.follow_console = follow
        
        at = self.verticalScrollBar().maximum() if follow else self.verticalScrollBar().value()
        self.verticalScrollBar().setSliderPosition(at)
        
        self.following.emit(follow)
    
    def wheelEvent(self, event):
        self.setFollow(False)
        QPlainTextEdit.wheelEvent(self, event)
    
    @pyqtSlot()
    def readProcess(self):
        self.appendPlainText(QString(self.process.readAllStandardOutput()))
        
        if self.follow_console:
            self.verticalScrollBar().setSliderPosition(
                self.verticalScrollBar().maximum())
    