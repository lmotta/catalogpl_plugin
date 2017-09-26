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

from PyQt4.QtGui import ( QAction, QIcon )
from PyQt4.QtCore import ( pyqtSlot, QEventLoop )

from qgis.gui import QgsMessageBar

from catalogpl import CatalogPL
from apiqtpl import API_PlanetLabs

def classFactory(iface):
  return CatalogPLPlugin( iface )

class CatalogPLPlugin:

  icon = QIcon( os.path.join( os.path.dirname(__file__), 'catalogpl.png' ) )
  pluginName = "Catalog Planet Labs"

  def __init__(self, iface):
    
    self.iface = iface
    self.name = u"&Catalog Planet Labs"
    self.msgBar = iface.messageBar()
    self.action = None
    self.ctl = CatalogPL( self.iface, CatalogPLPlugin.icon )

    CatalogPL.copyExpression()
    
  def initGui(self):
    msgtrans = "Catalog Planet Labs"
    self.action = QAction( CatalogPLPlugin.icon, msgtrans, self.iface.mainWindow() )
    self.action.setObjectName("CatalogPL")
    self.action.setWhatsThis( msgtrans )
    self.action.setStatusTip( msgtrans )
    self.action.triggered.connect( self.run )
    self.ctl.enableRun.connect( self.action.setEnabled )

    self.iface.addToolBarIcon( self.action )
    self.iface.addPluginToRasterMenu( self.name, self.action )

  def unload(self):
    self.iface.removePluginMenu( self.name, self.action )
    self.iface.removeToolBarIcon( self.action )
    del self.action
    del self.ctl
  
  @pyqtSlot()
  def run(self):

    if self.iface.mapCanvas().layerCount() == 0:
      msg = "Need layer(s) in map"
      self.iface.messageBar().pushMessage( CatalogPLPlugin.pluginName, msg, QgsMessageBar.WARNING, 2 )
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
