# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QMessageBox, qApp
from PyQt4.QtCore import QProcess, pyqtSlot
import sys, os, glob, datetime, xml.etree.ElementTree as ET, tempfile, zipfile, shutil
from elementtree.SimpleXMLWriter import XMLWriter
from custom_widgets import *
import capture_ui, training_ui, calibrate_ui, mapping_ui

class Wizard(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi('ui/wizard.ui', self)
        
        # process for annotation tool
        self.annotation_process = QProcess()
        
        # current directory, save status
        self.saved = True # new session is empty, doesn't need saving
        self.save_path = None
        self.save_date = None
        self._original_title = self.windowTitle() # for newaction
        self._working_title = self.windowTitle()
        
        # save/open events
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_As.triggered.connect(self.save_file_as)
        self.actionOpen.triggered.connect(self.open_file)
        self.actionNew.triggered.connect(self.clear_data)
        
        # about events
        self.actionAbout.triggered.connect(self.about)
        self.actionAbout_QT.triggered.connect(qApp.aboutQt)
        
        # save checks
        self.dataset_name_edit.textChanged.connect(self.update_working_title)
        self.dataset_name_edit.editingFinished.connect(self.set_unsaved)
        self.chessboard_edit.editingFinished.connect(self.set_unsaved)
        self.trainer_csv_edit.editingFinished.connect(self.set_unsaved)
        self.trainer_mov_edit.editingFinished.connect(self.set_unsaved)
        self.calibration_edit.editingFinished.connect(self.set_unsaved)
        self.trainer_xml_edit.editingFinished.connect(self.set_unsaved)
        self.vicondata_edit.editingFinished.connect(self.set_unsaved)
        self.vicondata_edit.editingFinished.connect(self.set_unsaved)
        self.dataset_mov_edit.editingFinished.connect(self.set_unsaved)
        self.dataset_mov_edit.editingFinished.connect(self.set_unsaved)
        self.dataset_map_edit.editingFinished.connect(self.set_unsaved)
        self.dataset_ann_edit.editingFinished.connect(self.set_unsaved)
        
        # editing check/enable events
        self.chessboard_edit.editingFinished.connect(self.load_chessboards)
        self.trainer_csv_edit.editingFinished.connect(self.check_trainer_enable)
        self.trainer_mov_edit.editingFinished.connect(self.check_trainer_enable)
        self.calibration_edit.editingFinished.connect(self.check_mapping_enable)
        self.trainer_xml_edit.editingFinished.connect(self.check_mapping_enable)
        self.vicondata_edit.editingFinished.connect(self.load_vicondata)
        self.vicondata_edit.editingFinished.connect(self.check_mapping_enable)
        self.dataset_mov_edit.editingFinished.connect(self.check_annotate_enable)
        self.dataset_mov_edit.editingFinished.connect(self.check_compare_enable)
        self.dataset_map_edit.editingFinished.connect(self.check_compare_enable)
        self.dataset_ann_edit.editingFinished.connect(self.check_compare_enable)
        
        # launch menu events
        self.actionCalibration_Tool.triggered.connect(self.launch_calibration)
        self.actionTraining_Tool.triggered.connect(self.launch_training)
        self.actionCapture_Tool.triggered.connect(self.launch_capture)
        self.actionMapping_Tool.triggered.connect(self.launch_mapping)
        self.actionAnnotation_Tool.triggered.connect(self.launch_annotate)
        self.actionComparison_Tool.triggered.connect(self.launch_comparison)
        
        # buttons and junk
        self.chessboard_button.clicked.connect(self.chessboard_extract)
        self.chessboard_edit.clicked.connect(self.browse_chessboards)
        self.calibration_button.clicked.connect(self.run_calibration)
        self.calibration_edit.clicked.connect(self.browse_calibration)
        
        self.trainer_csv_edit.clicked.connect(self.browse_trainer_csv)
        self.trainer_mov_button.clicked.connect(self.browse_trainer_mov)
        self.trainer_mov_edit.clicked.connect(self.browse_trainer_mov)
        self.trainer_xml_edit.clicked.connect(self.browse_trainer_xml)
        
        self.capture_button.clicked.connect(self.run_capture)
        self.vicondata_edit.clicked.connect(self.browse_vicondata)
        self.dataset_mov_button.clicked.connect(self.browse_vicon_mov)
        self.dataset_mov_edit.clicked.connect(self.browse_vicon_mov)
        
        self.mapping_button.clicked.connect(self.run_mapping)
        self.dataset_map_edit.clicked.connect(self.browse_mapping_data)
        
        self.annotation_button.clicked.connect(self.run_annotation)
        self.dataset_ann_edit.clicked.connect(self.browse_annotation_data)
    
    
    @pyqtSlot()
    def set_unsaved(self):
        self.saved = False
        self.setWindowTitle(self._working_title + "*")
    
    @pyqtSlot('QString')
    def update_working_title(self, text):
        self._working_title = "{} - {}".format(self._original_title, text)
        self.setWindowTitle(self._working_title)
    
    ## save, open, load stuff
    @pyqtSlot()
    def save_file(self):
        # only save edited
        if not self.saved:
            # open save_as if not previously saved
            if self.save_path is None:
                self.save_file_as()
            else:
                # check valid name first
                name = self.dataset_name_edit.text()
                if name == "":
                    QMessageBox.warning(self, "Error Saving File", "The name parameter was not specified")
                    return
                
                self.savezip(self.save_path, name)
            
    @pyqtSlot()
    def save_file_as(self):
        # check valid name first
        name = self.dataset_name_edit.text()
        if name == "":
            QMessageBox.warning(self, "Error Saving File", "The name parameter was not specified")
            return
                
        # open file dialog
        path = QFileDialog.getSaveFileName(self, "Save Dataset As...", "./", "Zip file (*.zip)")
        if path != "":
            self.savezip(path, name)
    
    @pyqtSlot()
    def open_file(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset Zip", "./", "Zip file (*.zip)")
        if path != "":
            self.openzip(path)
    
    def savezip(self, path, name):
        name = str(name)
        path = str(path)
        temp_date = datetime.date.today().strftime("%Y-%m-%d")
        
        # add zip extension if not already present
        if not path.lower().endswith(".zip"):
            path += ".zip"
        
        # create zipfile
        with zipfile.ZipFile(path, 'w') as zipper:
            
            # create header XML
            header_file = tempfile.NamedTemporaryFile(delete=False)
            w = XMLWriter(header_file)
            w.declaration()
            doc = w.start('datasetHeader', name=name, date=temp_date)
            
            # write stuff
            # calibration xml
            file_path = str(self.calibration_edit.text())
            if file_path != "" and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                
                w.start("calibration")
                w.element("xml", file_name)
                
                # optional elements - dependant on calib xml
                # write chessboard folder
                file_path = str(self.chessboard_edit.text())
                if file_path != "" and os.path.exists(file_path) and len(self.chessboards) > 0:
                    w.start("chessboards", path="chessboards/", size=str(len(self.chessboards)))
                    
                    for c in self.chessboards:
                        file_name = os.path.basename(c)
                        zipper.write(str(c), "chessboards/" + file_name)
                        
                        w.element("file", file_name)
                    
                    w.end() # chessboards
                w.end() # calibration
            
            # trainer xml
            file_path = str(self.trainer_xml_edit.text())
            if file_path != "" and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                
                w.start("training")
                w.element("xml", file_name)
                
                # optional elements - dependant on trainer xml
                # trainer video
                file_path = str(self.trainer_mov_edit.text())
                if file_path != "" and os.path.isfile(file_path):
                    
                    file_name = os.path.basename(file_path)
                    zipper.write(file_path, file_name)
                    
                    w.element("video", file_name)
                
                # trainer CSV
                file_path = str(self.trainer_csv_edit.text())
                if file_path != "" and os.path.isfile(file_path):
                    
                    file_name = os.path.basename(file_path)
                    zipper.write(file_path, file_name)
                    w.element("csv", file_name)
                    
                w.end() # training
                
            # raw video
            file_path = str(self.dataset_mov_edit.text())
            if file_path != "" and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                
                w.start("rawData")
                w.element("video", file_name)
                
                # write vicon folder - dependant on video_file
                file_path = str(self.vicondata_edit.text())
                if file_path != "" and os.path.exists(file_path) and len(self.vicondata) > 0:
                    w.start("vicon", path="vicondata/", size=str(len(self.vicondata)))
                    
                    for v in self.vicondata:
                        file_name = os.path.basename(v)
                        zipper.write(str(v), "vicondata/" + file_name)
                        w.element("file", file_name)
                    
                    w.end() # vicon
                w.end() # rawData
                
            # comparison xml
            file_path = str(self.evaluation_edit.text())
            if file_path != "" and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                w.element("evaluation", file_name)
                
            # write datasets group
            w.start("datasets")
            
            file_path = str(self.dataset_map_edit.text())
            if file_path != "" and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                w.element("mapping", file_name)
                
            file_path = str(self.dataset_ann_edit.text())
            if file_path != "" and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                w.element("annotation", file_name)
            
            w.end() # datasets
            w.close(doc)
            
            
            # write header to zipper
            header_file.close()
            zipper.write(header_file.name, "header.xml")
        
        self.save_date = temp_date
        self.save_path = path
        self.saved = True
        self.setWindowTitle(self._working_title)
        
    def openzip(self, path):
        # test file valid-ness
        if not zipfile.is_zipfile(str(path)):
            QMessageBox.error(self, "Not a valid dataset", "This is not a zip file or is corrupt")
            return
        
        with zipfile.ZipFile(str(path), 'r') as zipper:
            # test for header file
            if 'header.xml' not in zipper.namelist():
                QMessageBox.error(self, "Not a valid dataset", "The header.xml file is missing.")
                return
            
            # create a temporary path (delete if present)
            temp_dir = os.path.join(tempfile.gettempdir(), "eagleeye")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # extract header, open and parse stuff
            zipper.extract("header.xml", temp_dir)
            tree = ET.parse(os.path.join(temp_dir, "header.xml"))
            root = tree.getroot()
            
            # more tests
            if len(root) == 0:
                QMessageBox.error(self, "Not a valid dataset", "The header.xml file is corrupt.")
                return
            
            # load into text fields
            self.dataset_name_edit.setText(root.attrib["name"])
            self.save_date = root.attrib["date"]
            
            calib = root.find("calibration")
            training = root.find("trainer")
            raw_data = root.find("rawData")
            evaluation = root.find("evaluation")
            mapping = root.find("datasets/mapping")
            annotation = root.find("datasets/annotation")
            
            if calib:
                self.calibration_edit.setText(os.path.join(temp_dir, calib.find("xml").text))
                if calib.find("chessboards"):
                    self.chessboard_edit.setText(os.path.join(temp_dir, calib.find("chessboards").attrib["path"]))
            
            if training:
                if training.find("xml"):
                    self.training_xml_edit.setText(os.path.join(temp_dir, training.find("xml").text))
                    if training.find("csv"):
                        self.training_csv_edit.setText(os.path.join(temp_dir, training.find("csv").text))
                    if training.find("video"):
                        self.training_mov_edit.setText(os.path.join(temp_dir, training.find("video").text))
            
            if raw_data:
                if raw_data.find("video"):
                    self.dataset_mov_edit.setText(os.path.join(temp_dir, raw_data.find("video").text))
                    if calib.find("vicon"):
                        self.vicondata_edit.setText(os.path.join(temp_dir, calib.find("vicon").attrib["path"]))
            
            if evaluation:
                self.evaluation_edit.setText(os.path.join(temp_dir, evaluation.text))
            
            if mapping:
                self.dataset_map_edit.setText(os.path.join(temp_dir, mapping.text))
            
            if annotation:
                self.annotation_edit.setText(os.path.join(temp_dir, annotation.text))
            
            # now extract everything else
            zipper.extractall(temp_dir)
        
        self.save_path = path
        self.saved = True
        self.setWindowTitle(self._original_title)
        self.load_vicondata()
        self.load_chessboards()
    
    @pyqtSlot()
    def clear_data(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Wait a second!")
        dialog.setText("You haven't saved this session,\nare you sure?")
        dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Save)
        res = dialog.exec_()
        
        if res == QMessageBox.RejectRole:
            return False
        elif res == QMessageBox.AcceptRole:
            self.save_file()
        else: # DesctructiveRole
            pass
        
        self.saved = False
        self.save_path = None
        self.save_date = None
        
        self.dataset_name_edit.clear()
        self.chessboard_edit.clear()
        self.calibration_edit.clear()
        self.trainer_csv_edit.clear()
        self.trainer_mov_edit.clear()
        self.trainer_xml_edit.clear()
        self.vicondata_edit.clear()
        self.dataset_mov_edit.clear()
        self.dataset_map_edit.clear()
        self.dataset_ann_edit.clear()
        self.evaluation_edit.clear()
        
        # reset folder storage dealios
        self.load_chessboards()
        self.load_vicondata()
        
        return True
    
    ## button event slots
    @pyqtSlot()
    def run_calibration(self):
        self.launch_calibration(
                        {'args': self.chessboards,
                         'output': self.default_name('chessboard_edit')})
        
        # after successful calib
        #self.check_mapping_enable()
    
    @pyqtSlot()
    def run_capture_training(self):
        self.launch_capture()
                        #{'args': self.chessboards,
                         #'output': self.default_name('chessboard_edit')})
        
        # after successful training capture
        #self.check_trainer_enable()
    
    @pyqtSlot()
    def run_training(self):
        self.launch_training()
                        #{'args': self.chessboards,
                        # 'output': self.default_name('chessboard_edit')})
        
        # after successful training
        #self.check_mapping_enable()
    
    @pyqtSlot()
    def run_capture(self):
        self.launch_capture()
                        #{'args': self.chessboards,
                         #'output': self.default_name('chessboard_edit')})
        
        # after successful capture
        #self.load_vicondata()
    
    @pyqtSlot()
    def run_mapping(self):
        self.launch_mapping()
                        #{'args': self.chessboards,
                        # 'output': self.default_name('chessboard_edit')})
        
        # after successful mapping
        #self.check_comparison_enable()
    
    @pyqtSlot()
    def run_annotation(self):
        self.launch_annotate()
                        #{'args': self.chessboards,
                        # 'output': self.default_name('chessboard_edit')})
        
        # after successful annotation
        #self.check_comparison_enable()
    
    @pyqtSlot()
    def run_comparison(self):
        self.launch_comparison()
                        #{'args': self.chessboards,
                        # 'output': self.default_name('chessboard_edit')})
        
        # after - maybe prompt to save the dataset to file?
        
    @pyqtSlot()
    def chessboard_extract(self):
        print "extractor tool"
        #self.load_chessboards()
        
    @pyqtSlot()
    def browse_chessboards(self):
        path = QFileDialog.getExistingDirectory(self, "Folder of Chessboard Images", self.chessboard_edit.text())
        if path != "":
            self.chessboard_edit.setText(path)
            self.load_chessboards()
        
    @pyqtSlot()
    def browse_calibration(self):
        path = QFileDialog.getOpenFileName(self, "Open Calibration XML", self.calibration_edit.text(), "XML File (*.xml)")
        if path != "":
            self.calibration_edit.setText(path)
            self.check_mapping_enable()
        
    @pyqtSlot()
    def browse_trainer_csv(self):
        path = QFileDialog.getOpenFileName(self, "Open Training CSV", 
                                           self.trainer_csv_edit.text(), "CSV File (*.csv)")
        if path != "":
            self.trainer_csv_edit.setText(path)
            self.check_trainer_enable()
        
    @pyqtSlot()
    def browse_trainer_mov(self):
        path = QFileDialog.getOpenFileName(self, "Open Training Video", 
                                           self.trainer_mov_edit.text(), 
                                           "Video File (*.mov;*.avi;*.mp4);;All Files (*.*)")
        if path != "":
            self.trainer_mov_edit.setText(path)
            self.check_trainer_enable()
        
    @pyqtSlot()
    def browse_trainer_xml(self):
        path = QFileDialog.getOpenFileName(self, "Open Training XML", 
                                           self.trainer_xml_edit.text(), "XML File (*.xml)")
        if path != "":
            self.trainer_xml_edit.setText(path)
            self.check_mapping_enable()
    
    @pyqtSlot()
    def browse_vicondata(self):
        path = QFileDialog.getExistingDirectory(self, "Folder of Vicon CSV files", 
                                                self.vicondata_edit.text())
        if path != "":
            self.vicondata_edit.setText(path)
            self.load_vicondata()
        
    @pyqtSlot()
    def browse_vicon_mov(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset Video", 
                                           self.dataset_mov_edit.text(), 
                                           "Video File (*.mov;*.avi;*.mp4);;All Files (*.*)")
        if path != "":
            self.dataset_mov_edit.setText(path)
            self.check_comparison_enable()
            self.check_annotation_enable()
        
    @pyqtSlot()
    def browse_mapping_data(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset XML (Mapped)", 
                                           self.dataset_map_edit.text(), "XML File (*.xml)")
        if path != "":
            self.dataset_map_edit.setText(path)
            self.check_comparison_enable()
    
    @pyqtSlot()
    def browse_annotation_data(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset XML (Annotated)", 
                                           self.dataset_ann_edit.text(), "XML File (*.xml)")
        if path != "":
            self.dataset_ann_edit.setText(path)
            self.check_comparison_enable()
    
    ## button checker dealios (to ensure a correct pipeline workflow)
    @pyqtSlot()
    def check_trainer_enable(self):
        self.trainer_button.setEnabled(
                    self.trainer_csv_edit.text() != "" and 
                    self.trainer_mov_edit.text() != "")
    
    @pyqtSlot()
    def check_mapping_enable(self):
        self.mapping_button.setEnabled(
                    self.calibration_edit.text() != "" and 
                    self.trainer_xml_edit.text() != "" and 
                    self.vicondata_edit.text() != "")
    
    @pyqtSlot()
    def check_annotate_enable(self):
        self.annotation_button.setEnabled(
                    self.dataset_mov_edit.text() != "")
    
    @pyqtSlot()
    def check_compare_enable(self):
        self.comparison_button.setEnabled(
                    self.dataset_mov_edit.text() != "" and 
                    self.dataset_map_edit.text() != "" and 
                    self.dataset_ann_edit.text() != "")
    
    # loads directory of image paths into chessboard list
    @pyqtSlot()
    def load_chessboards(self):
        if self.chessboard_edit.text() != "":
            self.chessboards = glob.glob(os.path.join(str(self.chessboard_edit.text()), "*.jpg"))
        else:
            self.chessboards = []
        
        self.num_chessboards.setText(str(len(self.chessboards)))
        self.calibration_button.setEnabled(len(self.chessboards) > 0)
        
    # loads directory of csv paths into vicondata list
    @pyqtSlot()
    def load_vicondata(self):
        if self.vicondata_edit.text() != "":
            self.vicondata = glob.glob(os.path.join(str(self.vicondata_edit.text()), "*.csv"))
        else:
            self.vicondata = []
        
        self.num_vicondata.setText(str(len(self.vicondata)))
    
    
    ## tool launchers
    @pyqtSlot()
    def launch_capture(self, params={}):
        if 'cap' not in self.__dict__ or not self.cap.isVisible():
            self.cap = capture_ui.Capture()
            self.cap.show()
            print "capture"
        
    @pyqtSlot()
    def launch_training(self, params={}):
        if 'train' not in self.__dict__ or not self.train.isVisible():
            self.train = training_ui.Training()
            self.train.show()
            print "training"
        
    @pyqtSlot()
    def launch_mapping(self, params={}):
        if 'mapp' not in self.__dict__ or not self.mapp.isVisible():
            self.mapp = mapping_ui.Mapping()
            self.mapp.show()
            print "mapping"
        
    @pyqtSlot()
    def launch_calibration(self, params={}):
        if 'calib' not in self.__dict__ or not self.calib.isVisible():
            self.calib = calibrate_ui.Calibration()
            self.calib.show()
            print "calibration"
        
    @pyqtSlot()
    def launch_annotate(self, params={}):
        if self.annotation_process.state() == QProcess.NotRunning:
            print "annotate"
            args = ["tools/annotation.py"]
            print "launching: ", " ".join(args)
            self.annotation_process.start(sys.executable, args)
        
    @pyqtSlot()
    def launch_comparison(self, params={}):
        print "comparison"
    
    
    ## various other stuff
    def default_path(self, edit_name):
        return "{}_{}_{}".format(
                        self.dataset_name_edit.text().replace(" ", "-"), 
                        datetime.now().strftime("%m-%d"),
                        self.__dict__[edit_name].placeholderText())
    
    @pyqtSlot()
    def about(self):
        QMessageBox.about(self, "Project EagleEye", 
                                "UniSA ITMS 2015\n"
                                "Gwilyn Saunders\n"
                                "Kin Kuen Liu\n"
                                "Kim Manjung")
    
    def closeEvent(self, ev):
        if not self.saved:
            res = QMessageBox.question(self, "Wait a second!", 
                                    "You haven't save this session, are you sure?",
                                    QMessageBox.Save, QMessageBox.Discard)
            
            if res == QMessageBox.Save:
                self.save_file()
        sys.exit(0)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Wizard()
    w.show()
    sys.exit(app.exec_())