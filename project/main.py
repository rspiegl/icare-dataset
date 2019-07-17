import sys
import time

import tobii_research as tr
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog

from Evaluation import Evaluation
from Utilities import DatasetLoader
from gui.mainwindow import Ui_MainWindow


def current_micro_time(): return tr.get_system_time_stamp()


class ItiSignal(QObject):
    """A signal that gets emitted when the Intertrial Interval is over."""
    sig = pyqtSignal()


class SaveSignal(QObject):
    """Gets emitted when saving is complete."""
    sig = pyqtSignal()


class ItiThread(QThread):
    """A class used to signal the GUI when the Intertrial Interval is over."""
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.signal = ItiSignal()

    def run(self):
        time.sleep(1)
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
        if self.evaluation.tracker_data:
            self.evaluation.save_tracker_data_to_file()
        self.signal.sig.emit()


class MainWindowUI(QtWidgets.QMainWindow, Ui_MainWindow):
    evaluation = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.directory = DatasetLoader.DATASETS_PATH
        self.pics, self.pics_iter = None, None
        self.pic, self.pixmap = None, None
        self.timer_start, self.timer_end = 0, 0
        self.done = False
        self.start = True
        self.dataset = None
        self.data = []
        self.tracker = None
        self.eyetracker_data = []

        self.iti_thread = ItiThread()
        self.save_thread = SaveThread()
        self.iti_thread.signal.sig.connect(self.start_trial)
        self.save_thread.signal.sig.connect(self.saving_complete)

        self.load_dataset()
        self.init_eyetracker()

    def setupUi(self, mainWindow):
        super().setupUi(mainWindow)

    def classify(self, category):
        duration = self.timer_end - self.timer_start
        self.data.append([self.pic, category, duration, (self.timer_start, self.timer_end)])

    def load_dataset(self):
        self.dataset = DatasetLoader.load_problem(self.directory, True)
        self.reset()

    def gaze_data_callback(self, gaze_data):
        self.eyetracker_data.append(gaze_data)

    def init_eyetracker(self):
        found = tr.find_all_eyetrackers()
        if found:
            self.tracker = found[0]
        else:
            print("No EyeTrackers found.")

    def end_trial(self, classification: int):
        self.picShow.clear()
        # unsubscribe
        if self.tracker:
            self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback)
        # stop timer
        self.timer_end = current_micro_time()
        # save to data
        self.classify(classification)
        # add to list
        self._create_list_item()
        # display text
        if classification == self.pic[1]:
            classified = "Correct!"
        else:
            classified = "Incorrect"
        self.descriptionLabel.setText(classified)
        # disable buttons
        self._disable_buttons(True)
        # sleep 1s
        try:
            self.pic = next(self.pics_iter)
            self.iti_thread.start()
        except StopIteration:
            self.end_test()

    def start_test(self):
        if self.start:
            self.start = False
            self._disable_buttons(False)
            self.descriptionLabel.clear()
            self.start_trial()

    def end_test(self):
        self.descriptionLabel.setText("Saving...")
        self.evaluation = Evaluation(self.data, self.eyetracker_data)
        self.evaluation.set_pic_geometry((self.picShow.geometry().x(),
                                          self.picShow.geometry().y(),
                                          self.picShow.geometry().width(),
                                          self.picShow.geometry().height()))
        self.save_thread.set_evaluation(self.evaluation)
        self.save_thread.start()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.start_test()
        else:
            super().keyPressEvent(event)

    @QtCore.pyqtSlot()
    def saving_complete(self):
        self.descriptionLabel.setText("Saving complete.")

    @QtCore.pyqtSlot()
    def start_trial(self):
        # enable buttons
        self._disable_buttons(False)
        # start timer
        self.timer_start = current_micro_time()
        # subscribe
        if self.tracker:
            self.tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)
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
        self.load_dataset()
        self.reset()

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
