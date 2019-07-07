import sys
import time

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog

from Evaluation import Evaluation
from Utilities import DatasetLoader
from gui.mainwindow import Ui_MainWindow

import tobii_research as tr

class MainWindowUI(QtWidgets.QMainWindow, Ui_MainWindow):
    evaluation = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.directory = DatasetLoader.DATASETS_PATH
        self.pics, self.pics_iter = None, None
        self.pic, self.pixmap = None, None
        self.duration = 0
        self.done = False
        self.dataset = None
        self.data = []
        self.tracker = None
        self.eyetracker_data = []

        self.load_dataset()
        self.next_picture()
        self.timer = time.perf_counter()
        self.init_eyetracker()

    def setupUi(self, mainWindow):
        super().setupUi(mainWindow)

    def reset_timer(self):
        self.duration = round(time.perf_counter() - self.timer, 4)
        self.timer = time.perf_counter()

    def classify(self, category):
        self.data.append([self.pic, category, self.duration])

    def next_picture(self):
        try:
            self.pic = next(self.pics_iter)
            self.pixmap = QPixmap(self.pic[0])
            self.picShow.setPixmap(self.pixmap)

        except StopIteration:
            if self.tracker:
                self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback)

            self.done = True
            self.pushButtonTrue.setDisabled(True)
            self.pushButtonFalse.setDisabled(True)
            self.picShow.hide()

            self.evaluation = Evaluation(self.data, self.eyetracker_data)
            self.evaluation.save_to_file()
            if self.eyetracker_data:
                self.evaluation.save_tracker_data_to_file()

    def load_dataset(self):
        self.dataset = DatasetLoader.load_problem(self.directory, True)
        self.pics = self.dataset.data
        self.pics_iter = iter(self.pics)
        self.pushButtonTrue.setText(self.dataset.text1)
        self.pushButtonFalse.setText(self.dataset.text2)
        self.descriptionLabel.setText(self.dataset.description)

    def gaze_data_callback(self, gaze_data):
        print(gaze_data)
        self.eyetracker_data.append(gaze_data)

    def init_eyetracker(self):
        found = tr.find_all_eyetrackers()
        if found:
            self.tracker = found[0]
            self.tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)
        else:
            print("No EyeTrackers found.")


    @QtCore.pyqtSlot()
    def categoryTrue(self):
        self.reset_timer()
        self.classify(1)

        item = QtWidgets.QListWidgetItem()
        icon = QtGui.QIcon()
        icon.addPixmap(self.pixmap)
        item.setIcon(icon)
        self.listPicturesTrue.addItem(item)

        self.next_picture()

    @QtCore.pyqtSlot()
    def categoryFalse(self):
        self.reset_timer()
        self.classify(0)

        item = QtWidgets.QListWidgetItem()
        icon = QtGui.QIcon()
        icon.addPixmap(self.pixmap)
        item.setIcon(icon)
        self.listPicturesFalse.addItem(item)

        self.next_picture()

    @QtCore.pyqtSlot()
    def reset(self):
        self.picShow.show()
        self.pushButtonTrue.setDisabled(False)
        self.pushButtonFalse.setDisabled(False)
        self.pics_iter = iter(self.pics)
        self.data = []
        self.listPicturesTrue.clear()
        self.listPicturesFalse.clear()

        self.next_picture()
        self.timer = time.perf_counter()

    @QtCore.pyqtSlot()
    def selectDirectory(self):
        self.directory = str(QFileDialog.getExistingDirectory(self, "Select Directory")) + '/'
        self.load_dataset()
        self.reset()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindowUI()
    mw.show()
    app.exec()
    sys.exit()
