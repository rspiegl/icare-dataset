import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPixmap
from gui.mainwindow import Ui_MainWindow


class MainWindowUI(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def setupUi(self, mainWindow):
        super().setupUi(mainWindow)

    @QtCore.pyqtSlot()
    def resetTimer(self):
        self.labelTimer.setText("Button pressed")
        pixmap = QPixmap('datasets/problem1/sample_0_0000.png')
        self.picLeft.setPixmap(pixmap)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindowUI()
    mw.show()
    sys.exit(app.exec_())
