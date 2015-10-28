# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from eagleeye import marker_tool

class MarkerDialog(QDialog):
    def __init__(self, parent, path, marks):
        QDialog.__init__(self, parent)
        uic.loadUi('custom_widgets/marker_dialog.ui', self)
        
        self.path = path
        self.markin_edit.setValue(marks[0])
        self.markout_edit.setValue(marks[1])
        self.markin_edit.setFocus()
        
        self.run_button.clicked.connect(self.run_marker)
    
    @pyqtSlot()
    def run_marker(self):
        QMessageBox.information(self, "Marker Tool", 
                "Use the Left and Right arrow keys to navigate the video.\n"
                "Find the first 'flash' frame and mark it with the '[' key.\n"
                "Continue navigation until the second flash, mark it with the ']' key.\n"
                "When complete, press Enter.")
        
        stat, mark_in, mark_out = marker_tool(self.path)
        
        if stat:
            self.markin_edit.setValue(mark_in)
            self.markout_edit.setValue(mark_out)
    
    def marks(self):
        return (self.markin_edit.value(), self.markout_edit.value())