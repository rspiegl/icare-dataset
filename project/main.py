import sys
import time

import tobii_research as tr
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QPoint, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog

import processing.TestProcessor as Processor
from Utilities import DatasetLoader
from gui.mainwindow import Ui_MainWindow
from processing.Evaluation import Evaluation


def current_micro_time(): return tr.get_system_time_stamp()


class Signal(QObject):
    """Gets emitted when saving is complete."""
    sig = pyqtSignal()


class ProcessSignal(QObject):
    """Emits histogram and calibration pixmap when processing is done."""
    sig = pyqtSignal(QPixmap, QPixmap)


class SleepThread(QThread):
    """A class used to signal the GUI when the Intertrial Interval is over."""

    def __init__(self, sleep, parent=None):
        QThread.__init__(self, parent)
        self.sleep = sleep
        self.signal = Signal()

    def run(self):
        time.sleep(self.sleep)
        self.signal.sig.emit()


class SaveThread(QThread):
    """Handles the saving of data that, for longer trials, can take over half a second."""

    def __init__(self):
        QThread.__init__(self)
        self.evaluation = None
        self.signal = Signal()

    def set_evaluation(self, evaluation):
        self.evaluation = evaluation

    def run(self):
        self.evaluation.save_to_file()
        self.signal.sig.emit()


class ProcessThread(QThread):
    """Generates histograms for calibration and eyetracking data and then shows it."""

    def __init__(self, data=None, pic_geometry=None):
        QThread.__init__(self)
        self.data = data
        self.pic_geometry = pic_geometry
        self.signal = ProcessSignal()

    def set_data(self, data):
        self.data = data

    def set_pic_geometry(self, pic_geometry):
        self.pic_geometry = pic_geometry

    def run(self):
        if self.data[4] and self.data[5]:
            processed_pic = Processor.process_picture_eyetracking_data(self.data[4])
            pic_heat = Processor.create_heatmap(processed_pic)
            if not pic_heat:
                print("no data after creation of heatmap")
                return
            pic_trim = Processor.trim_heatmap(pic_heat, self.pic_geometry)
            histogram = Processor.create_histogram_temp(pic_trim, self.data[0][0], name='histo')
            histogram = QPixmap(histogram)

            processed_cali = Processor.process_picture_eyetracking_data(self.data[5])
            cali_heat = Processor.create_heatmap(processed_cali)
            if not cali_heat:
                print("no data after creation of calibration")
                return
            cali_offset = Processor.offset_calibration(cali_heat, self.pic_geometry)
            cali_trim = Processor.trim_heatmap(cali_offset, self.pic_geometry)
            calibration = Processor.create_histogram_temp(cali_trim, DatasetLoader.CALIBRATE_PICTURE, name='cali')
            calibration = QPixmap(calibration)

            self.signal.sig.emit(histogram, calibration)


class MainWindowUI(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.test_sequence = [
            (DatasetLoader.DATASET_CATDOG, 10, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 5), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 1), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 5), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 1), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 5), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 1), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 1), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 19), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 20), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 21), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sr'), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sd'), 35, True),
        ]
        self.sequence_iter = iter(self.test_sequence)
        self.directory = next(self.sequence_iter)
        self.mode = 'debug'
        self.pics, self.pics_iter = None, None
        self.pic, self.pixmap = None, None
        self.timer_start, self.timer_end = 0, 0
        self.success_counter = 0
        self.done = False
        self.start = True
        self.inter_trial = False
        self.dataset = None
        self.evaluation = None
        self.data = []
        self.tracker = None
        self.eyetracker_data, self.calibration_data = [], []
        self.calibrate_pixmap = QPixmap(DatasetLoader.CALIBRATE_PICTURE)
        self.picShow.setPixmap(self.calibrate_pixmap)
        self.central_widget_geometry, self.pic_geometry = None, None

        self.process_thread = None
        self.response_thread = SleepThread(1)
        self.response_thread.signal.sig.connect(self.remove_response)
        self.save_thread = SaveThread()
        self.save_thread.signal.sig.connect(self.saving_complete)

        self.init_eyetracker()
        self.load_dataset(self.directory[0], self.directory[1], self.directory[2])

    def setupUi(self, main_window):
        super().setupUi(main_window)
        self.listPicturesFalse.setSpacing(2)
        self.listPicturesTrue.setSpacing(2)

    def classify(self, category):
        duration = self.timer_end - self.timer_start
        self.data.append([self.pic, category, duration,
                          (self.timer_start, self.timer_end), self.eyetracker_data,
                          self.calibration_data])
        self.eyetracker_data = []

    def load_dataset(self, dir_path, number=35, balance=True):
        self.dataset = DatasetLoader.load_problem(dir_path, number=number, balance=balance)
        self.reset()

    def gaze_data_callback(self, gaze_data):
        self.eyetracker_data.append(gaze_data)

    def init_eyetracker(self):
        found = tr.find_all_eyetrackers()
        if found:
            self.tracker = found[0]
            self.tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)
        else:
            print("No EyeTrackers found.")

    def end_trial(self, classification: int):
        self.picShow.clear()
        # stop timer
        self.timer_end = current_micro_time()
        # save to data
        self.classify(classification)
        # add to list
        self._create_list_item()
        # display text
        if classification == self.pic[1]:
            self.success_counter += 1
            classified = "Correct!"
            self.picShow.setStyleSheet("background-color: rgb(138, 226, 52);")  # light green
        else:
            self.success_counter = 0
            classified = "Incorrect!"
            self.picShow.setStyleSheet("background-color: rgb(255, 51, 51);")  # light red
        self.picShow.setPixmap(self.calibrate_pixmap)

        self.descriptionLabel.setText(classified + " Press Enter to continue")
        # disable buttons
        self._disable_buttons(True)

        if self.mode == 'debug':
            self.process_thread = ProcessThread(self.data[-1], self.pic_geometry)
            self.process_thread.signal.sig.connect(self.show_histogram_calibration)
            self.process_thread.start()

        try:
            if self.success_counter >= 7:
                raise StopIteration
            self.pic = next(self.pics_iter)
        except StopIteration:
            self.response_thread.start()
            self.end_test()

    def end_test(self):
        self.inter_trial = False
        self.descriptionLabel.setText("Saving...")
        self.evaluation = Evaluation()
        self.evaluation.evaluate(self.data)

        self.evaluation.set_pic_geometry(self.pic_geometry)
        self.evaluation.set_central_widget_geometry(self.central_widget_geometry)

        self.save_thread.set_evaluation(self.evaluation)
        self.save_thread.start()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.start:
                self.start_test()
            elif self.inter_trial:
                self.start_trial()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.tracker:
            self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback)
        event.accept()

    def show_histogram_calibration(self, histogram, calibration):
        self.picRight.setPixmap(histogram)
        self.picLeft.setPixmap(calibration)

    @QtCore.pyqtSlot()
    def saving_complete(self):
        if self.success_counter >= 7:
            self.descriptionLabel.setText("Successfully classified 7 in a row. Test has ended.")
        else:
            self.descriptionLabel.setText("Saving complete.")

    @QtCore.pyqtSlot()
    def remove_response(self):
        self.picShow.setStyleSheet("")
        self.picShow.clear()
        if not self.inter_trial and not self.start:
            try:
                self.directory = next(self.sequence_iter)
                self.load_dataset(self.directory[0], self.directory[1], self.directory[2])
            except StopIteration:
                self.descriptionLabel.setText("Completed all tests.")
                self.picShow.setText("You're done. Good job.")
                return

            self.start = True
            self.picShow.setText("Start next test by pressing Enter.")

    def start_test(self):
        central_widget_global_top_left = self.centralWidget.mapToGlobal(QPoint(0, 0))
        pic_global_top_left = self.centralWidget.mapToGlobal(self.picShow.geometry().topLeft())

        self.central_widget_geometry = (central_widget_global_top_left.x(),
                                        central_widget_global_top_left.y(),
                                        self.centralWidget.geometry().width(),
                                        self.centralWidget.geometry().height())
        self.pic_geometry = (pic_global_top_left.x(),
                             pic_global_top_left.y(),
                             self.picShow.geometry().width(),
                             self.picShow.geometry().height())

        self.success_counter = 0

        self.inter_trial = True
        self.start = False
        self.start_trial()

    def start_trial(self):
        # remove background
        self.remove_response()
        self.descriptionLabel.clear()
        if self.tracker:
            self.calibration_data = self.eyetracker_data[-30:]
            self.eyetracker_data = []
        # enable buttons
        self._disable_buttons(False)
        # start timer
        self.timer_start = current_micro_time()
        # show next picture
        self.picRight.clear()
        self.picLeft.clear()
        self.pixmap = QPixmap(self.pic[0]).scaledToWidth(512)
        self.picShow.setPixmap(self.pixmap)

    @QtCore.pyqtSlot()
    def categoryTrue(self):
        self.end_trial(1)

    @QtCore.pyqtSlot()
    def categoryFalse(self):
        self.end_trial(0)

    @QtCore.pyqtSlot()
    def reset(self):
        self.start = True
        self.remove_response()
        self.picShow.setPixmap(self.calibrate_pixmap)
        self.picLeft.clear()
        self.picRight.clear()
        self.pics = self.dataset.data
        self.pics_iter = iter(self.pics)
        self.pic = next(self.pics_iter)
        self.data = []
        self.listPicturesTrue.clear()
        self.listPicturesFalse.clear()
        self._disable_buttons(True)
        self.descriptionLabel.setText("Press Enter key to start.")

    @QtCore.pyqtSlot()
    def selectDirectory(self):
        self.directory = str(QFileDialog.getExistingDirectory(self, "Select Directory")) + '/'
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuCamRot_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 1)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuCamRot_5(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 5)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuRanBoa_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 1)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuRanBoa_5(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 5)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuRotIma_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 1)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuRotIma_5(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 5)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuSVRT_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 1)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuSVRT_19(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 19)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuSVRT_20(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 20)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuSVRT_21(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 21)
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuPSVRT_SD(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sd')
        self.load_dataset(self.directory)

    @QtCore.pyqtSlot()
    def menuPSVRT_SR(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sr')
        self.load_dataset(self.directory)

    def _disable_buttons(self, disable):
        self.pushButtonFalse.setDisabled(disable)
        self.pushButtonTrue.setDisabled(disable)

    def _create_list_item(self):
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(QSize(256, 256))
        icon = QtGui.QIcon()
        icon.addPixmap(self.pixmap.scaledToWidth(256))
        item.setIcon(icon)

        if self.pic[1] == 1:
            self.listPicturesTrue.insertItem(0, item)
        else:
            self.listPicturesFalse.insertItem(0, item)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindowUI()
    mw.show()
    app.exec()
    sys.exit()
