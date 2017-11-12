# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Catalog Planet Labs
Description          : Create catalog from Planet Labs
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

import os

from PyQt4 import QtCore, QtGui
from qgis import core as QgsCore, gui as QgsGui

from catalogpl import CatalogPL
from apiqtpl import API_PlanetLabs

def classFactory(iface):
  return CatalogPLPlugin( iface )

class CatalogPLPlugin:

  icon = QtGui.QIcon( os.path.join( os.path.dirname(__file__), 'catalogpl.svg' ) )
  pluginName = "Catalog Planet Labs"

  def __init__(self, iface):
    
    self.iface = iface
    self.name = u"&Catalog Planet Labs"
    self.msgBar = iface.messageBar()
    self.action = None
    self.ctl = CatalogPL( CatalogPLPlugin.icon )

    CatalogPL.copyExpression()
    
  def initGui(self):
    dataActions = [
      {
        'isSepatator': False,
        'name': 'Catalog Planet Labs',
        'icon': QtGui.QIcon( CatalogPLPlugin.icon ),
        'method': self.run
      },
      { 'isSepatator': True },
      {
        'isSepatator': False,
        'name': 'Setting...',
        'icon': QgsCore.QgsApplication.getThemeIcon('/mActionOptions.svg'),
        'method': self.config
      },
      { 'isSepatator': True },             
      {
        'isSepatator': False,
        'name': 'Clear key',
        'icon': QgsCore.QgsApplication.getThemeIcon('/mActionOptions.svg'),
        'method': self.clearKey
      },
      {
        'isSepatator': False,
        'name': 'Copy key to Clipboard',
        'icon': QgsCore.QgsApplication.getThemeIcon('/mActionOptions.svg'),
        'method': self.clipboardKey
      }
    ]
    
    mw = self.iface.mainWindow()
    popupMenu = QtGui.QMenu( mw )
    for d in dataActions:
      if d['isSepatator']:
        a = QtGui.QAction( mw )
        a.setSeparator(True)
      else:
        a = QtGui.QAction( d['icon'], d['name'], mw )
        a.triggered.connect( d['method'] )
      self.iface.addPluginToRasterMenu( self.name, a )
      popupMenu.addAction(  a )
    defaultAction = popupMenu.actions()[0]
    self.toolButton = QtGui.QToolButton()
    self.toolButton.setPopupMode( QtGui.QToolButton.MenuButtonPopup )
    self.toolButton.setMenu( popupMenu )
    self.toolButton.setDefaultAction( defaultAction )
    
    self.actionPopupMenu = self.iface.addToolBarWidget( self.toolButton )
    self.ctl.enableRun.connect( self.actionPopupMenu.setEnabled )

  def unload(self):
    self.iface.removePluginMenu( self.name, self.action )
    self.iface.removeToolBarIcon( self.action )
    del self.action
    del self.ctl
  
  @QtCore.pyqtSlot()
  def run(self):
    if self.iface.mapCanvas().layerCount() == 0:
      msg = "Need layer(s) in map"
      self.iface.messageBar().pushMessage( CatalogPLPlugin.pluginName, msg, QgsGui.QgsMessageBar.WARNING, 2 )
      return

    if not self.ctl.isHostLive:
      self.ctl.hostLive()
      if not self.ctl.isHostLive:
        return

    if not self.ctl.hasRegisterKey:
      self.ctl.registerKey()
      if not self.ctl.hasRegisterKey:
        return

    self.ctl.createLayerScenes()

  @QtCore.pyqtSlot()
  def config(self):
    self.ctl.settingImages()

  @QtCore.pyqtSlot()
  def clearKey(self):
    self.ctl.clearKey()

  @QtCore.pyqtSlot()
  def clipboardKey(self):
    self.ctl.clipboardKey()
