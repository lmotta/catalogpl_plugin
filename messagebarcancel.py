# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : MessageBar Cancel
Description          : Use to add cancel in messagebar
Date                 : November, 2017
copyright            : (C) 2017 by Luiz Motta
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
import os

from PyQt4 import QtCore, QtGui
from qgis import core as QgsCore, gui as QgsGui


class MessageBarCancelProgress(QtCore.QObject):
  def __init__(self, pluginName, msgBar, msg, maximum, funcKill, hasProgressFile=False):
    def initGui():
      self.pb = QtGui.QProgressBar( self.msgBar )
      self.pb.setAlignment( QtCore.Qt.AlignLeft )
      self.lb = QtGui.QLabel( self.msgBar )
      self.tbCancel = QtGui.QToolButton( self.msgBar )
      self.tbCancel.setIcon( QgsCore.QgsApplication.getThemeIcon( "/mActionCancelAllEdits.svg" ) )
      self.tbCancel.setToolTip( "Cancel download")
      self.tbCancel.setText( "Cancel")
      self.tbCancel.setToolButtonStyle( QtCore.Qt.ToolButtonTextBesideIcon )
      self.widget = self.msgBar.createMessage( pluginName, msg )

      widgets = [ self.tbCancel, self.lb, self.pb ]
      lyt = self.widget.layout()
      for item in widgets:
        lyt.addWidget( item )
      del widgets[:]

      if hasProgressFile:
        self.pbFile = QtGui.QProgressBar( self.msgBar )
        self.pbFile.setAlignment( QtCore.Qt.AlignLeft )
        self.pbFile.setValue( 1 )
        lyt.addWidget( self.pbFile )

    super(MessageBarCancelProgress, self).__init__()
    ( self.msgBar, self.maximum ) = ( msgBar, maximum )
    self.pb = self.lb = self.widget = self.isCancel = self.pbFile = None
    initGui()
    self.tbCancel.clicked.connect( self.clickedCancel )
    self.pb.destroyed.connect( self.destroyed)

    self.msgBar.pushWidget( self.widget, QgsGui.QgsMessageBar.INFO )
    self.pb.setValue( 1 )
    self.pb.setMaximum( maximum )
    self.isCancel = False
    self.kill = funcKill

  def step(self, value, image=None):
    if self.pb is None:
      return
    
    self.pb.setValue( value )
    self.lb.setText( "%d/%d" % ( value, self.maximum ) )
    if not image is None:
      self.pbFile.setToolTip( image )
      self.pbFile.setFormat( "%p% " + os.path.split( image )[-1] )

  @QtCore.pyqtSlot(QtCore.QObject)
  def destroyed(self, obj):
    self.pb = None

  @QtCore.pyqtSlot(bool)
  def clickedCancel(self, checked):
    if self.pb is None:
      return
    self.kill()
    self.isCancel = True

  @QtCore.pyqtSlot(int, int)
  def stepFile(self, bytesReceived, bytesTotal):
    if self.pb is None:
      return

    self.pbFile.setMaximum( bytesTotal )
    self.pbFile.setValue( bytesReceived )


class MessageBarCancel(QtCore.QObject):
  def __init__(self, pluginName, msgBar, msg, funcKill):
    def initGui():
      self.tbCancel = QtGui.QToolButton( msgBar )
      self.tbCancel.setIcon( QgsCore.QgsApplication.getThemeIcon( '/mActionCancelAllEdits.svg' ) )
      self.tbCancel.setText( "Cancel")
      self.tbCancel.setToolButtonStyle( QtCore.Qt.ToolButtonTextBesideIcon )
      self.widget = msgBar.createMessage( pluginName, msg )

      lyt = self.widget.layout()
      lyt.addWidget( self.tbCancel )

    super(MessageBarCancel, self).__init__()
    self.widget = self.isCancel = None
    initGui()
    self.tbCancel.clicked.connect( self.clickedCancel )

    msgBar.pushWidget( self.widget, QgsGui.QgsMessageBar.INFO )
    self.isCancel = False
    self.kill = funcKill

  def message(self, msg):
    if not self.isCancel:
      self.widget.setText( msg )

  @QtCore.pyqtSlot(bool)
  def clickedCancel(self, checked):
    self.kill()
    self.isCancel = True
