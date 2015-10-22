# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class SaveOptionsDialog(QDialog):
    def __init__(self, parent, edit_fields):
        QDialog.__init__(self, parent)
        self.edit_fields = edit_fields
        self.ui = uic.loadUi('custom_widgets/save_options.ui', self)
        
        # top-level/children toggle rules
        self.calibration.toggled.connect(self.check_children)
        self.trainer_set.toggled.connect(self.check_children)
        self.dataset_mov.toggled.connect(self.check_children)
        self.dataset_check.toggled.connect(self.check_children)
        
        # preset buttons
        self.ui.everything_button.clicked.connect(self.preset_everything)
        self.ui.novideos_button.clicked.connect(self.preset_novideos)
        self.ui.typical_button.clicked.connect(self.preset_typical)
        self.ui.training_button.clicked.connect(self.preset_training)
        self.ui.minimal_button.clicked.connect(self.preset_minimal)
        
        novideo_slot = lambda: self.ui.novideos_button.setChecked(False)
        self.ui.dataset_mov.clicked.connect(novideo_slot)
        self.ui.trainer_mov.clicked.connect(novideo_slot)
        self.ui.comparison.clicked.connect(novideo_slot)
        self.ui.everything_button.clicked.connect(novideo_slot)
        self.ui.typical_button.clicked.connect(novideo_slot)
        self.ui.minimal_button.clicked.connect(novideo_slot)
        
        # load all top-level fields
        for i in ["calibration", "trainer_set", "dataset_mov", 
                  "dataset_map", "dataset_ann", "evaluation", "comparison"]:
            if i in edit_fields:
                self.ui.__dict__[i].setEnabled(True)
        
        # enable top-level dataset if children exist
        if self.ui.dataset_map.isEnabled() \
                or self.ui.dataset_ann.isEnabled():
            self.ui.dataset_check.setEnabled(True)
            self.ui.dataset_check.setChecked(True)
        
        # now toggle everything!
        self.ui.everything_button.click()
    
    # this is called whenever a top-level check is toggled
    # it will enable/disable child checks
    @pyqtSlot(bool)
    def check_children(self, val):
        children_fields = []
        if self.sender() == self.ui.calibration:
            children_fields = ["chessboards"]
        
        elif self.sender() == self.ui.trainer_set:
            children_fields = ["trainer_csv",
                               "trainer_mov",
                               "trainer_map"]
        
        elif self.sender() == self.ui.dataset_mov:
            children_fields = ["vicondata"]
        
        elif self.sender() == self.ui.dataset_check:
            children_fields = ["dataset_map",
                               "dataset_ann"]
        
        for i in children_fields:
            if i in self.edit_fields \
                    and i in self.ui.__dict__:
                self.ui.__dict__[i].setEnabled(val)
    
    @pyqtSlot()
    def preset_everything(self):
        # always toggle top-level checks first, then children 
        # because check_children will need to resolve first
        self.toggle_these(["calibration", "trainer_set", "dataset_mov", "dataset_map",
                           "dataset_ann", "evaluation", "comparison",
                           "chessboards", "trainer_csv", "trainer_mov", 
                           "trainer_map", "vicondata"], True)
        
    @pyqtSlot(bool)
    def preset_novideos(self, val):
        self.toggle_these(["trainer_mov", "dataset_mov", "comparison"], not val)
    
    @pyqtSlot()
    def preset_typical(self):
        self.toggle_these(["chessboards", "trainer_csv", "trainer_mov", 
                           "trainer_map", "comparison"], False)
        self.toggle_these(["calibration", "trainer_set", "dataset_mov", 
                           "vicondata", "dataset_map", "dataset_ann", "evaluation"], True)
        
    @pyqtSlot()
    def preset_minimal(self):
        self.toggle_these(["chessboards", "calibration", "trainer_csv", "trainer_mov", 
                           "trainer_map", "trainer_set", "comparison", "evaluation"], False)
        self.toggle_these(["dataset_mov", "vicondata", "dataset_map", "dataset_ann"], True)
    
    @pyqtSlot()
    def preset_training(self):
        self.toggle_these(["chessboards", "calibration", "vicondata", "dataset_mov", 
                           "dataset_map", "dataset_ann", "comparison", "evaluation"], False)
        self.toggle_these(["trainer_set", "trainer_csv", "trainer_mov", "trainer_map"], True)
    
    
    @pyqtSlot()
    def toggle_these(self, checkboxes, val):
        # dataset_check is special (doesn't exist in edit_fields)
        self.ui.dataset_check.setChecked(\
                                    "dataset_ann" in checkboxes \
                                    or "dataset_map" in checkboxes)
        
        # toggle if available and enabled
        for i in checkboxes:
            if i in self.edit_fields \
                    and i in self.ui.__dict__:
                self.ui.__dict__[i].setChecked(val)
    
    # return a dict of toggled fields with the respective input values
    def checked_fields(self):
        return_fields = {}
        
        for k in self.edit_fields:
            if k in self.ui.__dict__ \
                    and self.ui.__dict__[k].isEnabled() \
                    and self.ui.__dict__[k].isChecked():
                return_fields[k] = self.edit_fields[k]
        
        return return_fields


if __name__ == "__main__":
    app = QApplication([])
    
    edit_fields = {
            "calibration": "",
            "chessboards": "",
            "trainer_set": "",
            "trainer_csv": "",
            "trainer_mov": "",
            "trainer_map": "",
            "dataset_mov": "",
            "vicondata": "",
            "dataset_map": "",
            "dataset_ann": "",
            "evaluation": "",
            "comparison": ""}
    
    w = QMainWindow()
    dialog = SaveOptionsDialog(w, edit_fields)
    exit(dialog.exec_())
    
