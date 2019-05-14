#!/bin/bash
SOURCE_FILE="gui/masterGUI/mainwindow.ui"
TARGET_FILE="project/gui/mainwindow.py"

pyuic5 $SOURCE_FILE -o $TARGET_FILE
