import math
import sys
import time

import tobii_research as tr
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog

from Utilities import DatasetLoader
from gui.mainwindow import Ui_MainWindow
from processing.Evaluation import Evaluation

MODE_TEST = 0
MODE_REPLAY = 1


def current_micro_time(): return tr.get_system_time_stamp()


class SleepSignal(QObject):
    """A signal that gets emitted when the Intertrial Interval is over."""
    sig = pyqtSignal()


class SaveSignal(QObject):
    """Gets emitted when saving is complete."""
    sig = pyqtSignal()


class SleepThread(QThread):
    """A class used to signal the GUI when the Intertrial Interval is over."""

    def __init__(self, sleep, parent=None):
        QThread.__init__(self, parent)
        self.sleep = sleep
        self.signal = SleepSignal()

    def run(self):
        time.sleep(self.sleep)
        self.signal.sig.emit()


class SaveThread(QThread):
    """Handles the saving of data that, for longer trials, can take over half a second."""

    def __init__(self):
        QThread.__init__(self)
        self.evaluation = None
        self.signal = SaveSignal()

    def set_evaluation(self, evaluation):
        self.evaluation = evaluation

    def run(self):
        self.evaluation.save_to_file()
        self.signal.sig.emit()


class MainWindowUI(QtWidgets.QMainWindow, Ui_MainWindow):
    evaluation = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 1)
        self.pics, self.pics_iter = None, None
        self.pic, self.pixmap = None, None
        self.timer_start, self.timer_end = 0, 0
        self.nan_counter = 0
        self.done = False
        self.start = True
        self.dataset = None
        self.data = []
        self.tracker = None
        self.eyetracker_data = []

        self.iti_thread = SleepThread(1)
        self.response_thread = SleepThread(1)
        self.nan_test_thread = SleepThread(1)
        self.start_test_thread = SleepThread(2)
        self.save_thread = SaveThread()
        self.iti_thread.signal.sig.connect(self.start_trial)
        self.response_thread.signal.sig.connect(self.remove_response)
        self.nan_test_thread.signal.sig.connect(self.nan_test_end)
        self.start_test_thread.signal.sig.connect(self.start_test)
        self.save_thread.signal.sig.connect(self.saving_complete)

        self.init_eyetracker()
        self.load_dataset(self.directory, 2, True)

    def setupUi(self, mainWindow):
        super().setupUi(mainWindow)

    def classify(self, category):
        duration = self.timer_end - self.timer_start
        self.data.append([self.pic, category, duration, (self.timer_start, self.timer_end), self.eyetracker_data])
        self.eyetracker_data = []

    def load_dataset(self, dir_path, number, balance):
        self.dataset = DatasetLoader.load_problem(dir_path, number=number, balance=balance)
        self.reset()

    def gaze_data_callback(self, gaze_data):
        self.eyetracker_data.append(gaze_data)

    def gaze_data_callback_test(self, gaze_data):
        self.eyetracker_data.append(gaze_data)
        if math.isnan(gaze_data['left_pupil_diameter']):
            self.nan_counter += 1

    def init_eyetracker(self):
        found = tr.find_all_eyetrackers()
        if found:
            self.tracker = found[0]
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
            classified = "Correct!"
            self.picShow.setStyleSheet("background-color: rgb(138, 226, 52);")  # light green
        else:
            classified = "Incorrect"
            self.picShow.setStyleSheet("background-color: rgb(255, 51, 51);")  # light red
        self.descriptionLabel.setText(classified)
        # disable buttons
        self._disable_buttons(True)
        # sleep 1s
        try:
            self.pic = next(self.pics_iter)
            self.iti_thread.start()
        except StopIteration:
            self.response_thread.start()
            self.end_test()

    def end_test(self):
        if self.tracker:
            self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback)
        self.descriptionLabel.setText("Saving...")
        self.evaluation = Evaluation()
        self.evaluation.evaluate(self.data)

        pic_global_top_left = self.centralWidget.mapToGlobal(self.picShow.geometry().topLeft())
        self.evaluation.set_pic_geometry((pic_global_top_left.x(),
                                          pic_global_top_left.y(),
                                          self.picShow.geometry().width(),
                                          self.picShow.geometry().height()))

        central_widget_global_top_left = self.centralWidget.mapToGlobal(QPoint(0, 0))
        self.evaluation.set_central_widget_geometry((central_widget_global_top_left.x(),
                                                     central_widget_global_top_left.y(),
                                                     self.centralWidget.geometry().width(),
                                                     self.centralWidget.geometry().height()))

        self.save_thread.set_evaluation(self.evaluation)
        self.save_thread.start()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.start:
                self.start = False
                if self.tracker:
                    self.nan_test()
                else:
                    self.start_trial()
        else:
            super().keyPressEvent(event)

    def nan_test(self):
        pixmap = QPixmap(DatasetLoader.EXAMPLE_PICTURE)
        self.picShow.setPixmap(pixmap)
        self.nan_counter = 0
        self.tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback_test, as_dictionary=True)

        self.descriptionLabel.setText("Checking Eyetracker setup.")
        self.nan_test_thread.start()

    @QtCore.pyqtSlot()
    def nan_test_end(self):
        self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback_test)
        self.picShow.clear()
        if self.nan_counter > (len(self.eyetracker_data)/2):
            self.descriptionLabel.setText("Check Eyetracker setup -- too few values.")
            self.start = True
        else:
            self.descriptionLabel.setText("Everything is fine -- Test starts in 2 seconds.")
            self.start_test_thread.start()

    @QtCore.pyqtSlot()
    def saving_complete(self):
        self.descriptionLabel.setText("Saving complete.")

    @QtCore.pyqtSlot()
    def remove_response(self):
        self.picShow.setStyleSheet("")
        
    @QtCore.pyqtSlot()
    def start_test(self):
        if self.tracker:
            self.tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)
        self.start_trial()

    @QtCore.pyqtSlot()
    def start_trial(self):
        # remove background
        self.remove_response()
        self.descriptionLabel.clear()
        if self.tracker:
            self.eyetracker_data = []
        # enable buttons
        self._disable_buttons(False)
        # start timer
        self.timer_start = current_micro_time()
        # show next picture
        self.pixmap = QPixmap(self.pic[0])
        self.picShow.setPixmap(self.pixmap)

    @QtCore.pyqtSlot()
    def categoryTrue(self):
        self.end_trial(1)

    @QtCore.pyqtSlot()
    def categoryFalse(self):
        self.end_trial(0)

    @QtCore.pyqtSlot()
    def reset(self):
        self.picShow.clear()
        self.pics = self.dataset.data
        self.pics_iter = iter(self.pics)
        self.pic = next(self.pics_iter)
        self.data = []
        self.listPicturesTrue.clear()
        self.listPicturesFalse.clear()
        self.start = True
        self._disable_buttons(True)
        self.descriptionLabel.setText("Press Enter key to start.")

    @QtCore.pyqtSlot()
    def selectDirectory(self):
        self.directory = str(QFileDialog.getExistingDirectory(self, "Select Directory")) + '/'
        self.load_dataset(self.directory, 50, True)
        self.reset()

    @QtCore.pyqtSlot()
    def menuCamRot_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 1)
        self.load_dataset(self.directory, 50, True)
        self.reset()

    @QtCore.pyqtSlot()
    def menuCamRot_5(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 5)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuCamRot_10(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_CAMROT, 10)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuRanBoa_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 1)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuRanBoa_5(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 5)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuRanBoa_10(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_RANBOA, 10)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuRotIma_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 1)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuRotIma_5(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_ROTIMA, 5)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_1(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 1)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_5(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 5)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_7(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 7)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_15(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 15)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_19(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 19)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_20(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 20)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_21(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 21)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuSVRT_22(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_SVRT, 22)
        self.load_dataset(self.directory, 50, True)

    @QtCore.pyqtSlot()
    def menuPSVRT_SD(self):
        self.directory = DatasetLoader.get_dataset_path(DatasetLoader.IDENTIFIER_PSVRT)
        self.load_dataset(self.directory, 50, True)

    def _disable_buttons(self, disable):
        self.pushButtonFalse.setDisabled(disable)
        self.pushButtonTrue.setDisabled(disable)

    def _create_list_item(self):
        item = QtWidgets.QListWidgetItem()
        icon = QtGui.QIcon()
        icon.addPixmap(self.pixmap)
        item.setIcon(icon)
        if self.pic[1] == 1:
            self.listPicturesTrue.addItem(item)
        else:
            self.listPicturesFalse.addItem(item)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindowUI()
    mw.show()
    app.exec()
    sys.exit()
