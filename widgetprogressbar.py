#!/usr/bin/python3
# # -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Progress Bar 
Description          : Class for progress bar with  cancel
Date                 : April, 2019
copyright            : (C) 2019 by Luiz Motta
email                : motta.luiz@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import (
    pyqtSlot, pyqtSignal
)
from qgis.PyQt.QtWidgets import (
    QWidget, QProgressBar, QPushButton,
    QStyle,
    QVBoxLayout, QHBoxLayout,
)

class WidgetProgressBar(QWidget):
    buttonCancelClicked = pyqtSignal()
    def __init__(self, parent):
        def setupGui():
            lytMain = QVBoxLayout()
            # Progress Count and Cancel
            lyt = QHBoxLayout()
            self.pbCount = QProgressBar( self )
            self.pbCount.setRange(0,100)
            self.pbCount.setTextVisible(True)
            lyt.addWidget( self.pbCount )
            w = QPushButton('Cancel', self)
            w.setObjectName('objCancel')
            w.setIcon( self.style().standardIcon( QStyle.SP_DialogCancelButton ) )
            lyt.addWidget( w )
            lytMain.addLayout( lyt )
            # Progress file
            self.pbFile = QProgressBar( self )
            self.pbFile.setRange(0,100)
            self.pbFile.setTextVisible(True)
            lytMain.addWidget( self.pbFile )
            self.setLayout( lytMain )

        super().__init__( parent )
        self.pbCount, self.pbFile = None, None
        setupGui()
        self.nameProcess = None
        self.nameFile = None
        self.findChild( QPushButton, 'objCancel').clicked.connect( self._onCancel )

    def setHasFile(self, hasFile):
        self.pbFile.show() if hasFile else self.pbFile.hide()

    @pyqtSlot(bool)
    def _onCancel(self, checked):
        self.buttonCancelClicked.emit()

    @pyqtSlot(str)
    def currentProcess(self, name):
        self.nameProcess = name

    @pyqtSlot(str)
    def currentFile(self, name):
        self.nameFile = name

    @pyqtSlot()
    def resetCount(self):
        self.pbCount.reset()

    @pyqtSlot()
    def resetFile(self):
        self.pbFile.reset()

    @pyqtSlot(int, int, int)
    def processingCount(self, countData, totalData, percent):
        msg = f"{self.nameProcess}: {countData}/{totalData} ( {percent}% )"
        self.pbCount.setValue(  percent )
        self.pbCount.setFormat( msg )

    @pyqtSlot(int, int, int)
    def receivedBytesFile(self, countData, totalData, percent):
        countData /= 1048576 # bytes -> MB
        totalData /= 1048576 # bytes -> MB
        msg = f"{self.nameFile}: {countData:.2f}/{totalData:.2f} MB ( {percent}% )"
        self.pbFile.setValue(  percent )
        self.pbFile.setFormat( msg )
