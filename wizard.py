# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QMessageBox, QInputDialog, qApp
from PyQt4.QtCore import QProcess, QObject, QThread, pyqtSlot, pyqtSignal, QT_VERSION_STR
from PyQt4.Qt import PYQT_VERSION_STR
import sys, os, cv2, numpy as np, glob, datetime, xml.etree.ElementTree as ET, tempfile, zipfile, shutil
from elementtree.SimpleXMLWriter import XMLWriter
from custom_widgets import *

# ignore vicon capture errors because of PyVicon as it wont
# import on linux/OSX or 64bit system - not compiled for them
try: from vicon_capture import main as capture_main
except: pass

# tool imports
error = False
try:
    from extract_frames import main as chess_extract_main
    from dualcalib import main as calib_main
    from trainer import main as trainer_main
    from mapping import main as mapping_main
    from compare import main as compare_main
    from compare_trainer import main as compare_trainer_main
# catch errors, report in main()
except Exception as e:
    error = e

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
        
        self.trainer_marks = (0,0)
        self.dataset_marks = (0,0)
        self.buttonside_images = []
        self.backside_images = []
        self.vicondata = []
        
        # save/open events
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_As.triggered.connect(self.save_file_as)
        self.actionOpen.triggered.connect(self.open_file)
        self.actionNew.triggered.connect(self.clear_data)
        
        # other menu events
        self.actionAbout.triggered.connect(self.about)
        self.actionAbout_QT.triggered.connect(qApp.aboutQt)
        self.actionKill_Worker.triggered.connect(self.kill_worker)
        self.actionExit.triggered.connect(self.close)
        
        # save checks
        self.dataset_name_edit.textChanged.connect(self.update_working_title)
        self.dataset_name_edit.textChanged.connect(self.set_unsaved)
        self.chessboard_edit.textChanged.connect(self.set_unsaved)
        self.trainer_csv_edit.textChanged.connect(self.set_unsaved)
        self.trainer_mov_edit.textChanged.connect(self.set_unsaved)
        self.calibration_edit.textChanged.connect(self.set_unsaved)
        self.trainer_xml_edit.textChanged.connect(self.set_unsaved)
        self.trainer_map_edit.textChanged.connect(self.set_unsaved)
        self.vicondata_edit.textChanged.connect(self.set_unsaved)
        self.vicondata_edit.textChanged.connect(self.set_unsaved)
        self.dataset_mov_edit.textChanged.connect(self.set_unsaved)
        self.dataset_mov_edit.textChanged.connect(self.set_unsaved)
        self.dataset_map_edit.textChanged.connect(self.set_unsaved)
        self.dataset_ann_edit.textChanged.connect(self.set_unsaved)
        
        self.trainer_mov_edit.textEdited.connect(self.reset_trainer_marks)
        self.dataset_mov_edit.textEdited.connect(self.reset_dataset_marks)
        
        # editing check/enable events
        self.chessboard_edit.editingFinished.connect(self.load_chessboards)
        self.trainer_csv_edit.textChanged.connect(self.check_trainer_enable)
        self.trainer_mov_edit.textChanged.connect(self.check_trainer_enable)
        self.calibration_edit.textChanged.connect(self.check_mapping_enable)
        self.trainer_xml_edit.textChanged.connect(self.check_mapping_enable)
        self.vicondata_edit.editingFinished.connect(self.load_vicondata)
        self.vicondata_edit.textChanged.connect(self.check_mapping_enable)
        self.dataset_mov_edit.textChanged.connect(self.check_annotate_enable)
        self.dataset_mov_edit.textChanged.connect(self.check_compare_enable)
        self.dataset_map_edit.textChanged.connect(self.check_compare_enable)
        self.dataset_ann_edit.textChanged.connect(self.check_compare_enable)
        self.dataset_map_edit.textChanged.connect(self.check_evaluate_enable)
        self.dataset_ann_edit.textChanged.connect(self.check_evaluate_enable)
        self.trainer_xml_edit.textChanged.connect(self.check_trainer_mapping_enable)
        self.trainer_csv_edit.textChanged.connect(self.check_trainer_mapping_enable)
        self.calibration_edit.textChanged.connect(self.check_trainer_mapping_enable)
        self.trainer_xml_edit.textChanged.connect(self.check_trainer_compare_enable)
        self.trainer_map_edit.textChanged.connect(self.check_trainer_compare_enable)
        self.trainer_mov_edit.textChanged.connect(self.check_trainer_compare_enable)
        
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
        
        # determine which fields to save
        edit_fields = {}
        if self.calibration_edit.text() != "":
            edit_fields['calibration'] = str(self.calibration_edit.text())
        if len(self.buttonside_images) + len(self.backside_images) > 0 \
                and self.chessboards_edit.text() != "":
            edit_fields['chessboards'] = str(self.chessboards_edit.text())
        if self.trainer_xml_edit.text() != "":
            edit_fields['trainer_set'] = str(self.trainer_xml_edit.text())
        if self.trainer_csv_edit.text() != "":
            edit_fields['trainer_csv'] = str(self.trainer_csv_edit.text())
        if self.trainer_mov_edit.text() != "":
            edit_fields['trainer_mov'] = str(self.trainer_mov_edit.text())
        if self.trainer_map_edit.text() != "":
            edit_fields['trainer_map'] = str(self.trainer_map_edit.text())
        if self.dataset_mov_edit.text() != "":
            edit_fields['dataset_mov'] = str(self.dataset_mov_edit.text())
        if len(self.vicondata) > 0:
            edit_fields['vicondata'] = str(self.vicondata_edit.text())
        if self.dataset_map_edit.text() != "":
            edit_fields['dataset_map'] = str(self.dataset_map_edit.text())
        if self.trainer_map_edit.text() != "":
            edit_fields['dataset_ann'] = str(self.datset_ann_edit.text())
        if self.comparison_edit.text() != "":
            edit_fields['comparison'] = str(self.comparison_edit.text())
        if self.evaluation_edit.text() != "":
            edit_fields['evaluation'] = str(self.evaluation_edit.text())
        
        # abort if there's no data
        if len(edit_fields) == 0:
            QMessageBox.information(self, "No data", "There is nothing to save!")
            return
            
        # determine which data to save
        dialog = SaveOptionsDialog(self, edit_fields)
        ok = dialog.exec_()
        if not ok: return
        edit_fields = dialog.checked_fields()
        
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
            
            # zips things while at the same time 
            # recording them into the header xml
            
            # calibration xml
            file_path = edit_fields.get("calibration")
            if file_path and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                
                w.start("calibration")
                w.element("xml", file_name)
                
                # optional elements - dependant on calib xml
                chess_len = len(self.buttonside_images) + len(self.backside_images)
                file_path = edit_fields.get("chessboards")
                
                # write chessboard folder
                if file_path and os.path.exists(file_path) and chess_len > 0:
                    w.start("chessboards", path="chessboards/", size=str(chess_len))
                    
                    for c in self.buttonside_images + self.backside_images:
                        file_name = os.path.basename(c)
                        zipper.write(str(c), "chessboards/" + file_name)
                        w.element("file", file_name)
                    
                    w.end() # chessboards
                w.end() # calibration
            
            # trainer xml
            file_path = edit_fields.get("trainer_set")
            if file_path and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                
                w.start("training")
                w.element("xml", file_name)
                
                # optional elements - dependant on trainer xml
                # trainer video
                file_path = edit_fields.get("trainer_mov")
                if file_path and os.path.isfile(file_path):
                    
                    file_name = os.path.basename(file_path)
                    zipper.write(file_path, file_name)
                    
                    # with marks if applicable
                    if self.trainer_marks[1] > 0:
                        mark_in, mark_out = self.trainer_marks
                        w.start("video", mark_in=str(mark_in), mark_out=str(mark_out))
                    else:
                        w.start("video")
                    w.data(file_name)
                    w.end()
                
                # trainer CSV
                file_path = edit_fields.get("trainer_csv")
                if file_path and os.path.isfile(file_path):
                    
                    file_name = os.path.basename(file_path)
                    zipper.write(file_path, file_name)
                    w.element("csv", file_name)
                
                # trainer mapping
                file_path = edit_fields.get("trainer_map")
                if file_path and os.path.isfile(file_path):
                    
                    file_name = os.path.basename(file_path)
                    zipper.write(file_path, file_name)
                    w.element("map", file_name)
                    
                w.end() # training
                
            # raw video
            file_path = edit_fields.get("dataset_mov")
            if file_path and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                
                w.start("rawData")
                
                # dataset video, with marks if applicable
                if self.dataset_marks[1] > 0:
                    mark_in, mark_out = self.dataset_marks
                    w.start("video", mark_in=str(mark_in), mark_out=str(mark_out))
                else:
                    w.start("video")
                w.data(file_name)
                w.end()
                
                # write vicon folder - dependant on video_file
                file_path = edit_fields.get("vicondata")
                if file_path and os.path.exists(file_path) and len(self.vicondata) > 0:
                    w.start("vicon", path="vicondata/", size=str(len(self.vicondata)))
                    
                    for v in self.vicondata:
                        file_name = os.path.basename(v)
                        zipper.write(str(v), "vicondata/" + file_name)
                        w.element("file", file_name)
                    
                    w.end() # vicon
                w.end() # rawData
                
            # evaluation xml
            file_path = edit_fields.get("evaluation")
            if file_path and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                w.element("evaluation", file_name)
            
            # comparison video
            file_path = edit_fields.get("comparison")
            if file_path and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                w.element("comparison", file_name)
            
            # write datasets group
            w.start("datasets")
            
            file_path = edit_fields.get("dataset_map")
            if file_path and os.path.isfile(file_path):
                
                file_name = os.path.basename(file_path)
                zipper.write(file_path, file_name)
                w.element("mapping", file_name)
                
            file_path = edit_fields.get("dataset_ann")
            if file_path and os.path.isfile(file_path):
                
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
            
            # load dataset name
            self.dataset_name_edit.setText(root.attrib["name"])
            self.save_date = root.attrib["date"]
            
            # find root elements
            calib = root.find("calibration")
            training = root.find("training")
            raw_data = root.find("rawData")
            evaluation = root.find("evaluation")
            mapping = root.find("datasets/mapping")
            annotation = root.find("datasets/annotation")
            
            # find calib elements
            if calib is not None:
                xml = calib.find("xml")
                if xml is not None:
                    chess_element = calib.find("chessboards")
                    
                    self.calibration_edit.setText(os.path.join(temp_dir, calib.find("xml").text))
                    if chess_element is not None:
                        self.chessboard_edit.setText(os.path.normpath(os.path.join(
                                                        temp_dir, chess_element.attrib["path"])))
            
            # find trainer elements
            if training is not None:
                xml = training.find("xml")
                if xml is not None:
                    csv = training.find("csv")
                    video = training.find("video")
                    
                    # set edit boxes appropriately
                    self.trainer_xml_edit.setText(os.path.join(temp_dir, xml.text))
                    if csv is not None:
                        self.trainer_csv_edit.setText(os.path.join(temp_dir, csv.text))
                    if video is not None:
                        self.trainer_mov_edit.setText(os.path.join(temp_dir, video.text))
                        
                        # load video marks if found
                        if 'mark_in' in video.attrib:
                            self.training_marks = (video.attrib['mark_in'], video.attrib['mark_out'])
            
            # find data elements
            if raw_data is not None:
                video = raw_data.find("video")
                if video is not None:
                    vicon = raw_data.find("vicon")
                    
                    # set stuff
                    self.dataset_mov_edit.setText(os.path.join(temp_dir, video.text))
                    if 'mark_in' in video.attrib:
                            self.dataset_marks = (video.attrib['mark_in'], video.attrib['mark_out'])
                    
                    if vicon is not None:
                        self.vicondata_edit.setText(os.path.normpath(os.path.join(
                                                        temp_dir, vicon.attrib["path"])))
            
            # duh for the rest
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
        
        if res == QMessageBox.Discard:
            pass
        elif res == QMessageBox.Save:
            self.save_file()
        else: # Reject or whatever
            return False
        
        self.saved = True
        self.save_path = None
        self.save_date = None
        self.setWindowTitle(self._original_title)
        
        self.dataset_name_edit.clear()
        self.chessboard_edit.clear()
        self.calibration_edit.clear()
        self.trainer_csv_edit.clear()
        self.trainer_mov_edit.clear()
        self.trainer_xml_edit.clear()
        self.trainer_map_edit.clear()
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
        self.check_trainer_compare_enable()
        self.check_trainer_mapping_enable()
        
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
            self.disable_tools()
            
            self.actionKill_Worker.setEnabled(True)
            self.worker = worker
            return True, worker
        else:
            QMessageBox.warning(self, "Already running", "A tool is already running")
            return False, self.worker
    
    def kill_worker(self):
        if 'worker' in self.__dict__ and self.worker.isRunning():
            self.worker.terminate()
            self.actionKill_Worker.setEnabled(False)
    
    def destroy_worker(self, obj):
        del self.worker
    
    def choose_lens(self, title, text):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(text)
        buttonside_button = dialog.addButton("Button Side", QMessageBox.AcceptRole)
        backside_button = dialog.addButton("Back Side", QMessageBox.AcceptRole)
        both_button = dialog.addButton("Both", QMessageBox.AcceptRole)
        dialog.exec_()
        
        return buttonside_button, backside_button, both_button, dialog.clickedButton()
    
    ## tool launcher slots
    @pyqtSlot()
    def chessboard_extract(self):
        # find a chessboard video
        input_path = QFileDialog.getOpenFileName(self, "Open Chessboard Video", "./", 
                                                "Video File (*.mov;*.avi;*.mp4);;All Files (*.*)")
        if input_path == "": return
        
        # determine lens side
        button_b, back_b, both_b, click_b = self.choose_lens("Chessboard Extract", 
                                                "Which lens would you like to extract from this video?")
        
        # browse for save path
        if self.chessboard_edit.text() == "":
            self.browse_chessboards()
        
        output_path = self.chessboard_edit.text()
        if output_path == "": return
        
        def extractor_help():
            self.showHelp("Chessboard Extractor", 
                        "Use the Left and Right keys to navigate the video.\n"
                        "When an appropriate chessboard frame is found, press Enter.\n"
                        "To quit, press ESC.")
        
        if click_b == button_b:
            self.statusbar.showMessage("Running Chessboard Extractor on Button Side.")
            extractor_help()
            stat, worker = self.run_tool(chess_extract_main, ["wizard", 
                                    str(input_path), 
                                    str(output_path),
                                    "-split", "right",
                                    "-prefix", "buttonside_",
                                    "-config", self.config_path])
            if stat:
                worker.finished.connect(self.load_chessboards)
                worker.start()
        
        elif click_b == back_b:
            self.statusbar.showMessage("Running Chessboard Extractor on Back Side.")
            extractor_help()
            stat, worker = self.run_tool(chess_extract_main, ["wizard", 
                                    str(input_path), 
                                    str(output_path),
                                    "-split", "left",
                                    "-prefix", "backside_",
                                    "-config", self.config_path])
            if stat:
                worker.finished.connect(self.load_chessboards)
                worker.start()
            
        elif click_b == both_b:
            self.statusbar.showMessage("Running Chessboard Extractor on Button Side (1/2).")
            extractor_help()
            
            stat, worker = self.run_tool(chess_extract_main, ["wizard", 
                                    str(input_path),
                                    str(output_path),
                                    "-split", "right",
                                    "-prefix", "buttonside_",
                                    "-config", self.config_path])
            if stat:
                self.chessboard_video_path = input_path
                worker.destroyed.connect(self.run_extractor_left)
                worker.start()
        else:
            print "Cancelled"
            return
    
    @pyqtSlot()
    def run_extractor_left(self):
        self.statusbar.showMessage("Running Chessboard Extractor on Back Side (2/2).")
        stat, worker = self.run_tool(chess_extract_main, ["wizard", 
                            str(self.chessboard_video_path), 
                            str(self.chessboard_edit.text()),
                            "-split", "left",
                            "-prefix", "backside_",
                            "-config", self.config_path])
        if stat:
            worker.finished.connect(self.load_chessboards)
            worker.start()
    
    @pyqtSlot()
    def run_calibration(self):
        # browse for save path
        if self.calibration_edit.text() == "":
            path = QFileDialog.getSaveFileName(self, "Save Calibration XML", "./data",
                                                "XML File (*.xml)", options=QFileDialog.DontConfirmOverwrite)
        else:
            path = self.calibration_edit.text()
            
        # run tests
        if path == "": return
        path = os.path.normpath(str(path))
        if not path.lower().endswith(".xml"):
            path += ".xml"
        self.calibration_edit.setText(path)
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        button_b, back_b, both_b, click_b = self.choose_lens("Calibrate Lens", 
                                                    "Which lens would you like to calibrate?")
        
        if click_b == button_b:
            if len(self.buttonside_images) == 0:
                QMessageBox.information(self, "Not enough images", 
                                                "No Button Side images were found.\n"
                                                "Cancelling calibration.")
                return
            
            self.statusbar.showMessage("Running Calibration on Button Side.")
            args = ["wizard", 
                    "-output", path,
                    "-buttonside", self.buttonside_path,
                    "-config", self.config_path]
            
        elif click_b == back_b:
            if len(self.backside_images) == 0:
                QMessageBox.information(self, "Not enough images", 
                                                "No Back Side images were found.\n"
                                                "Cancelling calibration.")
                return
            
            self.statusbar.showMessage("Running Calibration on Back Side.")
            args = ["wizard", 
                    "-output", path,
                    "-backside", self.backside_path,
                    "-config", self.config_path]
            
        elif click_b == both_b:
            if len(self.buttonside_images) == 0:
                QMessageBox.information(self, "Not enough images", 
                                                "No Button Side images were found.\n"
                                                "Cancelling calibration.")
                return
            if len(self.backside_images) == 0:
                QMessageBox.information(self, "Not enough images", 
                                                "No Back Side images were found.\n"
                                                "Cancelling calibration.")
                return
            
            self.statusbar.showMessage("Running Calibration on Both Sides.")
            args = ["wizard", 
                    "-output", path,
                    "-buttonside", self.buttonside_path,
                    "-backside", self.backside_path,
                    "-config", self.config_path]
        else:
            print "Cancelled"
            return
        
        stat, worker = self.run_tool(calib_main, args)
        if stat: worker.start()
    
    @pyqtSlot()
    def run_capture_training(self):
        # check for capture import
        if 'capture_main' not in globals():
            QMessageBox.warning(self, "No capture available", 
                                "Cannot run CaptureTool.\n"
                                "Probably because PyVicon isn't compiled for this system.")
            return
        
        # browse for save path
        if self.trainer_csv_edit.text() == "":
            path = QFileDialog.getSaveFileName(self, "Save Trainer CSV", "./data",
                                                    "CSV File (*.csv)",  options=QFileDialog.DontConfirmOverwrite)
        else:
            path = self.trainer_csv_edit.text()
        
        # run tests
        if path == "": return
        path = os.path.normpath(str(path))
        if not path.lower().endswith(".csv"):
            path += ".csv"
        self.trainer_csv_edit.setText(path)
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        self.statusbar.showMessage("Running Training Capture.")
        self.showHelp("Training Capture", 
                        "First prepare the camera and flash for recording. "
                        "When ready, press the OK button (below).\n"
                        "The flash will trigger, then trigger the camera recording.\n"
                        "It will flash again to mark the start of the dataset. "
                        "Now wave the Vicon Wand around. "
                        "At the end of the dataset, it was flash again a third time.")
        
        stat, worker = self.run_tool(capture_main, ["wizard",
                                    "-training", path,
                                    "-config", self.config_path])
        if stat: worker.start()
        
    @pyqtSlot()
    def run_training(self):
        # browse for save path
        if self.trainer_xml_edit.text() == "":
            path = QFileDialog.getSaveFileName(self, "Save Trainer XML", "./data",
                                                    "XML File (*.xml)", options=QFileDialog.DontConfirmOverwrite)
        else:
            path = self.trainer_xml_edit.text()
        
        # run tests
        if path == "": return
        path = os.path.normpath(str(path))
        if not path.lower().endswith(".xml"):
            path += ".xml"
        self.trainer_xml_edit.setText(path)
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        args = ["wizard", 
                str(self.trainer_mov_edit.text()),
                str(self.trainer_csv_edit.text()),
                path,
                "-config", self.config_path]
        
        if self.trainer_marks[1] > 0:
            mark_in, mark_out = self.trainer_marks
            args += [str(mark_in), str(mark_out)]
        
        self.statusbar.showMessage("Running Trainer.")
        self.showHelp("Training Tool", 
                        "Use the Left and Right arrow keys to navigate the video.\n"
                        "Mark the middle Wand dot with the cursor. "
                        "Use the 1 and 2 keys to switch between each lens. "
                        "Change the number of clicks in the config file.\n"
                        "Navigate backwards one frame to preview it's position. "
                        "When satisfied, press Enter to save the training data.\n"
                        "To quit, press ESC - this will lose data.")
        
        stat, worker = self.run_tool(trainer_main, args)
        if stat: worker.start()
    
    @pyqtSlot()
    def run_capture(self):
        # check for capture import
        if 'capture_main' not in globals():
            QMessageBox.warning(self, "No capture available", 
                                "Cannot run CaptureTool.\n"
                                "Probably because PyVicon isn't compiled for this system.")
            return
        
        # browse for save path
        if self.vicondata_edit.text() == "":
            self.browse_vicondata()
        
        # get capture time
        time, ok = QInputDialog.getInt(self, "Capture Time", "Time:", 60, 30, 999)
        if not ok:
            return
        
        # get path
        path = str(self.vicondata_edit.text())
        if path == "": return
        
        self.statusbar.showMessage("Running Data Capture.")
        self.showHelp("Data Capture", 
                        "First prepare the camera and flash for recording. "
                        "When ready, press the OK button (below).\n"
                        "The flash will trigger, then trigger the camera recording.\n"
                        "It will flash again to mark the start of the dataset. "
                        "Now perform the dataset scenario. "
                        "At the end of the dataset, it was flash again a third time.")
        
        stat, worker = self.run_tool(capture_main, ["wizard", 
                                    "-time", str(time),
                                    "-output", path,
                                    "-config", self.config_path])
        if stat: 
            worker.finished.connect(self.load_vicondata)
            worker.start()
        
    @pyqtSlot()
    def run_mapping(self):
        # browse for save path
        if self.dataset_map_edit.text() == "":
            path = QFileDialog.getSaveFileName(self, "Save Mapping XML", "./data",
                                                    "XML File (*.xml)", options=QFileDialog.DontConfirmOverwrite)
        else:
            path = self.dataset_map_edit.text()
        
        # run tests
        if path == "": return
        path = os.path.normpath(str(path))
        if not path.lower().endswith(".xml"):
            path += ".xml"
        self.dataset_map_edit.setText(path)
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        self.statusbar.showMessage("Running Mapping.")
        stat, worker = self.run_tool(mapping_main, ["wizard", 
                                    "-calib", str(self.calibration_edit.text()),
                                    "-trainer", str(self.trainer_xml_edit.text()),
                                    "-output", path,
                                    "-config", self.config_path] +\
                                    self.vicondata)
        if stat: worker.start()
    
    @pyqtSlot()
    def run_trainer_mapping(self):
        # browse for save path
        if self.trainer_map_edit.text() == "":
            path = QFileDialog.getSaveFileName(self, "Save Trainer Mapping XML", "./data",
                                                    "XML File (*.xml)", options=QFileDialog.DontConfirmOverwrite)
        else:
            path = self.trainer_map_edit.text()
        
        # run tests
        if path == "": return
        path = os.path.normpath(str(path))
        if not path.lower().endswith(".xml"):
            path += ".xml"
        self.trainer_map_edit.setText(path)
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        self.statusbar.showMessage("Running Trainer Mapping.")
        stat, worker = self.run_tool(mapping_main, ["wizard", 
                                    "-calib", str(self.calibration_edit.text()),
                                    "-trainer", str(self.trainer_xml_edit.text()),
                                    "-output", path,
                                    "-config", self.config_path,
                                    trainer_csv.edit.text()])
        if stat: worker.start()
    
    @pyqtSlot()
    def run_trainer_compare(self):
        args = ["wizard", 
                str(self.trainer_mov_edit.text()),
                str(self.trainer_map_edit.text()),
                str(self.trainer_xml_edit.text()),
                "-config", self.config_path]
        
        # insert marks
        if self.trainer_marks[1] > 0:
            mark_in, mark_out = self.trainer_marks
            args += [str(mark_in), str(mark_out)]
        
        self.statusbar.showMessage("Running Trainer Comparison.")
        stat, worker = self.run_tool(trainer_compare_main, args)
        if stat: worker.start()
    
    @pyqtSlot()
    def run_annotation(self):
        print "annotation tool stub"
        # something with QProcess
        pass
    
    @pyqtSlot()
    def run_comparison(self):
        # determine comparison mode
        dialog = QMessageBox(self)
        dialog.setText("Would you like to export a video or use the interactive comparison?")
        dialog.setWindowTitle("Comparison Tool Mode")
        dialog.addButton("Interactive", QMessageBox.ActionRole)
        dialog.addButton("Export", QMessageBox.AcceptRole)
        dialog.exec_()
        res = dialog.buttonRole(dialog.clickedButton())
        
        args = ["wizard", 
                str(self.dataset_mov_edit.text()),
                str(self.dataset_map_edit.text()),
                str(self.dataset_ann_edit.text()),
                "-config", self.config_path]
        
        # cancel if invalid (ESC key)
        if res == QMessageBox.InvalidRole:
            return 
        
        # run export
        elif res == QMessageBox.AcceptRole:
            # browse for save path
            if self.comparison_edit.text() == "":
                path = QFileDialog.getSaveFileName(self, "Save Comparison Output", "./data",
                                                "MOV File (*.mov);;AVI File (*.avi);;MP4 File (*.mp4);;Any File (*.*)",
                                                options=QFileDialog.DontConfirmOverwrite)
            else:
                path = self.comparison_edit.text()
        
            # run tests
            if path == "": return
            path = os.path.normpath(str(path))
            self.comparison_edit.setText(path)
            
            args += ["-export", path]
            
            if os.path.isfile(path):
                res = QMessageBox.question(self, "File Exists", 
                                            "File Exists.\nDo you want to overwrite it?",
                                            QMessageBox.Yes, QMessageBox.No)
                if res == QMessageBox.No: return
        
        #else run interactive
        
        # insert marks
        if self.dataset_marks[1] > 0:
            mark_in, mark_out = self.dataset_marks
            args += [str(mark_in), str(mark_out)]
        
        # run the tool
        self.statusbar.showMessage("Running Comparison.")
        stat, worker = self.run_tool(compare_main, args)
        if stat: worker.start()
    
    @pyqtSlot()
    def run_evaluation(self):
        #TODO evaluation isn't complete, returns early
        QMessageBox.information(self, "Stub function", "This is incomplete at the moment. Soz.")
        return 
        
        # browse for save path
        if self.evaluation_edit.text() == "":
            path = QFileDialog.getSaveFileName(self, "Save Evaluation Output", "./data",
                                               "XML File (*.xml)", options=QFileDialog.DontConfirmOverwrite)
        else:
            path = self.evaluation_edit.text()
        
        # run tests
        if path == "": return
        path = os.path.normpath(str(path))
        if not path.lower().endswith(".xml"):
            path += ".xml"
        self.evaluation_edit.setText(path)
        
        if os.path.isfile(path):
            res = QMessageBox.question(self, "File Exists", 
                                        "File Exists.\nDo you want to overwrite it?",
                                        QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No: return
        
        self.statusbar.showMessage("Running Evaluation.")
        stat, worker = self.run_tool(evaluate_main, ["wizard", 
                                str(self.dataset_map_edit.text()),
                                str(self.dataset_ann_edit.text()),
                                str(self.evaluation_edit.text()),
                                "-config", self.config_path])
        if stat: worker.start()
    
    def run_marker(self, path, marks):
        dialog = MarkerDialog(self, path, marks)
        
        self.disable_tools()
        self.statusbar.showMessage("Running Marker Tool.")
        ok = dialog.exec_()
        self.reset_statusbar()
        self.enable_tools()
        
        if ok == MarkerDialog.Accepted:
            print "Marks:", dialog.marks()
            return dialog.marks()
        
        return None
    
    ## File dialog slots
    @pyqtSlot()
    def browse_chessboards(self):
        path = QFileDialog.getExistingDirectory(self, "Folder of Chessboards Images", 
                                                self.chessboard_edit.text(), QFileDialog.Options(0))
        
        if path != "":
            path = os.path.normpath(str(path))
            self.chessboard_edit.setText(path)
            self.load_chessboards()
    
    @pyqtSlot()
    def browse_calibration(self):
        path = QFileDialog.getOpenFileName(self, "Open Calibration XML", 
                                            self.calibration_edit.text(), "XML File (*.xml)")
        if path != "":
            path = os.path.normpath(str(path))
            self.calibration_edit.setText(path)
            self.check_mapping_enable()
        
    @pyqtSlot()
    def browse_trainer_csv(self):
        path = QFileDialog.getOpenFileName(self, "Open Training CSV", 
                                           self.trainer_csv_edit.text(), "CSV File (*.csv)")
        if path != "":
            path = os.path.normpath(str(path))
            self.trainer_csv_edit.setText(path)
            self.check_trainer_enable()
        
    @pyqtSlot()
    def browse_trainer_mov(self):
        path = QFileDialog.getOpenFileName(self, "Open Training Video", 
                                           self.trainer_mov_edit.text(), 
                                           "Video File (*.mov;*.avi;*.mp4);;All Files (*.*)")
        if path != "":
            path = os.path.normpath(str(path))
            self.trainer_mov_edit.setText(path)
            
            marks = self.run_marker(path, self.trainer_marks)
            if marks is not None:
                self.trainer_marks = marks
            
    @pyqtSlot()
    def browse_trainer_xml(self):
        path = QFileDialog.getOpenFileName(self, "Open Training XML", 
                                           self.trainer_xml_edit.text(), "XML File (*.xml)")
        if path != "":
            path = os.path.normpath(str(path))
            self.trainer_xml_edit.setText(path)
            self.check_mapping_enable()
    
    @pyqtSlot()
    def browse_vicondata(self):
        path = QFileDialog.getExistingDirectory(self, "Folder of Vicon CSV files", 
                                                self.vicondata_edit.text(), QFileDialog.Options(0))
        if path != "":
            path = os.path.normpath(str(path))
            self.vicondata_edit.setText(path)
            self.load_vicondata()
        
    @pyqtSlot()
    def browse_vicon_mov(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset Video", 
                                           self.dataset_mov_edit.text(), 
                                           "Video File (*.mov;*.avi;*.mp4);;All Files (*.*)")
        if path != "":
            path = os.path.normpath(str(path))
            self.dataset_mov_edit.setText(path)
            
            marks = self.run_marker(path, self.dataset_marks)
            if marks is not None:
                self.dataset_marks = marks
        
    @pyqtSlot()
    def browse_mapping_data(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset XML (Mapped)", 
                                           self.dataset_map_edit.text(), "XML File (*.xml)")
        if path != "":
            path = os.path.normpath(str(path))
            self.dataset_map_edit.setText(path)
            self.check_compare_enable()
            self.check_evaluate_enable()
    
    @pyqtSlot()
    def browse_annotation_data(self):
        path = QFileDialog.getOpenFileName(self, "Open Dataset XML (Annotated)", 
                                           self.dataset_ann_edit.text(), "XML File (*.xml)")
        if path != "":
            path = os.path.normpath(str(path))
            self.dataset_ann_edit.setText(path)
            self.check_compare_enable()
            self.check_evaluate_enable()
    
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
    
    @pyqtSlot()
    def check_trainer_mapping_enable(self):
        self.trainer_map_button.setEnabled(
                    self.trainer_xml_edit.text() != "" and 
                    self.trainer_csv_edit.text() != "" and 
                    self.calibration_edit.text() != "")
    
    @pyqtSlot()
    def check_trainer_compare_enable(self):
        self.trainer_compare_button.setEnabled(
                    self.trainer_map_edit.text() != "" and 
                    self.trainer_mov_edit.text() != "" and 
                    self.trainer_xml_edit.text() != "")
    
    
    @pyqtSlot()
    def check_evaluate_enable(self):
        self.evaluation_button.setEnabled(
                    self.dataset_map_edit.text() != "" and 
                    self.dataset_ann_edit.text() != "")
    
    # loads directory of image paths into chessboard list
    @pyqtSlot()
    def load_chessboards(self):
        self.buttonside_path = ""
        self.backside_path = ""
        self.buttonside_images = []
        self.backside_images = []
        
        # load new images (if applicable)
        if self.chessboard_edit.text() != "":
            self.buttonside_path = str(self.chessboard_edit.text()) + os.sep + "buttonside_"
            self.backside_path = str(self.chessboard_edit.text()) + os.sep + "backside_"
            
            self.buttonside_images = glob.glob(self.buttonside_path + "*")
            self.backside_images = glob.glob(self.backside_path + "*")
        
        # determine length, present in gui, enable buttons, whatever
        chess_len = len(self.buttonside_images) + len(self.backside_images)
        self.num_chessboards.setText(str(chess_len))
        self.calibration_button.setEnabled(chess_len > 0)
        self.num_chessboards.setToolTip("{} button side, {} back side".format(
                                            len(self.buttonside_images), 
                                            len(self.backside_images)))
    
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
    
    @pyqtSlot()
    def set_trainer_marks(self, mark_in, mark_out):
        self.trainer_marks = (mark_in, mark_out)
        
    @pyqtSlot()
    def set_dataset_marks(self, mark_in, mark_out):
        self.dataset_marks = (mark_in, mark_out)
    
    @pyqtSlot()
    def reset_trainer_marks(self):
        self.trainer_marks = (0,0)
    
    @pyqtSlot()
    def reset_dataset_marks(self):
        self.dataset_marks = (0,0)
    
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
        self.calibration_edit.setEnabled(set)
        self.trainer_csv_edit.setEnabled(set)
        self.trainer_mov_edit.setEnabled(set)
        self.trainer_xml_edit.setEnabled(set)
        self.dataset_mov_edit.setEnabled(set)
        self.vicondata_edit.setEnabled(set)
        self.dataset_map_edit.setEnabled(set)
        self.dataset_ann_edit.setEnabled(set)
        self.comparison_edit.setEnabled(set)
        self.evaluation_edit.setEnabled(set)
        self.trainer_map_edit.setEnabled(set)
        self.actionNew.setEnabled(set)
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
            self.trainer_map_button.setEnabled(set)
            self.trainer_compare_button.setEnabled(set)
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
    
    def showHelp(self, title, text):
        if self.actionHelp_Dialogs.isChecked():
            dialog = QMessageBox(self);
            dialog.setWindowTitle(title)
            dialog.setText(text)
            dialog.setIcon(QMessageBox.Information)
            dialog.setStandardButtons(QMessageBox.Ok)
            dialog.exec_()
    
    @pyqtSlot()
    def about(self):
        QMessageBox.about(self, "Project EagleEye", 
                                "UniSA ITMS 2015\n"
                                "Gwilyn Saunders\n"
                                "Kin Kuen Liu\n"
                                "Kim Manjung\n"
                                "\n"
                                "Using:\n"
                                "Python: {}\n"
                                "Qt: {}\n"
                                "PyQt: {}\n"
                                "OpenCV: {}\n"
                                "NumPy: {}"\
                                .format(sys.version.split('|')[0], 
                                    QT_VERSION_STR, 
                                    PYQT_VERSION_STR,
                                    cv2.__version__, 
                                    np.__version__))
    
    def closeEvent(self, ev):
        if not self.saved:
            if not self.clear_data():
                ev.ignore()
                return
            
        ev.accept()
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
    
    # catch import errors
    if error:
        QMessageBox.critical(None, "Error!", str(error))
        exit(1)
    
    w = Wizard()
    w.show()
    sys.exit(app.exec_())
