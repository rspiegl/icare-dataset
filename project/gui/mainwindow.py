# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui/masterGUI/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 720)
        MainWindow.setMinimumSize(QtCore.QSize(1280, 720))
        MainWindow.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.widgetPics = QtWidgets.QWidget(self.centralWidget)
        self.widgetPics.setGeometry(QtCore.QRect(30, 10, 1201, 331))
        self.widgetPics.setObjectName("widgetPics")
        self.picShow = QtWidgets.QLabel(self.widgetPics)
        self.picShow.setGeometry(QtCore.QRect(470, 30, 256, 256))
        self.picShow.setMinimumSize(QtCore.QSize(256, 256))
        self.picShow.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.picShow.setFrameShadow(QtWidgets.QFrame.Plain)
        self.picShow.setScaledContents(True)
        self.picShow.setAlignment(QtCore.Qt.AlignCenter)
        self.picShow.setObjectName("picShow")
        self.widgetButtons = QtWidgets.QWidget(self.centralWidget)
        self.widgetButtons.setGeometry(QtCore.QRect(30, 610, 1201, 41))
        self.widgetButtons.setObjectName("widgetButtons")
        self.pushButtonCat1 = QtWidgets.QPushButton(self.widgetButtons)
        self.pushButtonCat1.setGeometry(QtCore.QRect(289, 10, 91, 27))
        self.pushButtonCat1.setObjectName("pushButtonCat1")
        self.pushButtonCat2 = QtWidgets.QPushButton(self.widgetButtons)
        self.pushButtonCat2.setGeometry(QtCore.QRect(750, 10, 91, 27))
        self.pushButtonCat2.setObjectName("pushButtonCat2")
        self.listWidgetCat1 = QtWidgets.QListWidget(self.centralWidget)
        self.listWidgetCat1.setGeometry(QtCore.QRect(30, 340, 561, 271))
        self.listWidgetCat1.setStyleSheet("gridline-color: rgb(0, 0, 0);\n"
"background-color: rgb(186, 189, 182);")
        self.listWidgetCat1.setFrameShape(QtWidgets.QFrame.Box)
        self.listWidgetCat1.setFrameShadow(QtWidgets.QFrame.Plain)
        self.listWidgetCat1.setLineWidth(2)
        self.listWidgetCat1.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listWidgetCat1.setIconSize(QtCore.QSize(128, 128))
        self.listWidgetCat1.setViewMode(QtWidgets.QListView.IconMode)
        self.listWidgetCat1.setObjectName("listWidgetCat1")
        self.listWidgetCat2 = QtWidgets.QListWidget(self.centralWidget)
        self.listWidgetCat2.setGeometry(QtCore.QRect(670, 340, 561, 271))
        self.listWidgetCat2.setStyleSheet("background-color: rgb(186, 189, 182);\n"
"gridline-color: rgb(0, 0, 0);")
        self.listWidgetCat2.setFrameShape(QtWidgets.QFrame.Box)
        self.listWidgetCat2.setFrameShadow(QtWidgets.QFrame.Plain)
        self.listWidgetCat2.setLineWidth(2)
        self.listWidgetCat2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listWidgetCat2.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.listWidgetCat2.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.listWidgetCat2.setIconSize(QtCore.QSize(128, 128))
        self.listWidgetCat2.setViewMode(QtWidgets.QListView.IconMode)
        self.listWidgetCat2.setObjectName("listWidgetCat2")
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1280, 24))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QtWidgets.QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtWidgets.QToolBar(MainWindow)
        self.mainToolBar.setEnabled(False)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionSelectDirectory = QtWidgets.QAction(MainWindow)
        self.actionSelectDirectory.setObjectName("actionSelectDirectory")
        self.actionReset = QtWidgets.QAction(MainWindow)
        self.actionReset.setObjectName("actionReset")
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionSelectDirectory)
        self.menuFile.addAction(self.actionReset)
        self.menuFile.addAction(self.actionExit)
        self.menuBar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.pushButtonCat2.clicked.connect(MainWindow.category2)
        self.pushButtonCat1.clicked.connect(MainWindow.category1)
        self.actionReset.triggered.connect(MainWindow.reset)
        self.actionSelectDirectory.triggered.connect(MainWindow.selectDirectory)
        self.actionExit.triggered.connect(MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Study Foo Bar"))
        self.picShow.setText(_translate("MainWindow", "TextLabel"))
        self.pushButtonCat1.setText(_translate("MainWindow", "Category 1"))
        self.pushButtonCat2.setText(_translate("MainWindow", "Category 2"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionSelectDirectory.setText(_translate("MainWindow", "Select Directory"))
        self.actionReset.setText(_translate("MainWindow", "Reset"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))


