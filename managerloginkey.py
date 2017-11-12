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

from PyQt4 import QtCore, QtGui

from apiqtpl import API_PlanetLabs 

class DialogLoginKey(QtGui.QDialog):

  def __init__(self, parent, windowTitle, icon=None):
    def initGui():
      def connect():
        buttonLogin.clicked.connect( self.onLogin )
        self.textKey.textEdited.connect( self.onTextEdited )
      #
      self.setWindowTitle( windowTitle )
      if not icon is None:
        self.setWindowIcon( icon )
      labelKey = QtGui.QLabel( "Key: ", self )
      self.labelError = QtGui.QLabel( self )
      self.labelError.hide()
      self.textKey = QtGui.QLineEdit( self )
      self.textKey.setEchoMode( QtGui.QLineEdit.Password )
      buttonLogin = QtGui.QPushButton( "Login", self )
      connect()
      layout = QtGui.QVBoxLayout( self )
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

  @QtCore.pyqtSlot( bool )
  def onLogin(self, checked):
    def setFinishedPL(response):
      self.responsePL = response
      loop.quit()
    
    def setKeyResponse():
      if self.responsePL['isOk']:
        self.accept()
      else:
        self.labelError.setTextFormat( QtCore.Qt.RichText )
        msg = "<font color=\"red\"><b><i>Invalid key! %s</i></b></font>" % self.responsePL['message'] 
        self.labelError.setText( msg )
        self.labelError.show()

    key = self.textKey.text().encode('ascii', 'ignore')
    self.responsePL = None
    loop = QtCore.QEventLoop()
    self.apiPL.setKey( key, setFinishedPL )
    loop.exec_()
    setKeyResponse()

  @QtCore.pyqtSlot( str )
  def onTextEdited(self, text ):
    if self.labelError.isHidden():
      return
    self.labelError.hide()


class ManagerLoginKey(QtCore.QObject):
  
  def __init__(self, localSetting):
    super(ManagerLoginKey, self).__init__()
    self.localSettingKey = "%s/key" % localSetting # ~/.config/QGIS/QGIS2.conf
  
  def dialogLogin(self, dataDlg, dataMsgBox, setResult):

    def saveKeyDlg():
      reply = QtGui.QMessageBox.question( dlg, dataMsgBox['title'], dataMsgBox['msg'], QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) 
      if reply == QtGui.QMessageBox.Yes:
        s = QtCore.QSettings()
        s.setValue( self.localSettingKey, API_PlanetLabs.validKey )
    
    @QtCore.pyqtSlot( int )
    def finished(result):
      isOk = result == QtGui.QDialog.Accepted 
      if isOk:
        saveKeyDlg()
      setResult( isOk )

    dlg = DialogLoginKey( dataDlg['parent'] , dataDlg['windowTitle'], dataDlg['icon'] )
    dlg.finished.connect( finished )
    dlg.exec_()
    
  def getKeySetting(self):
    s = QtCore.QSettings()
    return s.value( self.localSettingKey, None )
  
  def removeKey(self):
    s = QtCore.QSettings()
    s.remove( self.localSettingKey )
