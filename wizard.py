# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QMessageBox, qApp
from PyQt4.QtCore import QProcess, QObject, QThread, pyqtSlot, pyqtSignal
import sys, os, glob, datetime, xml.etree.ElementTree as ET, tempfile, zipfile, shutil
from elementtree.SimpleXMLWriter import XMLWriter
from custom_widgets import *

# tool imports
from vicon_capture import main as capture_main
from extract_frames import main as chess_extract_main
from stdcalib import main as calib_main
from trainer import main as trainer_main
from mapping import main as mapping_main
from compare import main as compare_main

class Wizard(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi('wizard.ui', self)
        
        # process for annotation tool
        self.annotation_process = QProcess()
        self.reset_statusbar()
        
        # current directory, save status
        self.saved = True # new session is empty, doesn't need saving
        self.save_path = None
        self.save_date = None
        self._original_title = self.windowTitle() # for newaction
        self._working_title = self.windowTitle()
        
        # config stuff
        self.config_path = "eagleeye.cfg"
        #TODO loading config files, editing and junk
        
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
        self.dataset_map_edit.editingFinished.connect(self.check_evaluate_enable)
        self.dataset_ann_edit.editingFinished.connect(self.check_evaluate_enable)
        
        # buttons and junk
        self.chessboard_button.clicked.connect(self.chessboard_extract)
        self.chessboard_edit.clicked.connect(self.browse_chessboards)
        self.calibration_button.clicked.connect(self.run_calibration)
        self.calibration_edit.clicked.connect(self.browse_calibration)
        
        self.capture_trainer_button.clicked.connect(self.run_capture_training)
        self.trainer_button.clicked.connect(self.run_training)
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
        
        self.comparison_button.clicked.connect(self.run_comparison)
        self.evaluation_button.clicked.connect(self.run_evaluation)
    
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
            training = root.find("training")
            raw_data = root.find("rawData")
            evaluation = root.find("evaluation")
            mapping = root.find("datasets/mapping")
            annotation = root.find("datasets/annotation")
            
            if calib is not None:
                self.calibration_edit.setText(os.path.join(temp_dir, calib.find("xml").text))
                if calib.find("chessboards") is not None:
                    self.chessboard_edit.setText(os.path.join(temp_dir, calib.find("chessboards").attrib["path"]))
            
            if training is not None:
                if training.find("xml") is not None:
                    self.trainer_xml_edit.setText(os.path.join(temp_dir, training.find("xml").text))
                    if training.find("csv") is not None:
                        self.trainer_csv_edit.setText(os.path.join(temp_dir, training.find("csv").text))
                    if training.find("video") is not None:
                        self.trainer_mov_edit.setText(os.path.join(temp_dir, training.find("video").text))
            
            if raw_data is not None:
                if raw_data.find("video") is not None:
                    self.dataset_mov_edit.setText(os.path.join(temp_dir, raw_data.find("video").text))
                    if raw_data.find("vicon") is not None:
                        self.vicondata_edit.setText(os.path.join(temp_dir, raw_data.find("vicon").attrib["path"]))
            
            if evaluation is not None:
                self.evaluation_edit.setText(os.path.join(temp_dir, evaluation.text))
            
            if mapping is not None:
                self.dataset_map_edit.setText(os.path.join(temp_dir, mapping.text))
            
            if annotation is not None:
                self.annotation_edit.setText(os.path.join(temp_dir, annotation.text))
            
            # now extract everything else
            zipper.extractall(temp_dir)
        
        self.save_path = path
        self.saved = True
        self.setWindowTitle(self._original_title)
        
        # run button checks
        self.load_chessboards()
        self.load_vicondata()
        self.check_trainer_enable()
        self.check_mapping_enable()
        self.check_annotate_enable()
        self.check_evaluate_enable()
        self.check_compare_enable()
    
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
        
        # re-check the button dealios
        self.load_chessboards()
        self.load_vicondata()
        self.check_trainer_enable()
        self.check_mapping_enable()
        self.check_annotate_enable()
        self.check_evaluate_enable()
        self.check_compare_enable()
        
        return True
    
    ## Runs a tool in a separate thread, if the worker is not already occupied
    def run_tool(self, tool_func, args):
        if 'worker' not in self.__dict__ or self.worker.isFinished():
            worker = ThreadWorker(tool_func, args)
            worker.finished.connect(self.reset_statusbar)
            worker.finished.connect(worker.deleteLater)
            worker.finished.connect(self.enable_tools)
            worker.destroyed.connect(self.destroy_worker)
            
            print "exec:", " ".join(args)
            worker.start()
            self.disable_tools()
        else:
            QMessageBox.warning(self, "Already running", "A tool is already running")
        
        self.worker = worker
        return self.worker
    
    def destroy_worker(self, obj):
        del self.worker
    
    ## tool launcher slots
    @pyqtSlot()
    def chessboard_extract(self):
        # browse for save path
        if self.chessboard_edit.text() == "":
            self.browse_chessboards()
        
        # get path
        output_path = str(self.chessboard_edit.text())
        if output_path == "": return
        
        # find a chessboard video
        input_path = QFileDialog.getOpenFileName(self, "Open Chessboard Video", "./", 
                                                "Video File (*.mov;*.avi;*.mp4);;All Files (*.*)")
        if input_path == "": return
        
        self.statusbar.showMessage("Running Chessboard Extractor.")
        worker = self.run_tool(chess_extract_main, ["wizard", 
                                    str(input_path),
                                    output_path,
                                    "-config", self.config_path])
        
        worker.finished.connect(self.load_chessboards)
        
    @pyqtSlot()
    def run_calibration(self):
        # browse for save path
        if self.calibration_edit.text() == "":
            path = str(QFileDialog.getSaveFileName(self, "Save Calibration XML", "./data",
                                                "XML File (*.xml)"))
            self.calibration_edit.setText(path)
        else:
            path = str(self.calibration_edit.text())
            
        # run tests
        if path == "": return
        if not path.lower().endswith(".xml"):
            path += ".xml"
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        
        self.statusbar.showMessage("Running Calibration.")
        self.run_tool(calib_main, ["wizard", 
                        "-output", path,
                        "-config", self.config_path] +\
                        self.chessboards)

    @pyqtSlot()
    def run_capture_training(self):
        # browse for save path
        if self.trainer_csv_edit.text() == "":
            path = str(QFileDialog.getSaveFileName(self, "Save Trainer CSV", "./data",
                                                    "CSV File (*.csv)"))
            self.trainer_csv_edit.setText(path)
        else:
            path = str(self.trainer_csv_edit.text())
        
        # run tests
        if path == "": return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        #TODO need to add trainer mode to vicon_capture
        self.statusbar.showMessage("Running Training Capture.")
        self.run_tool(capture_main, ["wizard", 
                        "-trainer", path,
                        "-config", self.config_path])

        
    @pyqtSlot()
    def run_training(self):
        # browse for save path
        if self.trainer_xml_edit.text() == "":
            path = str(QFileDialog.getSaveFileName(self, "Save Trainer XML", "./data",
                                                    "XML File (*.xml)"))
            self.trainer_xml_text.setText(path)
        else:
            path = str(self.trainer_xml_edit.text())
        
        # run tests
        if path == "": return
        if not path.lower().endswith(".xml"):
            path += ".xml"
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        
        
        self.statusbar.showMessage("Running Trainer.")
        self.run_tool(trainer_main, ["wizard", 
                        path,
                        str(self.trainer_csv_edit.text()),
                        str(self.trainer_xml_edit.text()),
                        "-config", self.config_path])

        
    @pyqtSlot()
    def run_capture(self):
        # browse for save path
        if self.vicondata_edit.text() == "":
            self.browse_vicondata()
        
        # get path
        path = str(self.vicondata_edit.text())
        if path == "": return
        
        self.statusbar.showMessage("Running Data Capture.")
        worker = self.run_tool(capture_main, ["wizard", 
                                "-output", path,
                                "-config", self.config_path])
        
        worker.finished.connect(self.load_vicondata)
        
    @pyqtSlot()
    def run_mapping(self):
        # browse for save path
        if self.dataset_map_edit.text() == "":
            path = str(QFileDialog.getSaveFileName(self, "Save Mapping XML", "./data",
                                                    "XML File (*.xml)"))
            self.dataset_map_edit.setText(path)
        else:
            path = str(self.dataset_map_edit.text())
        
        # run tests
        if path == "": return
        if not path.lower().endswith(".xml"):
            path += ".xml"
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        self.statusbar.showMessage("Running Mapping.")
        self.run_tool(mapping_main, ["wizard", 
                        "-calib", str(self.calibration_edit.text()),
                        "-trainer", str(self.trainer_xml_edit.text()),
                        "-output", path,
                        "-config", self.config_path] +\
                        self.vicondata)

    @pyqtSlot()
    def run_annotation(self):
        print "annotation tool stub"
        # something with QProcess
        pass
    
    @pyqtSlot()
    def run_comparison(self):
        # browse for save path
        if self.comparison_edit.text() == "":
            path = str(QFileDialog.getSaveFileName(self, "Save Comparison Output", "./data",
                                               "MOV File (*.mov);;AVI File (*.avi);;MP4 File (*.mp4);;Any File (*.*)"))
            self.comparison_edit.setText(path)
        else:
            path = str(self.comparison_edit.text())
        
        # run tests
        if path == "": return
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        self.statusbar.showMessage("Running Comparison.")
        self.run_tool(compare_main, ["wizard", 
                    str(self.dataset_mov_edit.text()),
                    str(self.dataset_map_edit.text()),
                    str(self.dataset_ann_edit.text()),
                    "-export", path,
                    "-config", self.config_path])
    
    @pyqtSlot()
    def run_evaluation(self):
        #TODO evaluation isn't complete, returns early
        QMessageBox.information(self, "Stub function", "This is incomplete at the moment. Soz.")
        return 
        
        # browse for save path
        if self.evaluation_edit.text() == "":
            path = QFileDialog.getSaveFileName(self, "Save Evaluation Output", "./data",
                                               "XML File (*.xml)")
            self.evaluation_edit.setText(path)
        else:
            path = str(self.evaluation_edit.text())
        
        # run tests
        if path == "": return
        if not path.lower().endswith(".xml"):
            path += ".xml"
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        self.statusbar.showMessage("Running Evaluation.")
        self.run_tool(evaluate_main, ["wizard", 
                    str(self.dataset_map_edit.text()),
                    str(self.dataset_ann_edit.text()),
                    str(self.evaluation_edit.text()),
                    "-config", self.config_path])
    
    ## File dialog slots
    @pyqtSlot()
    def browse_chessboards(self):
        path = QFileDialog.getExistingDirectory(self, "Folder of Chessboard Images", 
                                            self.chessboard_edit.text(), QFileDialog.Options(0))
        
        if path != "":
            self.chessboard_edit.setText(path)
            self.load_chessboards()
        
    @pyqtSlot()
    def browse_calibration(self):
        path = QFileDialog.getOpenFileName(self, "Open Calibration XML", 
                                            self.calibration_edit.text(), "XML File (*.xml)")
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
                                                self.vicondata_edit.text(), QFileDialog.Options(0))
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
            self.check_compare_enable()
            self.check_annotate_enable()
        
    @pyqtSlot()
    def browse_mapping_data(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset XML (Mapped)", 
                                           self.dataset_map_edit.text(), "XML File (*.xml)")
        if path != "":
            self.dataset_map_edit.setText(path)
            self.check_compare_enable()
            self.check_evaluate_enable()
    
    @pyqtSlot()
    def browse_annotation_data(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset XML (Annotated)", 
                                           self.dataset_ann_edit.text(), "XML File (*.xml)")
        if path != "":
            self.dataset_ann_edit.setText(path)
            self.check_compare_enable()
            self.check_evaluate_enable()
    
    ## button checker dealios (to ensure a correct pipeline workflow)
    @pyqtSlot()
    def check_trainer_enable(self):
        if 'worker' not in self.__dict__ or self.worker.isRunning():
            self.trainer_button.setEnabled(
                        self.trainer_csv_edit.text() != "" and 
                        self.trainer_mov_edit.text() != "")
    
    @pyqtSlot()
    def check_mapping_enable(self):
        if 'worker' not in self.__dict__ or self.worker.isRunning():
            self.mapping_button.setEnabled(
                        self.calibration_edit.text() != "" and 
                        self.trainer_xml_edit.text() != "" and 
                        self.vicondata_edit.text() != "")
    
    @pyqtSlot()
    def check_annotate_enable(self):
        if 'worker' not in self.__dict__ or self.worker.isRunning():
            self.annotation_button.setEnabled(
                        self.dataset_mov_edit.text() != "")
    
    @pyqtSlot()
    def check_compare_enable(self):
        if 'worker' not in self.__dict__ or self.worker.isRunning():
            self.comparison_button.setEnabled(
                        self.dataset_mov_edit.text() != "" and 
                        self.dataset_map_edit.text() != "" and 
                        self.dataset_ann_edit.text() != "")
    
    @pyqtSlot()
    def check_evaluate_enable(self):
        if 'worker' not in self.__dict__ or self.worker.isRunning():
            self.evaluation_button.setEnabled(
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
        self.vicondata = []
        if self.vicondata_edit.text() != "":
            for f in glob.glob(os.path.join(str(self.vicondata_edit.text()), "*.csv")):
                if "wand" not in f.lower():
                    self.vicondata.append(f)
        
        self.num_vicondata.setText(str(len(self.vicondata)))
        self.mapping_button.setEnabled(len(self.vicondata) > 0)
    
    ## Various GUI events
    @pyqtSlot()
    def set_unsaved(self):
        self.saved = False
        self.setWindowTitle(self._working_title + "*")
    
    @pyqtSlot('QString')
    def update_working_title(self, text):
        self._working_title = "{} - {}".format(self._original_title, text)
        self.setWindowTitle(self._working_title + "*")
    
    @pyqtSlot()
    def reset_statusbar(self):
        self.statusbar.showMessage("Nothing Running.")
    
    @pyqtSlot()
    def enable_tools(self, set=True):
        self.chessboard_button.setEnabled(set)
        self.capture_trainer_button.setEnabled(set)
        self.capture_button.setEnabled(set)
        self.trainer_mov_button.setEnabled(set)
        self.dataset_mov_button.setEnabled(set)
        self.chessboard_edit.setEnabled(set)
        self.trainer_csv_edit.setEnabled(set)
        self.trainer_mov_edit.setEnabled(set)
        self.trainer_xml_edit.setEnabled(set)
        self.dataset_mov_edit.setEnabled(set)
        self.vicondata_edit.setEnabled(set)
        self.dataset_map_edit.setEnabled(set)
        self.dataset_ann_edit.setEnabled(set)
        self.comparison_edit.setEnabled(set)
        self.evaluation_edit.setEnabled(set)
        self.actionSave.setEnabled(set)
        self.actionSave_As.setEnabled(set)
        self.actionOpen.setEnabled(set)
        self.actionSave.setEnabled(set)
        self.actionOpen_Config.setEnabled(set)
        self.actionEdit_Config.setEnabled(set)
        
        if not set:
            self.calibration_button.setEnabled(set)
            self.trainer_button.setEnabled(set)
            self.mapping_button.setEnabled(set)
            self.annotation_button.setEnabled(set)
            self.comparison_button.setEnabled(set)
            self.evaluation_button.setEnabled(set)
        else:
            self.check_trainer_enable()
            self.check_mapping_enable()
            self.check_annotate_enable()
            self.check_compare_enable()
            self.check_evaluate_enable()
            self.load_chessboards()
            self.load_vicondata()
    
    @pyqtSlot()
    def disable_tools(self, set=False):
        self.enable_tools(set)
    
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

## Worker thread, for running CPU intensive tools
## so as not to interrupt the ui event loop
class ThreadWorker(QThread):
    # only pass tool main() function here
    # _cannot_ accept Wizard functions (because of clashing event loops, etc)
    def __init__(self, func, args, parent=None):
        QThread.__init__(self, parent)
        self.func = func
        self.args = args
    
    def start(self):
        QThread.start(self)

    def run(self):
        self.func(self.args)

## Main thread
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Wizard()
    w.show()
    sys.exit(app.exec_())