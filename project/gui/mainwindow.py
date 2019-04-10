# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../../gui/masterGUI/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 720)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.widgetPics = QtWidgets.QWidget(self.centralWidget)
        self.widgetPics.setGeometry(QtCore.QRect(20, 20, 1201, 581))
        self.widgetPics.setObjectName("widgetPics")
        self.picLeft = QtWidgets.QLabel(self.widgetPics)
        self.picLeft.setGeometry(QtCore.QRect(70, 110, 421, 341))
        self.picLeft.setObjectName("picLeft")
        self.picRight = QtWidgets.QLabel(self.widgetPics)
        self.picRight.setGeometry(QtCore.QRect(680, 110, 421, 341))
        self.picRight.setObjectName("picRight")
        self.labelTimer = QtWidgets.QLabel(self.centralWidget)
        self.labelTimer.setGeometry(QtCore.QRect(1136, 600, 141, 20))
        self.labelTimer.setObjectName("labelTimer")
        self.widget = QtWidgets.QWidget(self.centralWidget)
        self.widget.setGeometry(QtCore.QRect(1, 621, 1281, 29))
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButtonTrue = QtWidgets.QPushButton(self.widget)
        self.pushButtonTrue.setObjectName("pushButtonTrue")
        self.horizontalLayout.addWidget(self.pushButtonTrue)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pushButtonFalse = QtWidgets.QPushButton(self.widget)
        self.pushButtonFalse.setObjectName("pushButtonFalse")
        self.horizontalLayout.addWidget(self.pushButtonFalse)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1280, 24))
        self.menuBar.setObjectName("menuBar")
        self.menuTesting = QtWidgets.QMenu(self.menuBar)
        self.menuTesting.setObjectName("menuTesting")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtWidgets.QToolBar(MainWindow)
        self.mainToolBar.setEnabled(False)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.menuTesting.addAction(self.actionOpen)
        self.menuBar.addAction(self.menuTesting.menuAction())

        self.retranslateUi(MainWindow)
        self.pushButtonFalse.clicked.connect(MainWindow.resetTimer)
        self.pushButtonTrue.clicked.connect(MainWindow.resetTimer)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.picLeft.setText(_translate("MainWindow", "TextLabel"))
        self.picRight.setText(_translate("MainWindow", "TextLabel"))
        self.labelTimer.setText(_translate("MainWindow", "TextLabel"))
        self.pushButtonTrue.setText(_translate("MainWindow", "True"))
        self.pushButtonFalse.setText(_translate("MainWindow", "False"))
        self.menuTesting.setTitle(_translate("MainWindow", "Testing"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))


