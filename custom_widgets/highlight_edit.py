# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import QLineEdit, QMouseEvent, QGraphicsDropShadowEffect, QColor, QIcon, QToolButton, QStyle
from PyQt4.QtCore import Qt, pyqtSlot, pyqtSignal

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
        
        self.clear_button = QToolButton(self)
        self.clear_button.setIcon(QIcon.fromTheme("edit-clear", QIcon("delete_icon.png")))
        self.clear_button.setCursor(Qt.ArrowCursor)
        self.clear_button.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self.clear_button.clicked.connect(self.clear)
        #self.clear_button.hide()
        
        # some padding stuff
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet("QLineEdit {{ padding-right: {}px; }} ".format(
                                        self.clear_button.sizeHint().width() + frameWidth + 1))
    
    #create a signal on doubleclick events
    def mouseDoubleClickEvent(self, ev):
        ev.accept()
        self.clicked.emit()
    
    # fix up the clear button positioning
    def resizeEvent(self, ev):
        sz = self.clear_button.sizeHint()
        
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.clear_button.move(self.rect().right() - frameWidth - sz.width(),
                        (self.rect().bottom() + 1 - sz.height())/2)
        
    # a slot for turning the graphics effect on and off
    @pyqtSlot(bool)
    def highlight(self, val):
        self._highlight_effect.setEnabled(val)
