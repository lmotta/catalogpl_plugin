# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Legend Layer
Description          : Legend Layer for Planet Labs layer
Date                 : June, 2015
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

from PyQt4.QtCore import ( pyqtSlot, QSettings, QDir, QDate, QFile, QIODevice, QTimer )
from PyQt4.QtGui  import (
     QDialog, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSpinBox, QGroupBox, QRadioButton, QCheckBox,
     QDateEdit, QFileDialog, QMessageBox, QAction, QColor
)
from PyQt4.QtXml import QDomDocument

import qgis
from qgis.core import ( 
     QGis, QgsMapLayer, QgsRectangle, QgsGeometry,
     QgsCoordinateReferenceSystem, QgsCoordinateTransform
)
from qgis.gui import ( QgsRubberBand )

class DialogImageSettingPL(QDialog):

  def __init__(self, parent, icon=None, data=None):
    def initGui():
      def setData():
        buttonPath.setText( self.data["path"] )
        radioVisual.setChecked( self.data["isVisual"] )
        radioAnalytic.setChecked( not self.data["isVisual"] )
        d1 = self.data["date1"]
        d2 = self.data["date2"]
        date1.setDate( d1 )
        date2.setDate( d2 )
        date1.setMaximumDate( d2.addDays( -1 ) )
        date2.setMinimumDate( d1.addDays( +1 ) )
        spinDay.setValue( d1.daysTo( d2) )

      def connect():
        buttonOK.clicked.connect( self.onOK )
        buttonPath.clicked.connect( self.onPath )
        date1.dateChanged.connect( self.onDateChanged1 )
        date2.dateChanged.connect( self.onDateChanged2 )
        spinDay.valueChanged.connect( self.onValueChanged )

      windowTitle = "Setting download images Planet Labs"
      self.setWindowTitle( windowTitle )
      self.setWindowIcon( icon )

      grpImage = QGroupBox( "Images", self )
      radioVisual = QRadioButton( "Visual", grpImage )
      radioVisual.setObjectName( "rbVisual" )
      radioAnalytic = QRadioButton( "Analytic", grpImage )
      buttonPath = QPushButton( self.titleSelectDirectory, grpImage )
      buttonPath.setObjectName( "pbPath" )

      layoutRadioButtons = QHBoxLayout()
      for item in ( radioVisual, radioAnalytic ):
        layoutRadioButtons.addWidget( item )

      layoutImage = QVBoxLayout( grpImage )
      layoutImage.addLayout( layoutRadioButtons )
      layoutImage.addWidget( buttonPath )

      grpDateSearch = QGroupBox( "Dates for search", self )
      date1 = QDateEdit( grpDateSearch )
      date1.setObjectName( "deDate1" )
      date2 = QDateEdit( grpDateSearch )
      date2.setObjectName( "deDate2" )
      for item in [ date1, date2 ]:
        item.setCalendarPopup( True )
        format = item.displayFormat().replace( "yy", "yyyy")
        item.setDisplayFormat( format )
      spinDay = QSpinBox( grpDateSearch )
      spinDay.setObjectName( "sbDay" )
      spinDay.setSingleStep( 1 )
      spinDay.setSuffix( " Days")
      spinDay.setRange( 1, 1000*360 )
      
      layoutDate = QHBoxLayout( grpDateSearch )
      layoutDate.addWidget( QLabel("From", grpDateSearch ) )
      layoutDate.addWidget( date1 )
      layoutDate.addWidget( QLabel("To", grpDateSearch ) )
      layoutDate.addWidget( date2 )
      layoutDate.addWidget( spinDay )
      

      buttonOK = QPushButton( "OK", self )

      layout = QVBoxLayout( self )
      layout.addWidget( grpImage )
      layout.addWidget( grpDateSearch )
      layout.addWidget( buttonOK )

      self.resize( 5 * len( windowTitle ) + 200 , 30 )

      if not self.data is None:
        setData()
      else:
        radioVisual.setChecked( True )
        radioAnalytic.setChecked( False )
        d2 = QDate.currentDate()
        d1 = d2.addMonths( -1 )
        date1.setDate( d1 )
        date2.setDate( d2 )
        date1.setMaximumDate( d2.addDays( -1 ) )
        date2.setMinimumDate( d1.addDays( +1 ) )
        spinDay.setValue( d1.daysTo( d2) )

      connect()

    super( DialogImageSettingPL, self ).__init__( parent )
    self.data = data
    self.titleSelectDirectory = "Select download directory"
    initGui()

  def getData(self):
    return self.data

  def _saveDataSetting(self):
    localSetting = "catalogpl_plugin" # ~/.config/QGIS/QGIS2.conf
    values = { 
          'path': "{0}/path".format( localSetting ),
          'isVisual': "{0}/isVisual".format( localSetting )
    }
    s = QSettings()
    for key in values.keys():
      s.setValue( values[ key ], self.data[ key ] )

  def _setSpinDay(self,  date1, date2 ):
    spinDay = self.findChild( QSpinBox, "sbDay" )
    spinDay.valueChanged.disconnect( self.onValueChanged )
    spinDay.setValue( date1.daysTo( date2) )
    spinDay.valueChanged.connect( self.onValueChanged )

  @staticmethod
  def getDownloadSettings():
    localSetting = "catalogpl_plugin" # ~/.config/QGIS/QGIS2.conf
    values = { 
          'path': "%s/path" % localSetting,
          'isVisual': "%s/isVisual" % localSetting
    }
    data = None
    s = QSettings()
    path = s.value( values['path'], None )
    if not path is None:
      isVisual = s.value( values['isVisual'], None )
      isVisual = True if isVisual == "true" else False
      if QDir( path ).exists():
        data = { 'path': path, 'isVisual': isVisual, 'isOk': True }
      else:
        data = { 'path': path, 'isOk': False }
        s.remove( values['path'] )
    else:
      data = { 'path': "Empty", 'isOk': False }
      
    return data

  @pyqtSlot( bool )
  def onOK(self, checked):
    pb = self.findChild( QPushButton, "pbPath" )
    path = pb.text()
    if path == self.titleSelectDirectory:
      msg = "Directory '{0}'not found".format( self.titleSelectDirectory )
      QMessageBox.information( self, "Missing directory for download", msg )
      return

    rb = self.findChild( QRadioButton, "rbVisual" )
    date1 = self.findChild( QDateEdit, "deDate1" )
    date2 = self.findChild( QDateEdit, "deDate2" )
    self.data = {
        "path": path,
        "isVisual": rb.isChecked(),
        "date1": date1.date(),
        "date2": date2.date()
    }
    self._saveDataSetting()
    self.data[ 'isOk' ] = True
    self.accept()

  @pyqtSlot( bool )
  def onPath(self, checked):
    pb = self.findChild( QPushButton, "pbPath" )
    path = pb.text()
    if path == self.titleSelectDirectory:
      path = None
    sdir = QFileDialog.getExistingDirectory(self, self.titleSelectDirectory, path )
    if len(sdir) > 0:
      pb.setText( sdir )

  @pyqtSlot( 'QDate' )
  def onDateChanged1(self, date ):
    date2 = self.findChild( QDateEdit, "deDate2" )
    date2.setMinimumDate( date.addDays( +1 ) )
    self._setSpinDay( date, date2.date() )

  @pyqtSlot( 'QDate' )
  def onDateChanged2(self, date ):
    date1 = self.findChild( QDateEdit, "deDate1" )
    date1.setMaximumDate( date.addDays( -1 ) )
    self._setSpinDay( date1.date(), date )

  @pyqtSlot( int )
  def onValueChanged(self, days ):
    date1 = self.findChild( QDateEdit, "deDate1" )
    date2 = self.findChild( QDateEdit, "deDate2" )
    newDate = date2.date().addDays( -1 * days )
    date1.dateChanged.disconnect( self.onDateChanged1 )
    date1.setDate( newDate )
    date2.setMinimumDate( newDate.addDays( +1 ) )
    date1.dateChanged.connect( self.onDateChanged1 )

class LegendCatalogLayer():

  def __init__(self, slots):
    self.slots = slots
    self.legendInterface = qgis.utils.iface.legendInterface()
    self.legendMenuIDs = {
      'clear_key': 'idKey',
      'clipboard_key': 'idClipboardKey',
      'setting_images': 'idSetting',
      'calculate_status_assets': 'idCalculateStatusAssets',
      'create_tms': 'idCreateTMS',
      'download_images': 'idDownloadImages',
      'download_thumbnails': 'idDownloadThumbnails'
    }
    self.legendLayer = self.layer = None

  def clean(self):
    for item in self.legendLayer:
      self.legendInterface.removeLegendLayerAction( item['action'] )

  def setLayer(self, layer):
    def addActionLegendLayer():
      self.legendLayer = [
        {
          'menu': u"Clear key",
          'id': self.legendMenuIDs['clear_key'],
          'slot': self.slots['clear_key'],
          'action': None
        },
        {
          'menu': u"Copy key to Clipboard",
          'id': self.legendMenuIDs['clipboard_key'],
          'slot': self.slots['clipboard_key'],
          'action': None
        },
        {
          'id': 'idSeparator',
          'action': None
        },
        {
          'menu': u"Search settings",
          'id': self.legendMenuIDs['setting_images'],
          'slot': self.slots['setting_images'],
          'action': None
        },
        {
          'id': 'idSeparator',
          'action': None
        },
        {
          'menu': u"Calculate Status Assets",
          'id': self.legendMenuIDs['calculate_status_assets'],
          'slot': self.slots['calculate_status_assets'],
          'action': None
        },
        {
          'id': 'idSeparator',
          'action': None
        },
        {
          'menu': u"Create TMS",
          'id': self.legendMenuIDs['create_tms'],
          'slot': self.slots['create_tms'],
          'action': None
        },
        {
          'menu': u"Download images",
          'id': self.legendMenuIDs['download_images'],
          'slot': self.slots['download_images'],
          'action': None
        },
        {
          'menu': u"Download thumbnails",
          'id': self.legendMenuIDs['download_thumbnails'],
          'slot': self.slots['download_thumbnails'],
          'action': None
        }
      ]

      prefixTotal = "({0} total)".format( self.layer.featureCount() )
      prefixIds = ( self.legendMenuIDs['create_tms'], self.legendMenuIDs['download_thumbnails'] )
      for item in self.legendLayer:
        if item['id'] == 'idSeparator':
          item['action'] = QAction(None)
          item['action'].setSeparator(True)
        else:
          item['action'] = QAction( item['menu'], None )
          item['action'].triggered.connect( item['slot'] )
          if item['id'] in prefixIds:
            lblAction = "{0} {1}".format( item['menu'], prefixTotal )
            item['action'].setText( lblAction )
        arg = ( item['action'], labelMenu, item['id'], QgsMapLayer.VectorLayer, False )
        self.legendInterface.addLegendLayerAction( *arg )
        self.legendInterface.addLegendLayerActionForLayer( item['action'], self.layer )

    self.layer = layer
    self.layer.selectionChanged.connect( self.selectionChanged )
    labelMenu = u"Planet Labs"
    addActionLegendLayer()

  def enabledProcessing(self, enabled=True):
    notIds = (
      'idSeparator',
      self.legendMenuIDs['clear_key'],
      self.legendMenuIDs['clipboard_key']
    )
    for item in self.legendLayer:
      if item['id'] in notIds:
        continue
      item['action'].setEnabled( enabled )

  def enabledClearKey (self, enabled=True):
    for item in self.legendLayer:
      if item['id'] == self.legendMenuIDs['clear_key']:
        item['action'].setEnabled( enabled )
        break

  @pyqtSlot()
  def selectionChanged(self):
    def getPrefixTotal():
      total = self.layer.selectedFeatureCount()
      prefixTotal = "({0} selected)".format( total )
      if total == 0:
        total = self.layer.featureCount()
        prefixTotal = "({0} total)".format( total )
  
      return prefixTotal
    
    prefixTotal = getPrefixTotal()
    prefixIds = ( self.legendMenuIDs['create_tms'], self.legendMenuIDs['download_thumbnails'] )
    totalIds = len( prefixIds )
    countIds = 0
    for item in self.legendLayer:
      if item['id'] in prefixIds:
        lblAction = "{0} {1}".format( item['menu'], prefixTotal )
        item['action'].setText( lblAction )
        countIds += 1
        if countIds == totalIds:
          break
