# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import QLineEdit, QMouseEvent, QGraphicsDropShadowEffect, QColor
from PyQt4.QtCore import pyqtSlot, pyqtSignal

class HighlightEdit(QLineEdit):
    clicked = pyqtSignal(name='clicked')
    
    def __init__(self, parent):
        QLineEdit.__init__(self, parent)
        self._highlight_effect = QGraphicsDropShadowEffect(self)
        self._highlight_effect.setOffset(0.0)
        self._highlight_effect.setBlurRadius(5.0)
        self._highlight_effect.setColor(QColor(50, 50, 200))
        self.setGraphicsEffect(self._highlight_effect)
        self._highlight_effect.setEnabled(False)
        
    def mouseDoubleClickEvent(self, ev):
        ev.accept()
        self.clicked.emit()
    
    @pyqtSlot(bool)
    def highlight(self, val):
        self._highlight_effect.setEnabled(val)
        