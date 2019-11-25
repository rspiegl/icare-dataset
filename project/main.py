import re
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


def current_micro_time(): return tr.get_system_time_stamp()


class Signal(QObject):
    """Gets emitted when saving is complete."""
    sig = pyqtSignal()


class ProcessSignal(QObject):
    """Emits histogram and calibration pixmap when processing is done."""
    sig = pyqtSignal(QPixmap)


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

    def __init__(self, data, geometry):
        QThread.__init__(self)
        self.data = data
        self.geometry = geometry
        self.signal = Signal()

    def run(self):
        dataset_identifier = re.findall(r'([^/]+)/[^/]+\.', self.data[0][0][0])[0]
        timestamp = time.strftime('%m-%d_%H-%M', time.localtime())
        dir_path = 'processing/'
        dic = {'geometry': self.geometry, 'eyetracking': self.data}

        with open(dir_path + dataset_identifier + '_' + timestamp + '.txt', 'w') as file:
            file.write(str(dic))

        self.signal.sig.emit()


class ProcessThread(QThread):
    """Generates histograms for calibration and eyetracking data and then shows it."""

    def __init__(self, calibration_data=None, pic_geometry=None):
        QThread.__init__(self)
        self.data = calibration_data
        self.pic_geometry = pic_geometry
        self.signal = ProcessSignal()

    def set_data(self, data):
        self.data = data

    def set_pic_geometry(self, pic_geometry):
        self.pic_geometry = pic_geometry

    def run(self):
        if self.data:
            processed_cali = Processor.process_picture_eyetracking_data(self.data)
            cali_heat = Processor.get_coords_for_heatmap(processed_cali)
            if not cali_heat:
                print("no data after creation of calibration")
                return
            cali_trim = Processor.trim_heatmap(cali_heat, self.pic_geometry)
            calibration = Processor.create_calibration_histogram(cali_trim, full_path='cali')
            calibration = QPixmap(calibration)

            self.signal.sig.emit(calibration)


class MainWindowUI(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.test_sequence = [
            (DatasetLoader.DATASET_CATDOG, 10, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sr'), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 1), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 5), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 1), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sd'), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 19), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 5), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 1), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 20), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 21), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 5), 35, True),
            (DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 1), 35, True),
        ]
        self.dataset_order = [x[0] for x in self.test_sequence]
        self.pics, self.pics_iter, self.sequence_iter = None, None, None
        self.pic, self.pixmap, self.directory = None, None, None
        self.timer_start, self.timer_end = 0, 0
        self.success_counter = 0
        self.done = False
        self.start, self.inter_trial = True, False
        self.dataset = None
        self.evaluation = None
        self.data = []
        self.tracker = None
        self.eyetracker_data, self.calibration_data = [], []
        self.calibrate_pixmap = QPixmap(DatasetLoader.CALIBRATE_PICTURE)
        self.pic_geometry = None

        self.process_thread, self.save_thread = None, None
        self.response_thread = SleepThread(1)
        self.response_thread.signal.sig.connect(self.remove_response)
        self.inter_trial_thread = SleepThread(0.5)
        self.inter_trial_thread.signal.sig.connect(self.switch_intertrial)

        self.init_eyetracker()
        self.restart()

    def setupUi(self, main_window):
        super().setupUi(main_window)
        self.listPicturesFalse.setSpacing(2)
        self.listPicturesTrue.setSpacing(2)

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

        return found

    def start_test(self):
        pic_global_top_left = self.picShow.mapToGlobal(QPoint(0, 0))
        self.pic_geometry = (pic_global_top_left.x(),
                             pic_global_top_left.y(),
                             self.picShow.geometry().width(),
                             self.picShow.geometry().height())

        self.success_counter = 0

        self.start = False
        self.inter_trial = True
        self.picShow.setPixmap(self.calibrate_pixmap)

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
        self.picLeft.clear()
        self.pixmap = QPixmap(self.pic[0]).scaledToWidth(512)
        self.picShow.setPixmap(self.pixmap)

    def classify(self, category):
        duration = self.timer_end - self.timer_start
        self.data.append([self.pic, category, duration, self.eyetracker_data, self.calibration_data])
        self.eyetracker_data = []

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
        # disable buttons
        self._disable_buttons(True)

        try:
            if self.success_counter >= 7:
                raise StopIteration
            self.pic = next(self.pics_iter)
            self.inter_trial = False
            self.inter_trial_thread.start()
        except StopIteration:
            self.response_thread.start()
            self.end_test()

    def end_test(self):
        self.inter_trial = False
        self.descriptionLabel.setText("Saving...")

        self.save_thread = SaveThread(self.data, self.pic_geometry)
        self.save_thread.signal.sig.connect(self.saving_complete)
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

    def show_calibration(self, calibration):
        self.picLeft.setPixmap(calibration)
        self.inter_trial = True

    def switch_intertrial(self):
        self.inter_trial = True

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
                self._load_dataset_iter()
            except StopIteration:
                self.descriptionLabel.setText("Completed all tests.")
                self.picShow.setText("You're done. Good job.")
                return
            self.picShow.setText("Time for questions...\nAfterwards recalibrate please..")
            self.start = True

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
        self.picShow.setText("Calibrate the eye tracker!")
        self.picShow.setStyleSheet("font: 22pt \"Cantarell\";")
        self.picLeft.clear()
        self.pics = self.dataset.data
        self.pics_iter = iter(self.pics)
        self.pic = next(self.pics_iter)
        self.data = []
        self.listPicturesTrue.clear()
        self.listPicturesFalse.clear()
        self._disable_buttons(True)

    @QtCore.pyqtSlot()
    def restart(self):
        self.sequence_iter = iter(self.test_sequence)
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def connectEyeTracker(self):
        if self.init_eyetracker():
            self.descriptionLabel.setText("Connected to eyetracker.")
        else:
            self.descriptionLabel.setText("Couldn't connect to eyetracker.")

    @QtCore.pyqtSlot()
    def selectDirectory(self):
        self.directory = (str(QFileDialog.getExistingDirectory(self, "Select Directory")) + '/', 35, True)
        self.sequence_iter = iter([])
        self.load_dataset(self.directory[0], self.directory[1], self.directory[2])

    @QtCore.pyqtSlot()
    def menuCamRot_1(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 1)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuCamRot_5(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 5)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuRanBoa_1(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 1)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuRanBoa_5(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 5)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuRotIma_1(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 1)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuRotIma_5(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 5)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuSVRT_1(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 1)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuSVRT_19(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 19)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuSVRT_20(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 20)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuSVRT_21(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 21)
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuPSVRT_SD(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sd')
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    @QtCore.pyqtSlot()
    def menuPSVRT_SR(self):
        dataset_path = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT, 'sr')
        self.sequence_iter = iter(self.test_sequence[self.dataset_order.index(dataset_path):])
        self._load_dataset_iter()

    def _load_dataset_iter(self):
        self.directory = next(self.sequence_iter)
        self.load_dataset(self.directory[0], self.directory[1], self.directory[2])

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
