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

import os, shutil

from PyQt4 import QtCore, QtGui, QtXml 
import qgis
from qgis import core as QgsCore, gui as QgsGui, utils as QgsUtils

class DialogImageSettingPL(QtGui.QDialog):

  localSetting = "catalogpl_plugin" # ~/.config/QGIS/QGIS2.conf

  def __init__(self, parent, icon=None, data=None):
    def initGui():
      def setData():
        def getSizeCacheTMS():
          dirs = self._getDirsCacheTMS()
          if len( dirs ) == 0:
            return 0

          total_size = 0
          for path in dirs: 
            for dirpath, dirnames, filenames in os.walk(path):
              total_size += os.path.getsize(dirpath) / 1024.0 # KB
              for f in filenames:
                fp = os.path.join( dirpath, f )
                total_size += os.path.getsize(fp) / 1024.0 # KB
          return total_size/1024.0   # in MB

        w = self.findChild( QtGui.QRadioButton, self.data['current_asset'] )
        w.setChecked(True)
        checkUdm.setChecked( self.data['udm'] )
        buttonPath.setText( self.data['path'] )
        total = getSizeCacheTMS()
        if total > 0:
          buttonClearCache.setText( self.titleClearCache.format( total ) )
          buttonClearCache.setEnabled(True)
        d1 = self.data['date1']
        d2 = self.data['date2']
        date1.setDate( d1 )
        date2.setDate( d2 )
        date1.setMaximumDate( d2.addDays( -1 ) )
        date2.setMinimumDate( d1.addDays( +1 ) )
        spinDay.setValue( d1.daysTo( d2) )

      def connect():
        buttonOK.clicked.connect( self.onOK )
        buttonPath.clicked.connect( self.onPath )
        buttonClearCache.clicked.connect( self.onClearCache )
        date1.dateChanged.connect( self.onDateChanged1 )
        date2.dateChanged.connect( self.onDateChanged2 )
        spinDay.valueChanged.connect( self.onValueChanged )

      def createCheckBox(text, objName, group, layout=None):
        widget = QtGui.QCheckBox( text, group )
        widget.setObjectName( objName )
        if not layout is None:
          layout.addWidget( widget )
        return widget

      def createDateEdit(labelName, objName, group, layout):
        label = QtGui.QLabel( labelName, group )
        layout.addWidget( label )
        widget = QtGui.QDateEdit( group )
        widget.setObjectName( objName )
        widget.setCalendarPopup( True )
        format = widget.displayFormat().replace('yy', 'yyyy')
        widget.setDisplayFormat( format )
        layout.addWidget( widget )
        return widget

      def createRadioButton(text, objName, group, layout=None):
        widget = QtGui.QRadioButton( text, group )
        widget.setObjectName( objName )
        if not layout is None:
          layout.addWidget( widget )

      windowTitle = "Setting Planet Labs"
      self.setWindowTitle( windowTitle )
      self.setWindowIcon( icon )

      grpImage = QtGui.QGroupBox('Images', self )
      # https://www.planet.com/docs/reference/data-api/items-assets/#item-type
      lytAssets = QtGui.QHBoxLayout()
      for name in self.nameAssets:
        createRadioButton( name.capitalize(), name, grpImage, lytAssets )

      checkUdm = createCheckBox( 'Save UDM(Unusable Data Mask)', 'udm', grpImage )

      buttonPath = QtGui.QPushButton( self.titleSelectDirectory, grpImage )
      buttonPath.setObjectName('path')

      buttonClearCache = QtGui.QPushButton( self.titleClearCache.format(0), grpImage )
      buttonClearCache.setObjectName('clear_cache')
      buttonClearCache.setEnabled(False)

      lytImage = QtGui.QVBoxLayout( grpImage )
      lytImage.addLayout( lytAssets )
      lytImage.addWidget( checkUdm )
      lytImage.addWidget( buttonPath )
      lytImage.addWidget( buttonClearCache )

      grpDateSearch = QtGui.QGroupBox('Dates for search', self )
      lytDate = QtGui.QHBoxLayout( grpDateSearch )
      date1 = createDateEdit('From', 'deDate1', grpDateSearch, lytDate )
      date2 = createDateEdit('To', 'deDate2', grpDateSearch, lytDate )
      spinDay = QtGui.QSpinBox( grpDateSearch )
      spinDay.setObjectName('sbDay')
      spinDay.setSingleStep( 1 )
      spinDay.setSuffix(' Days')
      spinDay.setRange( 1, 1000*360 )
      lytDate.addWidget( spinDay )

      buttonOK = QtGui.QPushButton('OK', self )

      layout = QtGui.QVBoxLayout( self )
      layout.addWidget( grpImage )
      layout.addWidget( grpDateSearch )
      layout.addWidget( buttonOK )

      self.resize( 5 * len( windowTitle ) + 200 , 30 )

      if not self.data is None:
        setData()
      else:
        w = self.findChild( QtGui.QRadioButton, 'planet' )
        w.setChecked( True )
        d2 = QtCore.QDate.currentDate()
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
    self.titleClearCache = "Clear TMS cache (total {:0.2f}MB)"
    self.nameAssets = ('planet', 'rapideye', 'landsat8', 'sentinel2')
    initGui()

  def getData(self):
    return self.data

  def _saveDataSetting(self):
    # Next step add all informations
    #See __init__.initGui
    #keys = ['path', 'planet', 'rapideye', 'landsat8', 'sentinel2', 'udm', 'date1', 'date2']

    keys = ['path' ]
    values = {}
    for k in keys:
      values[ k ] = "{0}/{1}".format( DialogImageSettingPL.localSetting, k )
    s = QtCore.QSettings()
    for k in values.keys():
      s.setValue( values[ k ], self.data[ k ] )

  def _setSpinDay(self,  date1, date2 ):
    spinDay = self.findChild( QtGui.QSpinBox, "sbDay" )
    spinDay.valueChanged.disconnect( self.onValueChanged )
    spinDay.setValue( date1.daysTo( date2) )
    spinDay.valueChanged.connect( self.onValueChanged )

  def _getDirsCacheTMS(self):
    w = self.findChild( QtGui.QPushButton, 'path' )
    tmsDir = os.path.join( w.text(), 'tms' )
    if not os.path.isdir( tmsDir ):
      return []
    dirs = [os.path.join(tmsDir, d) for d in os.listdir(tmsDir) if os.path.isdir(os.path.join(tmsDir, d))]
    return dirs

  @staticmethod
  def getSettings():
    # Next step add all informations
    #See __init__.initGui
    #keys = ['path', 'planet', 'rapideye', 'landsat8', 'sentinel2', 'date1', 'date2']

    keys = ['path']
    values = {}
    for k in keys:
      values[ k ] = "{0}/{1}".format( DialogImageSettingPL.localSetting, k )
    data = None
    s = QtCore.QSettings()
    path = s.value( values['path'], None )
    if not path is None:
      # Next step add all informations
      # planet = s.value( values['planet'], None )
      # planet = True if planet == "true" else False
      # rapideye = s.value( values['rapideye'], None )
      # rapideye = True if rapideye == "true" else False
      # ...
      # if QtCore.QDir( path ).exists():
      #   data = { 'isOk': True, 'path': path, 'planet': planet, 'rapideye': rapideye,... }

      if QtCore.QDir( path ).exists():
        data = { 'isOk': True, 'path': path }
      else:
        data = { 'isOk': False, 'has_path': True, 'path': path }
        s.remove( values['path'] )
    else:
      data = { 'isOk': False, 'has_path': False }

    return data

  @QtCore.pyqtSlot()
  def onOK(self):
    def getCurrentNameAsset():
      for name in self.nameAssets:
        w = self.findChild( QtGui.QRadioButton, name )
        if w.isChecked():
          return name

    pb = self.findChild( QtGui.QPushButton, 'path' )
    path = pb.text()
    if path == self.titleSelectDirectory:
      msg = "Directory '{0}'not found".format( self.titleSelectDirectory )
      QtGui.QMessageBox.information( self, "Missing directory for download", msg )
      return
    udm = self.findChild( QtGui.QCheckBox, 'udm' )
    date1 = self.findChild( QtGui.QDateEdit, "deDate1" )
    date2 = self.findChild( QtGui.QDateEdit, "deDate2" )
    self.data = {
        'path': path,
        'current_asset': getCurrentNameAsset(),
        'udm': udm.isChecked(),
        'date1': date1.date(),
        'date2': date2.date()
    }
    self._saveDataSetting()
    self.data['isOk'] = True
    self.accept()

  @QtCore.pyqtSlot()
  def onPath(self):
    w = self.findChild( QtGui.QPushButton, 'path' )
    path = w.text()
    if path == self.titleSelectDirectory:
      path = None
    sdir = QtGui.QFileDialog.getExistingDirectory(self, self.titleSelectDirectory, path )
    if len(sdir) > 0:
      w.setText( sdir )

  @QtCore.pyqtSlot()
  def onClearCache(self):
    dirs = self._getDirsCacheTMS()
    if not len( dirs ) == 0:
      for d in dirs:
        shutil.rmtree(d)
    title = self.titleClearCache.format(0)
    w = self.findChild( QtGui.QPushButton, 'clear_cache' )
    w.setText( title )
    w.setEnabled(False)

  @QtCore.pyqtSlot(QtCore.QDate)
  def onDateChanged1(self, date ):
    date2 = self.findChild( QtGui.QDateEdit, "deDate2" )
    date2.setMinimumDate( date.addDays( +1 ) )
    self._setSpinDay( date, date2.date() )

  @QtCore.pyqtSlot(QtCore.QDate)
  def onDateChanged2(self, date ):
    date1 = self.findChild( QtGui.QDateEdit, "deDate1" )
    date1.setMaximumDate( date.addDays( -1 ) )
    self._setSpinDay( date1.date(), date )

  @QtCore.pyqtSlot( int )
  def onValueChanged(self, days ):
    date1 = self.findChild( QtGui.QDateEdit, "deDate1" )
    date2 = self.findChild( QtGui.QDateEdit, "deDate2" )
    newDate = date2.date().addDays( -1 * days )
    date1.dateChanged.disconnect( self.onDateChanged1 )
    date1.setDate( newDate )
    date2.setMinimumDate( newDate.addDays( +1 ) )
    date1.dateChanged.connect( self.onDateChanged1 )

class LegendCatalogLayer():
  def __init__(self, labelMenu, slots, getTotalAssets):
    self.labelMenu, self.slots, self.getTotalAssets = labelMenu, slots, getTotalAssets
    self.legendInterface = QgsUtils.iface.legendInterface()
    self.legendMenuIDs = {
      'clear_key': 'idKey',
      'clipboard_key': 'idClipboardKey',
      'setting_images': 'idSetting',
      'calculate_status_assets': 'idCalculateStatusAssets',
      'activate_assets': 'idActivateAssets',
      'create_tms': 'idCreateTMS',
      'download_images': 'idDownloadImages',
      'download_thumbnails': 'idDownloadThumbnails'
    }
    self.legendLayer = self.layer = None
    self.statusEnableAssetsImage = {
      'activate_assets': False,
      'download_images': False
    }

  def _getPrefixs(self, totalAssets):
    totalFeats = self.layer.selectedFeatureCount()
    isSelect = totalFeats > 0
    prefix = "selected" if isSelect else "total"
    if not isSelect:
      totalFeats = self.layer.featureCount()
    
    prefixTotal  = "{0} - {1}".format( totalFeats, prefix ) 
    arg = ( totalAssets['analytic']['images'], totalAssets['udm']['images'], prefix )
    prefixImages = "{0} analytic - {1} udm - {2}".format( *arg )
    arg = ( totalAssets['analytic']['activate'], totalAssets['udm']['activate'], prefix )
    prefixAssets = "{0} analytic - {1} udm - {2}".format( *arg )
  
    return {
      'total': prefixTotal,
      'images': prefixImages,
      'assets': prefixAssets
    }

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
          'menu': u"Settings...",
          'id': self.legendMenuIDs['setting_images'],
          'slot': self.slots['setting_images'],
          'action': None
        },
        {
          'id': 'idSeparator',
          'action': None
        },
        {
          'menu': u"Calculate status assets",
          'id': self.legendMenuIDs['calculate_status_assets'],
          'slot': self.slots['calculate_status_assets'],
          'action': None
        },
        {
          'menu': u"Activate assets",
          'id': self.legendMenuIDs['activate_assets'],
          'slot': self.slots['activate_assets'],
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

      prefixs = {
        'total':  "{0} - total".format( self.layer.featureCount() ),
        'images': "0 analytic - 0 udm - total",
        'assets': "0 analytic - 0 udm - total"
      }
      idsTotal = (
        self.legendMenuIDs['calculate_status_assets'],
        self.legendMenuIDs['create_tms'],
        self.legendMenuIDs['download_thumbnails']
      )
      for item in self.legendLayer:
        if item['id'] == 'idSeparator':
          item['action'] = QtGui.QAction(None)
          item['action'].setSeparator(True)
        else:
          item['action'] = QtGui.QAction( item['menu'], self.legendInterface )
          item['action'].triggered.connect( item['slot'] )
          if item['id'] in idsTotal:
            lblAction = "{0}({1})".format( item['menu'], prefixs['total'] )
            item['action'].setText( lblAction )
          if item['id'] == self.legendMenuIDs['download_images']:
            lblAction = "{0}({1})".format( item['menu'], prefixs['images'] )
            item['action'].setText( lblAction )
            item['action'].setEnabled( False )
          if item['id'] == self.legendMenuIDs['activate_assets']:
            lblAction = "{0}({1})".format( item['menu'], prefixs['assets'] )
            item['action'].setText( lblAction )
            item['action'].setEnabled( False )
        arg = ( item['action'], self.labelMenu, item['id'], QgsCore.QgsMapLayer.VectorLayer, False )
        self.legendInterface.addLegendLayerAction( *arg )
        self.legendInterface.addLegendLayerActionForLayer( item['action'], self.layer )

    self.layer = layer
    self.layer.selectionChanged.connect( self.selectionChanged )
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

    if  enabled:
      ids = ( self.legendMenuIDs['download_images'], self.legendMenuIDs['activate_assets'] )
      c_ids, total_ids = 0, len( ids )
      for item in self.legendLayer:
        if item['id'] == self.legendMenuIDs['download_images']:
          item['action'].setEnabled( self.statusEnableAssetsImage['download_images'] )
          c_ids += 1
        if item['id'] == self.legendMenuIDs['activate_assets']:
          item['action'].setEnabled( self.statusEnableAssetsImage['activate_assets'] )
          c_ids += 1
        if c_ids == total_ids:
          break

  def setAssetImages(self, totalAssets):
    enable = not ( totalAssets['analytic']['images'] + totalAssets['udm']['images'] == 0 )
    self.statusEnableAssetsImage['download_images'] = enable
    enable = not ( totalAssets['analytic']['activate'] + totalAssets['udm']['activate'] == 0 )
    self.statusEnableAssetsImage['activate_assets'] = enable
    prefixs = self._getPrefixs( totalAssets )
    ids = ( self.legendMenuIDs['download_images'], self.legendMenuIDs['activate_assets'] )
    c_ids, total_ids = 0, len( ids )
    for item in self.legendLayer:
      if item['id'] == self.legendMenuIDs['download_images']:
        lblAction = "{0} ({1})".format( item['menu'], prefixs['images'] )
        item['action'].setText( lblAction )
        item['action'].setEnabled( self.statusEnableAssetsImage['download_images'] )
        c_ids += 1
      if item['id'] == self.legendMenuIDs['activate_assets']:
        lblAction = "{0} ({1})".format( item['menu'], prefixs['assets'] )
        item['action'].setText( lblAction )
        item['action'].setEnabled( self.statusEnableAssetsImage['activate_assets'] )
        c_ids += 1
      if c_ids == total_ids:
        break

  def enabledClearKey (self, enabled=True):
    for item in self.legendLayer:
      if item['id'] == self.legendMenuIDs['clear_key']:
        item['action'].setEnabled( enabled )
        break

  @QtCore.pyqtSlot()
  def selectionChanged(self):
    totalAssets = self.getTotalAssets()
    enable = not ( totalAssets['analytic']['images'] + totalAssets['udm']['images'] == 0 )
    self.statusEnableAssetsImage['download_images'] = enable
    enable = not ( totalAssets['analytic']['activate'] + totalAssets['udm']['activate'] == 0 )
    self.statusEnableAssetsImage['activate_assets'] = enable
    prefixs = self._getPrefixs( totalAssets )
    idsTotal = (
      self.legendMenuIDs['calculate_status_assets'],
      self.legendMenuIDs['create_tms'],
      self.legendMenuIDs['download_thumbnails']
    )
    for item in self.legendLayer:
      if item['id'] in idsTotal:
        lblAction = "{0} ({1})".format( item['menu'], prefixs['total'] )
        item['action'].setText( lblAction )
      if item['id'] == self.legendMenuIDs['download_images']:
        lblAction = "{0} ({1})".format( item['menu'], prefixs['images'] )
        item['action'].setText( lblAction )
        item['action'].setEnabled( self.statusEnableAssetsImage['download_images'] )
      if item['id'] == self.legendMenuIDs['activate_assets']:
        lblAction = "{0} ({1})".format( item['menu'], prefixs['assets'] )
        item['action'].setText( lblAction )
        item['action'].setEnabled( self.statusEnableAssetsImage['activate_assets'] )

