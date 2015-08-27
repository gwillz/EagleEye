# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import QPushButton
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QEvent

class HoverButton(QPushButton):
    hovered = pyqtSignal(bool, name="hovered")
    
    def __init__(self, parent):
        QPushButton.__init__(self, parent)
        
    def event(self, ev):
        if ev.type() == QEvent.HoverEnter:
            ev.accept()
            self.hovered.emit(True)
            return True
        elif ev.type() == QEvent.HoverLeave:
            ev.accept()
            self.hovered.emit(False)
            return False
        else:
            return QPushButton.event(self, ev)