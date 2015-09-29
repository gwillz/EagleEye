# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class SaveOptionsDialog(QDialog):
    def __init__(self, parent, edit_fields):
        QDialog.__init__(self, parent)
        self.edit_fields = edit_fields
        self.ui = uic.loadUi('custom_widgets/save_options.ui', self)
        
        # load available fields
        if "calibration" in edit_fields:
            self.ui.calibration.setEnabled(True)
            self.ui.calibration.setChecked(True)
            
            # only enable optionals if parents exist
            if "chessboards" in edit_fields:
                self.ui.chessboards.setEnabled(True)
                self.ui.chessboards.setChecked(True)
        
        if "trainer_set" in edit_fields:
            self.ui.trainer_set.setEnabled(True)
            self.ui.trainer_set.setChecked(True)
            
            for i in ["trainer_csv", "trainer_mov", "trainer_map"]:
                if i in edit_fields:
                    self.ui.__dict__[i].setEnabled(True)
                    self.ui.__dict__[i].setChecked(True)
        
        if "dataset_mov" in edit_fields:
            self.ui.dataset_mov.setEnabled(True)
            self.ui.dataset_mov.setChecked(True)
            
            if "vicondata" in edit_fields:
                self.ui.vicondata.setEnabled(True)
                self.ui.vicondata.setChecked(True)
        
        for i in ["dataset_map", "dataset_ann", "evaluation", "comparison"]:
            if i in edit_fields:
                self.ui.__dict__[i].setEnabled(True)
                self.ui.__dict__[i].setChecked(True)
        
        # enable dataset group checkbox
        if self.ui.dataset_map.isEnabled() \
                or self.ui.dataset_ann.isEnabled():
            self.ui.dataset_check.setEnabled(True)
            self.ui.dataset_check.setChecked(True)
        
        # check-enable rules
        self.calibration.toggled.connect(self.check_children)
        self.trainer_set.toggled.connect(self.check_children)
        self.dataset_mov.toggled.connect(self.check_children)
        self.dataset_check.toggled.connect(self.check_children)
        
        # presets
        self.ui.everything_button.clicked.connect(self.preset_everything)
        self.ui.novideos_button.clicked.connect(self.preset_novideos)
        self.ui.typical_button.clicked.connect(self.preset_typical)
        self.ui.minimal_button.clicked.connect(self.preset_minimal)
        
        self.ui.dataset_mov.clicked.connect(lambda: self.ui.novideos_button.setChecked(False))
        self.ui.trainer_mov.clicked.connect(lambda: self.ui.novideos_button.setChecked(False))
        self.ui.comparison.clicked.connect(lambda: self.ui.novideos_button.setChecked(False))
    
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
        # check all parent toggles
        self.toggle_these(["calibration", "trainer_set", "dataset_mov", "dataset_map",
                           "dataset_ann", "evaluation", "comparison",
                           "chessboards", "trainer_csv", "trainer_mov", 
                           "trainer_map", "vicondata"], True)
        
    @pyqtSlot(bool)
    def preset_novideos(self, val):
        self.toggle_these(["trainer_mov", "dataset_mov", "comparison"], not val)
    
    @pyqtSlot()
    def preset_typical(self):
        self.toggle_these(["calibration", "trainer_set", "dataset_mov", 
                           "vicondata", "dataset_map", "dataset_ann", "evaluation"], True)
        self.toggle_these(["chessboards", "trainer_csv", "trainer_mov", 
                           "trainer_map", "comparison"], False)
        
    @pyqtSlot()
    def preset_minimal(self):
        self.toggle_these(["dataset_mov", "vicondata", "dataset_map", "dataset_ann"], True)
        self.toggle_these(["chessboards", "calibration", "trainer_csv", "trainer_mov", 
                           "trainer_map", "trainer_set", "comparison", "evaluation"], False)
    
    @pyqtSlot()
    def toggle_these(self, checkboxes, val):
        for i in checkboxes:
            if i in self.edit_fields \
                    and i in self.ui.__dict__ \
                    and self.ui.__dict__[i].isEnabled():
                self.ui.__dict__[i].setChecked(val)
    
    # return a dict of checked fields with the respective input values
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
    
