# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Manager Login
Description          : Manager login in server
Date                 : April, 2015
copyright            : (C) 2015 by Luiz Motta
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

import qgis

from PyQt4.QtCore import ( Qt, QObject, QMutex, pyqtSignal, pyqtSlot, QEventLoop, QSettings )
from PyQt4.QtGui  import ( QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox )

from apiqtpl import API_PlanetLabs 
from PyQt4.Qt import QMutex

class DialogLoginKey(QDialog):

  def __init__(self, parent, windowTitle, icon=None):
    def initGui():
      def connect():
        buttonLogin.clicked.connect( self.onLogin )
        self.textKey.textEdited.connect( self.onTextEdited )
      #
      self.setWindowTitle( windowTitle )
      if not icon is None:
        self.setWindowIcon( icon )
      labelKey = QLabel( "Key: ", self )
      self.labelError = QLabel( self )
      self.labelError.hide()
      self.textKey = QLineEdit( self )
      self.textKey.setEchoMode( QLineEdit.Password )
      buttonLogin = QPushButton( "Login", self )
      connect()
      layout = QVBoxLayout( self )
      layout.addWidget( labelKey )
      layout.addWidget( self.textKey )
      layout.addWidget( buttonLogin )
      layout.addWidget( self.labelError )
      #
      self.resize( 4 * len( windowTitle ) + 200 , 30 )
    #
    super( DialogLoginKey, self ).__init__( parent )
    self.apiPL = API_PlanetLabs()
    self.responsePL = None
    initGui()

  @pyqtSlot( bool )
  def onLogin(self, checked):
    def setFinishedPL(response):
      self.responsePL = response
      loop.quit()
    
    def setKeyResponse():
      if self.responsePL['isOk']:
        self.accept()
      else:
        self.labelError.setTextFormat( Qt.RichText )
        msg = "<font color=\"red\"><b><i>Invalid key! %s</i></b></font>" % self.responsePL['message'] 
        self.labelError.setText( msg )
        self.labelError.show()

    key = self.textKey.text().encode('ascii', 'ignore')
    self.responsePL = None
    loop = QEventLoop()
    self.apiPL.setKey( key, setFinishedPL )
    loop.exec_()
    setKeyResponse()

  @pyqtSlot( str )
  def onTextEdited(self, text ):
    if self.labelError.isHidden():
      return
    self.labelError.hide()


class ManagerLoginKey(QObject):
  
  def __init__(self, localSetting):
    super(ManagerLoginKey, self).__init__()
    self.localSettingKey = "%s/key" % localSetting # ~/.config/QGIS/QGIS2.conf
  
  def dialogLogin(self, dataDlg, dataMsgBox, setResult):

    def saveKeyDlg():
      reply = QMessageBox.question( dlg, dataMsgBox['title'], dataMsgBox['msg'], QMessageBox.Yes | QMessageBox.No) 
      if reply == QMessageBox.Yes:
        s = QSettings()
        s.setValue( self.localSettingKey, API_PlanetLabs.validKey )
    
    @pyqtSlot( int )
    def finished(result):
      isOk = result == QDialog.Accepted 
      if isOk:
        saveKeyDlg()
      setResult( isOk )

    dlg = DialogLoginKey( dataDlg['parent'] , dataDlg['windowTitle'], dataDlg['icon'] )
    dlg.finished.connect( finished )
    dlg.exec_()
    
  def getKeySetting(self):
    s = QSettings()
    return s.value( self.localSettingKey, None )
  
  def dialogRemoveKey(self, parent, title, message):
    QMessageBox.information ( parent, title, message, QMessageBox.Ok)
    s = QSettings()
    s.remove( self.localSettingKey )
