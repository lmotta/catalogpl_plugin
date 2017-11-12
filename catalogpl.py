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

import os, json

from PyQt4 import QtCore, QtGui
from qgis import core as QgsCore, gui as QgsGui, utils as QgsUtils

from apiqtpl import API_PlanetLabs
from legendlayerpl import ( DialogImageSettingPL, LegendCatalogLayer )
from legendlayer import LegendRasterGeom
from managerloginkey import ManagerLoginKey
from messagebarcancel import MessageBarCancel, MessageBarCancelProgress 
from workertms import WorkerCreateTMS_GDAL_WMS


class CatalogPL(QtCore.QObject):

  pluginName = u'Catalog Planet Labs'
  styleFile = 'pl_scenes.qml'
  expressionFile = 'pl_expressions.py'
  expressionDir = 'expressions'

  enableRun = QtCore.pyqtSignal( bool )
  
  def __init__(self, icon):
    def setLegendCatalogLayer():
      # keys = LegendCatalogLayer.legendMenuIDs 
      slots = { 
         'clear_key': self.clearKey,
         'clipboard_key': self.clipboardKey,
         'setting_images': self.settingImages,
         'calculate_status_assets': self.calculateAssetStatus,
         'activate_assets': self.activateAssets,
         'create_tms': self.CreateTMS_GDAL_WMS,
         'download_images': self.downloadImages,
         'download_thumbnails': self.downloadThumbnails
      }
      arg = ( CatalogPL.pluginName, slots, self.getTotalAssets )
      self.legendCatalogLayer = LegendCatalogLayer( *arg )

    def setSearchSettings():
      self.settings = DialogImageSettingPL.getSettings()
      
      # Next step add all informations (DialogImageSettingPL.getSettings)
      self.settings['current_asset'] = 'planet'
      self.settings['udm'] = False
      date2 = QtCore.QDate.currentDate()
      date1 = date2.addMonths( -1 )
      self.settings['date1'] = date1 
      self.settings['date2'] = date2

    super(CatalogPL, self).__init__()
    self.canvas = QgsUtils.iface.mapCanvas()
    self.msgBar = QgsUtils.iface.messageBar()
    self.logMessage = QgsCore.QgsMessageLog.instance().logMessage
    self.icon = icon
    self.mainWindow = QgsUtils.iface.mainWindow()

    self.apiPL = API_PlanetLabs()
    self.mngLogin = ManagerLoginKey('catalogpl_plugin')
    self.legendRasterGeom = LegendRasterGeom( CatalogPL.pluginName )
    self.thread = self.worker = None # initThread
    self.mbcancel = None # Need for worker it is be class attribute
    self.isHostLive = False
    self.hasRegisterKey = False

    self.layer = self.layerTree = None
    self.hasCriticalMessage = None
    self.url_scenes = self.scenes = self.total_features_scenes = None 
    self.pixmap = self.messagePL = self.isOkPL = None
    self.legendCatalogLayer = self.settings = None
    self.imageDownload = self.totalReady = None
    self.currentItem = None
    self.catalog = { 'ltg': None, 'satellite': None, 'typeImage': None }

    setLegendCatalogLayer()
    setSearchSettings()
    self._connect()
    self._initThread()

  def __del__(self):
    self._connect( False )
    self._finishThread()
    del self.legendRasterGeom

  def _initThread(self):
    self.thread = QtCore.QThread( self )
    self.thread.setObjectName( "QGIS_Plugin_Catalog_PlanetLabs" )
    self.worker = WorkerCreateTMS_GDAL_WMS( self.logMessage, self.legendRasterGeom )
    self.worker.moveToThread( self.thread )
    self.thread.started.connect( self.worker.run )

  def _finishThread(self):
    self.thread.started.disconnect( self.worker.run )
    self.worker.deleteLater()
    self.thread.wait()
    self.thread.deleteLater()
    del self.worker
    self.thread = self.worker = None

  def _connect(self, isConnect = True):
    s = { 'signal': QgsCore.QgsMapLayerRegistry.instance().layerWillBeRemoved, 'slot': self.layerWillBeRemoved }
    if isConnect:
      s['signal'].connect( s['slot'] )
    else:
      s['signal'].disconnect( s['slot'] )

  def _startProcess(self, funcKill, hasProgressFile=False):
    def getFeatureIteratorTotal():
      hasSelected = True
      iter = self.layer.selectedFeaturesIterator()
      total = self.layer.selectedFeatureCount()
      if total == 0:
        hasSelected = False
        iter = self.layer.getFeatures()
        total = self.layer.featureCount()

      return ( iter, total, hasSelected )

    ( iterFeat, totalFeat, hasSelected ) = getFeatureIteratorTotal()
    if totalFeat == 0:
      msg = "Not have images for processing."
      arg = ( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.WARNING, 4 ) 
      self.msgBar.pushMessage( *arg )
      return { 'isOk': False }

    msg = "selected" if hasSelected else "all"
    msg = "Processing {0} images({1})...".format( totalFeat, msg )
    arg = ( CatalogPL.pluginName, self.msgBar, msg, totalFeat, funcKill, hasProgressFile )
    self.mbcancel = MessageBarCancelProgress( *arg )
    self.enableRun.emit( False )
    self.legendCatalogLayer.enabledProcessing( False )
    return { 'isOk': True, 'iterFeat': iterFeat }

  def _endProcessing(self, nameProcessing, totalError):
    self.enableRun.emit( True )
    if self.layerTree is None:
      self.msgBar.popWidget()
      return
    
    self.legendCatalogLayer.enabledProcessing()
    
    self.msgBar.popWidget()
    if not self.mbcancel.isCancel and totalError > 0:
      msg = "Has error in download (total = {0}) - See log messages".format( totalError )
      arg = ( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.CRITICAL, 4 )
      self.msgBar.pushMessage( *arg )
      return

    if self.mbcancel.isCancel:
      f_msg = "Canceled '{0}' by user"
      typMessage = QgsGui.QgsMessageBar.WARNING
    else:
      f_msg = "Finished '{0}'"
      typMessage = QgsGui.QgsMessageBar.INFO
    
    msg = f_msg.format( nameProcessing )
    self.msgBar.clearWidgets()
    self.msgBar.pushMessage( self.pluginName, msg, typMessage, 4 )

  def _setGroupCatalog(self, typeImage):
    def existsGroupCatalog():
      groups = [ n for n in root.children() if n.nodeType() == QgsCore.QgsLayerTreeNode.NodeGroup ]
      return self.catalog['ltg'] in groups

    def createGroupCatalog():
      self.catalog['satellite'] = self.settings['current_asset']
      self.catalog['typeImage'] = typeImage 
      self.catalog['ltg'] = root.addGroup( 'Calculating...' )

    root = QgsCore.QgsProject.instance().layerTreeRoot()
    if self.catalog['ltg'] is None:
      createGroupCatalog()
    if not self.catalog['satellite'] == self.settings['current_asset']:
      createGroupCatalog()
    if not existsGroupCatalog():
      createGroupCatalog()
    else:
      self.catalog['ltg'].removeAllChildren()

  def _getValuesAssets(self, assets_status):
    def getValues(asset):
      status = assets_status[asset]['status'] # active, inactive, *Need calculate*, *None*
      if status in ('*Need calculate*', '*None*'):
        return { 'isOk': False, 'status': status }
      r = { 'isOk': True, 'status': status }
      if assets_status[asset].has_key('activate'):
        r['activate'] = assets_status[asset]['activate']
      if assets_status[asset].has_key('location'):
        r['location'] = assets_status[asset]['location']
      return r

    return { 'analytic': getValues('a_analytic'), 'udm': getValues('a_udm') }

  def _calculateTotalAsset(self, name_asset, valuesAssets, totalAssets):
    asset = valuesAssets[ name_asset ]
    if not asset['isOk']:
      return
    if asset['status'] == 'inactive' and asset.has_key('activate'):
      totalAssets[ name_asset ]['activate'] += 1
    if asset.has_key('location'):
      totalAssets[ name_asset ]['images'] += 1

  def _hasLimiteErrorOK(self, response):
    err = response['errorCode']
    l1 = API_PlanetLabs.errorCodeLimitOK[0]-1
    l2 = API_PlanetLabs.errorCodeLimitOK[1]+1
    return err > l1 and err < l2 

  def _hasErrorDownloads(self, response):
    if response['errorCode'] in API_PlanetLabs.errorCodeDownloads.keys():
      msg = API_PlanetLabs.errorCodeDownloads[ response['errorCode'] ]
      msg = "{0}(code {1})".format( msg, response['errorCode'] )
      return { 'isOk': True, 'message': msg }
    return { 'isOk': False }

  def _sortNameGroupCatalog(self, reverse=True):
      def getLayers():
        ltls = self.catalog['ltg'].findLayers()
        if len( ltls ) == 0:
          return
        # Sort layer
        d_name_layerd = {}
        for ltl in ltls:
          layer = ltl.layer()
          name = layer.name()
          d_name_layerd[ name ] = layer
        l_name_sorted = sorted( d_name_layerd.keys() )
        #
        layers = [ d_name_layerd[ name] for name in  l_name_sorted ]
  
        return layers
  
      def getGroupsDate(layers):
        groupDates =  {} # 'date': layers }
        for l in layers:
          date = l.customProperty('date', '_errorT').split('T')[0]
          if not date in groupDates.keys():
            groupDates[ date ] = [ l ]
          else:
            groupDates[ date ].append( l )
        return groupDates
  
      def addGroupDates(groupDates):
        keys = sorted(groupDates.keys(), reverse=reverse )
        for idx, key in enumerate( keys ):
          name = "{0} [{1}]".format( key, len( groupDates[ key ] ) )
          ltg = self.catalog['ltg'].insertGroup( idx, name )
          for l in groupDates[ key ]:
            ltg.addLayer( l ).setVisible( QtCore.Qt.Unchecked )
          ltg.setExpanded(False)
        self.catalog['ltg'].removeChildren( len( keys), len( layers) )
  
      def setNameGroupCatalog(total):
        arg = ( self.catalog['satellite'], self.catalog['typeImage'], total ) 
        name = "PL Catalog {} ({}) [{}]".format( *arg )
        self.catalog['ltg'].setName( name )

      layers = getLayers()
      groupDates = getGroupsDate( layers )
      addGroupDates( groupDates )
      setNameGroupCatalog( len( groupDates ) )

  def hostLive(self):
    def setFinished(response):
      self.isOkPL = response[ 'isHostLive' ]
      if not self.isOkPL:
        self.messagePL = response[ 'message' ]
      loop.quit()

    loop = QtCore.QEventLoop()
    msg = "Checking server..."
    self.msgBar.pushMessage( self.pluginName, msg, QgsGui.QgsMessageBar.INFO )
    self.enableRun.emit( False )
    self.apiPL.isHostLive( setFinished )
    loop.exec_()
    self.msgBar.popWidget()
    if not self.isOkPL:
      self.msgBar.pushMessage( self.pluginName, self.messagePL, QgsGui.QgsMessageBar.CRITICAL, 4 )
      self.messagePL = None
    self.isHostLive = self.isOkPL
    self.enableRun.emit( True )

  def registerKey(self):
    
    def dialogGetKey():
      def setResult( isValid ):
        self.hasRegisterKey = isValid

      dataDlg = {
       'parent': self.mainWindow,
       'windowTitle': CatalogPL.pluginName,
       'icon': self.icon
      }
      dataMsgBox = {
        'title': "Planet Labs Register Key",
        'msg': "Do you would like register your Planet Labs key (QGIS setting)?"
      }
      # Accept -> set Key in API_PlanetLabs
      self.mngLogin.dialogLogin( dataDlg, dataMsgBox, setResult )

    def setFinished(response):
      self.isOkPL = response[ 'isOk' ]
      loop.quit()
      
    self.enableRun.emit( False )

    key =  self.mngLogin.getKeySetting()
    if key is None:
      dialogGetKey()
      return

    msg = "Checking register key..."
    self.msgBar.pushMessage( self.pluginName, msg, QgsGui.QgsMessageBar.INFO )
    loop = QtCore.QEventLoop()
    self.apiPL.setKey( key, setFinished )
    loop.exec_()
    self.msgBar.popWidget()
    if not self.isOkPL :
      msg = "Your registered Key not is valid. It will be removed in QgsCore.QGis setting! Please enter a new key."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.CRITICAL, 4 ) 
      self.mngLogin.removeKey()
    self.hasRegisterKey = self.isOkPL
    self.enableRun.emit( True )

  def createLayerScenes(self):
    def createLayer():
      atts = [
        "id:string(25)", "acquired:string(35)", "thumbnail:string(2000)",
        "meta_html:string(2000)", "meta_json:string(2000)",
        "meta_jsize:integer"
      ]
      l_fields = map( lambda item: "field=%s" % item, atts  )
      l_fields.insert( 0, "Multipolygon?crs=epsg:4326" )
      l_fields.append( "index=yes" )
      uri = '&'.join( l_fields )
      
      date1 = self.settings['date1'].toString( QtCore.Qt.ISODate )
      date2 = self.settings['date2'].toString( QtCore.Qt.ISODate )
      name = "PL {}({} to {})".format( self.settings['current_asset'], date1, date2)
      vl = QgsCore.QgsVectorLayer( uri, name, "memory" )
      # Add layer
      self.layer = QgsCore.QgsMapLayerRegistry.instance().addMapLayer( vl, addToLegend=False )
      self.layerTree = QgsCore.QgsProject.instance().layerTreeRoot().insertLayer( 0, self.layer )
      # Symbology
      ns = os.path.join( os.path.dirname( __file__ ), CatalogPL.styleFile )
      self.layer.loadNamedStyle( ns )
      QgsUtils.iface.legendInterface().refreshLayerSymbology( self.layer )
      self.layerTree.setVisible( QtCore.Qt.Unchecked )

    def removeFeatures():
      prov = self.layer.dataProvider()
      if prov.featureCount() > 0:
        self.layer.startEditing()
        prov.deleteFeatures( self.layer.allFeatureIds() )
        self.layer.commitChanges()
        self.layer.updateExtents()

    def populateLayer():
      def processScenes(json_request):
        def setFinishedPL(response):
          self.isOkPL = response['isOk']
          if self.isOkPL:
            self.total_features_scenes = response['total']
            self.url_scenes = response['url_scenes']
          else:
            self.messagePL = response[ 'message' ]

          loop.quit()

        loop = QtCore.QEventLoop()
        self.apiPL.getUrlScenes( json_request, setFinishedPL )
        loop.exec_()
        if not self.isOkPL: 
          self.hasCriticalMessage = True
          self.msgBar.popWidget()
          self.msgBar.pushMessage( CatalogPL.pluginName, self.messagePL, QgsGui.QgsMessageBar.CRITICAL, 4 )
          self.messagePL = None
          self.total_features_scenes = None

      def addFeatures( ):
        def setFinishedPL(response):
          self.isOkPL = response['isOk']
          if self.isOkPL:
            ( self.url_scenes, self.scenes ) = ( response['url'], response['scenes'] )
          else:
            self.messagePL = response['message']

          loop.quit()

        def setScenesResponse():
          def getFeatures():
            fields = [ 'id', 'acquired', 'thumbnail', 'meta_html', 'meta_json', 'meta_jsize' ] # See FIELDs order from createLayer
            features = []
            for item in self.scenes:
              # Fields
              meta_json = item['properties']
              vFields =  { }
              vFields[ fields[0] ] = item['id']
              vFields[ fields[1] ] = meta_json['acquired']
              del meta_json['acquired']
              vFields[ fields[2] ] = "Need download thumbnail"
              meta_json['assets_status'] = {
                'a_analytic': { 'status': '*Need calculate*' },
                'a_udm': { 'status': '*Need calculate*' }
              }
              vFields[ fields[3] ] = API_PlanetLabs.getHtmlTreeMetadata( meta_json, '')
              vjson = json.dumps( meta_json )
              vFields[ fields[4] ] = vjson
              vFields[ fields[5] ] = len( vjson)
              # Geom
              geomItem = item['geometry']
              geomCoords = geomItem['coordinates']
              if geomItem['type'] == 'Polygon':
                qpolygon = map ( lambda polyline: map( lambda item: QgsCore.QgsPoint( item[0], item[1] ), polyline ), geomCoords )
                geom = QgsCore.QgsGeometry.fromMultiPolygon( [ qpolygon ] )
              elif geomItem['type'] == 'MultiPolygon':
                qmultipolygon = []
                for polygon in geomCoords:
                    qpolygon = map ( lambda polyline: map( lambda item: QgsCore.QgsPoint( item[0], item[1] ), polyline ), polygon )
                    qmultipolygon.append( qpolygon )
                geom = QgsCore.QgsGeometry.fromMultiPolygon( qmultipolygon )
              else:
                continue
              feat = QgsCore.QgsFeature()
              feat.setGeometry( geom )

              atts = map( lambda item: vFields[ item ], fields )
              feat.setAttributes( atts )
              features.append( feat )

            return features

          def commitFeatures():
            if not self.layerTree is None and len( features ) > 0:
              self.layer.startEditing()
              prov.addFeatures( features )
              self.layer.commitChanges()
              self.layer.updateExtents()

          if self.isOkPL: 
            if len( self.scenes ) == 0:
              return
            features = getFeatures()
            del self.scenes[:]
            self.total_features_scenes += len( features ) 
            commitFeatures()
            del features[:]
          else:
            self.hasCriticalMessage = True
            self.msgBar.popWidget()
            self.msgBar.pushMessage( CatalogPL.pluginName, self.messagePL, QgsGui.QgsMessageBar.CRITICAL, 4 )
            self.messagePL = None
            self.url_scenes = None
            self.scenes = []

        loop = QtCore.QEventLoop()
        self.apiPL.getScenes( self.url_scenes,  setFinishedPL )
        loop.exec_()
        setScenesResponse()

      def createRubberBand():

        def canvasRect( ):
          # Adaption from "https://github.com/sourcepole/qgis-instantprint-plugin/blob/master/InstantPrintTool.py" 
          mtp  = self.canvas.mapSettings().mapToPixel()
          rect = self.canvas.extent().toRectF()
          p1 = mtp.transform( QgsCore.QgsPoint( rect.left(), rect.top() ) )
          p2 = mtp.transform( QgsCore.QgsPoint( rect.right(), rect.bottom() ) )
          return QtCore.QRect( p1.x(), p1.y(), p2.x() - p1.x(), p2.y() - p1.y() )

        rb = QgsGui.QgsRubberBand( self.canvas, False )
        rb.setBorderColor( QtGui.QColor( 0, 255 , 255 ) )
        rb.setWidth( 2 )
        rb.setToCanvasRectangle( canvasRect() )
        return rb

      def extentFilter():
        crsCanvas = self.canvas.mapSettings().destinationCrs()
        crsLayer = self.layer.crs()
        ct = QgsCore.QgsCoordinateTransform( crsCanvas, crsLayer )
        extent = self.canvas.extent() if crsCanvas == crsLayer else ct.transform( self.canvas.extent() )
        return json.loads( QgsCore.QgsGeometry.fromRect( extent ).exportToGeoJSON() )

      def get_item_types():
        # Same list of DialogImageSettingPL.nameAssets
        item_types = {
          'planet':   'PSScene4Band',
          'rapideye': 'REScene',
          'landsat8': 'Landsat8L1G',
          'sentinel2': 'Sentinel2L1C'
        }
        return [ item_types[ self.settings['current_asset'] ] ]

      def finished():
        self.canvas.scene().removeItem( rb )
        if not self.hasCriticalMessage:
          self.msgBar.popWidget()
          
        if self.layerTree is None:
          return
        self.layerTree.setCustomProperty ('showFeatureCount', True )
        
        msg = "Finished the search of images. Found %d images" % self.total_features_scenes
        typeMessage = QgsGui.QgsMessageBar.INFO
        if self.mbcancel.isCancel:
          self.msgBar.popWidget()
          removeFeatures()
          typeMessage = QgsGui.QgsMessageBar.WARNING
          msg = "Canceled the search of images. Removed %d features" % self.total_features_scenes
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, typeMessage, 4 )

      date1 = self.settings['date1']
      date2 = self.settings['date2']
      days = date1.daysTo( date2)
      date1, date2 = date1.toString( QtCore.Qt.ISODate ), date2.toString( QtCore.Qt.ISODate )
      sdate1 = "{0}T00:00:00.000000Z".format( date1 )
      sdate2 = "{0}T00:00:00.000000Z".format( date2 )

      self.msgBar.clearWidgets()
      msg = "Starting the search of images - %s(%d days)..." % ( date2, days ) 
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.INFO )
      rb = createRubberBand() # Show Rectangle of Query (coordinate in pixel)
      # JSon request
      geometry_filter = {
        'type': 'GeometryFilter',
        'field_name': 'geometry',
        'config': extentFilter()
      }
      date_range_filter = {
        'type': 'DateRangeFilter',
        'field_name': 'acquired',
        'config': { 'gte': sdate1, 'lte': sdate2 }
      }
      permission_filter = {
        'type': 'PermissionFilter',
        'config': ['assets.analytic:download'] 
      }
      #config = [ geometry_filter, date_range_filter, permission_filter ] 
      config = [ geometry_filter, date_range_filter ]
      json_request = {
        "item_types": get_item_types(),
        "filter": { "type": "AndFilter", "config": config }
      }
      processScenes( json_request )
      if self.hasCriticalMessage:
        self.canvas.scene().removeItem( rb )
        return
      if self.total_features_scenes == 0:
        self.canvas.scene().removeItem( rb )
        msg = "Not found images"
        self.msgBar.popWidget()
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.WARNING, 2 )
        return

      self.msgBar.popWidget()
      item_types = ",".join( json_request['item_types'] )
      msg = "Item types: {2}".format( date2, days, item_types )
      self.mbcancel = MessageBarCancel( CatalogPL.pluginName, self.msgBar, msg, self.apiPL.kill )
      self.total_features_scenes = 0

      prov = self.layer.dataProvider()
      while self.url_scenes:
        if self.mbcancel.isCancel or self.layerTree is None :
          break
        addFeatures()
        msg = "Adding {0} features...".format( self.total_features_scenes )
        self.mbcancel.message( msg )

      finished()

    def checkLayerLegend():
      # self.settings setting by __init__.setSearchSettings()
      if self.settings['isOk']:
        return True
      if not self.settings['has_path']:
        msg = "Please setting the directory for download in Planet Labs Catalog layer"
      else:
        msg = "The directory '{0}' not found, please setting directory in Planet Labs Catalog layer"
        msg = msg.format( self.settings['path'] )
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.WARNING, 6 )
      return False

    self.enableRun.emit( False )

    # Setting Layer
    if not self.layer is None:
      QgsCore.QgsMapLayerRegistry.instance().removeMapLayer( self.layer.id() )
    createLayer()
    self.layerTree.setVisible(QtCore.Qt.Unchecked)

    if not checkLayerLegend():
      self.legendCatalogLayer.setLayer( self.layer )
      self.enableRun.emit( True )
      return

    self.hasCriticalMessage = False
    populateLayer() # addFeatures().commitFeatures() -> QtCore.QEventLoop()
    self.legendCatalogLayer.setLayer( self.layer )
    self.enableRun.emit( True )

  def getTotalAssets(self):
    iterFeat = self.layer.selectedFeaturesIterator()
    if self.layer.selectedFeatureCount() == 0:
      iterFeat = self.layer.getFeatures()

    totalAssets = {
      'analytic': { 'images': 0, 'activate': 0 },
      'udm':      { 'images': 0, 'activate': 0 }
    }
    for feat in iterFeat:  
      meta_json = json.loads( feat['meta_json'] )
      valuesAssets = self._getValuesAssets( meta_json['assets_status'] )

      self._calculateTotalAsset('analytic', valuesAssets, totalAssets )
      self._calculateTotalAsset('udm', valuesAssets, totalAssets )

    return totalAssets 

  @QtCore.pyqtSlot(str)
  def layerWillBeRemoved(self, id):
    if not self.layerTree is None and id == self.layer.id():
      self.apiPL.kill()
      self.worker.kill()
      self.legendCatalogLayer.clean()
      self.layerTree = self.layer = None

  @QtCore.pyqtSlot()
  def clearKey(self):
    def dialogQuestion():
      title = "Planet Labs"
      msg = "Are you sure want clear the register key?"
      msgBox = QtGui.QMessageBox( QtGui.QMessageBox.Question, title, msg, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,  self.mainWindow )
      msgBox.setDefaultButton( QtGui.QMessageBox.No )
      return msgBox.exec_()

    if self.mngLogin.getKeySetting() is None:
      msg = "Already cleared the register key. Next run QGIS will need enter the key."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.INFO, 4 )
      self.legendCatalogLayer.enabledClearKey( False )
      return
    
    if QtGui.QMessageBox.Yes == dialogQuestion():
      self.mngLogin.removeKey()
      msg = "Cleared the register key. Next run QGIS will need enter the key."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.INFO, 4 )
      self.legendCatalogLayer.enabledClearKey( False )

  @QtCore.pyqtSlot()
  def clipboardKey(self):
    cb = QtGui.QApplication.clipboard()
    key = self.mngLogin.getKeySetting()
    if key is None:
      key = "Don't have key registered"
    cb.setText( key, mode=cb.Clipboard )    

  @QtCore.pyqtSlot()
  def settingImages(self):
    settings = self.settings if self.settings['isOk'] else None 
    dlg = DialogImageSettingPL( self.mainWindow, self.icon, settings )
    if dlg.exec_() == QtGui.QDialog.Accepted:
      self.settings = dlg.getData()
      self.legendCatalogLayer.enabledProcessing()

  @QtCore.pyqtSlot()
  def createTMS_ServerXYZ(self):
    @QtCore.pyqtSlot( dict )
    def finished( message ):
      self.thread.quit()
      self.worker.finished.disconnect( finished )
      self._endProcessing( "Create TMS", message['totalError'] )

    self._setGroupCatalog('TMS')
    r = self._startProcess( self.worker.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    path_tms = os.path.join( self.settings['path'], 'tms')
    if not os.path.exists( path_tms ):
      os.makedirs( path_tms )

    self.worker.finished.connect( finished )
    self.worker.setting( iterFeat, ltgRoot, self.catalog['ltg'] ) # 
    self.worker.stepProgress.connect( self.mbcancel.step )
    self.thread.start() # Start Worker
    #self.worker.run() #DEBUGER

  @QtCore.pyqtSlot()
  def calculateAssetStatus(self):
    @QtCore.pyqtSlot( dict )
    def finished( response ):
      if self.mbcancel.isCancel:
        self.messagePL = None
      else:
        self.messagePL = response['assets_status']
      loop.quit()

    r = self._startProcess( self.apiPL.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    id_meta_json = self.layer.fieldNameIndex('meta_json')
    id_meta_html = self.layer.fieldNameIndex('meta_html')
    isEditable = self.layer.isEditable()
    if not isEditable:
      self.layer.startEditing()
    totalAssets = {
      'analytic': { 'images': 0, 'activate': 0 },
      'udm':      { 'images': 0, 'activate': 0 }
    }
    loop = QtCore.QEventLoop()
    step = totalError = 0
    for feat in iterFeat:  
      step += 1
      self.mbcancel.step( step )
      meta_json = json.loads( feat['meta_json'] )
      ( ok, item_type ) = API_PlanetLabs.getValue( meta_json, [ 'item_type' ] )
      if not ok:
        totalError += 1
        continue
      self.apiPL.getAssetsStatus( item_type, feat['id'], finished )
      loop.exec_()
      if self.mbcancel.isCancel or self.layerTree is None :
        step -= 1
        iterFeat.close()
        break
      meta_json['assets_status'] = self.messagePL
      valuesAssets = self._getValuesAssets( meta_json['assets_status'] )
      self._calculateTotalAsset('analytic', valuesAssets, totalAssets )
      self._calculateTotalAsset('udm', valuesAssets, totalAssets )
      meta_html = API_PlanetLabs.getHtmlTreeMetadata( meta_json, '')
      vjson = json.dumps( meta_json )
      self.messagePL.clear()
      self.messagePL = None
      if not self.layer.changeAttributeValue( feat.id(), id_meta_json, vjson ):
        totalError += 1
      if not self.layer.changeAttributeValue( feat.id(), id_meta_html, meta_html ):
        totalError += 1

    self.layer.commitChanges()
    if isEditable:
      self.layer.startEditing()

    self._endProcessing( "Calculate Asset Status", totalError )
    self.legendCatalogLayer.setAssetImages( totalAssets )

  ## Its is for API V0! Not update
  
  @QtCore.pyqtSlot()
  def activateAssets(self):
    def activeAsset(asset, activate, dataLocal):
      def setFinished( response ):
        if not response[ 'isOk' ] and not self._hasLimiteErrorOK(response ):
          r =  self._hasErrorDownloads(response)
          if r['isOk']:
            arg = ( self.currentItem, r['message'] )
            msg = "Error request for {0}: {1}".format( *arg )
          else:
            arg = ( self.currentItem, response['message'], response[ 'errorCode' ] )
            msg = "Error request for {0}: {1} (Code = {2})".format( *arg )
          self.logMessage( msg, CatalogPL.pluginName, QgsCore.QgsMessageLog.CRITICAL )
          self.currentItem = None
          self.isOkPL = False
        loop.quit()

      self.mbcancel.step( dataLocal['step'] )
      if self.mbcancel.isCancel or self.layerTree is None :
        dataLocal['step'] -= 1
        iterFeat.close()
        return False
      self.currentItem = "'{0}({1})'".format( feat['id'], asset )
      self.isOkPL = True
      self.apiPL.activeAsset( activate, setFinished )
      loop.exec_()
      if not self.isOkPL:
        dataLocal['totalError'] += 1
      return True # Not cancel by user
    
    #msg = "Sorry! I am working this feature for API Planet V1"
    #self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsGui.QgsMessageBar.CRITICAL, 8 )
    #return
    r = self._startProcess( self.apiPL.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    dataLocal = { 'totalError': 0, 'step': 0 }
    loop = QtCore.QEventLoop()
    for feat in iterFeat:
      dataLocal['step'] += 1
      meta_json = json.loads( feat['meta_json'] )
      valuesAssets = self._getValuesAssets( meta_json['assets_status'] )
      asset = 'analytic'
      if valuesAssets[ asset ]['isOk'] and \
         valuesAssets[ asset ]['status'] == 'inactive' and \
         valuesAssets[ asset ].has_key('activate'):
        if not activeAsset( asset, valuesAssets[ asset ]['activate'], dataLocal ):
          break # Cancel by user
      asset = 'udm'
      if valuesAssets[ asset ]['isOk'] and \
         valuesAssets[ asset ]['status'] == 'inactive' and \
         valuesAssets[ asset ].has_key('activate'):
        if not activeAsset( asset, valuesAssets[ asset ]['activate'], dataLocal ):
          break # Cancel by user

    self._endProcessing( "Activate assets", dataLocal['totalError'] ) 

  @QtCore.pyqtSlot()
  def CreateTMS_GDAL_WMS(self):
    @QtCore.pyqtSlot( dict )
    def finished( message ):
      self.thread.quit()
      self.worker.finished.disconnect( finished )
      self._sortNameGroupCatalog()
      self._endProcessing( "Create TMS", message['totalError'] )

    self._setGroupCatalog('TMS')
    r = self._startProcess( self.worker.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    path_tms = os.path.join( self.settings['path'], 'tms')
    if not os.path.exists( path_tms ):
      os.makedirs( path_tms )
    cr3857 = QgsCore.QgsCoordinateReferenceSystem( 3857, QgsCore.QgsCoordinateReferenceSystem.EpsgCrsId )
    ctTMS = QgsCore.QgsCoordinateTransform( self.layer.crs(), cr3857 )

    self.worker.finished.connect( finished )
    data = {
      'pluginName': CatalogPL.pluginName,
      'getURL': API_PlanetLabs.getURL_TMS,
      'user_pwd': { 'user': API_PlanetLabs.validKey, 'pwd': '' }, 
      'path': path_tms,
      'ltgCatalog': self.catalog['ltg'],
      'id_layer': self.layer.id(),
      'ctTMS': ctTMS,
      'iterFeat': iterFeat # feat: 'id', 'acquired', 'meta_json'
    }
    self.worker.setting( data )
    
    self.worker.stepProgress.connect( self.mbcancel.step )
    self.thread.start() # Start Worker
    #self.worker.run() #DEBUGER

  @QtCore.pyqtSlot()
  def downloadThumbnails(self):
    def setFinished( response ):
      if response[ 'isOk' ]:
        self.pixmap = response[ 'pixmap' ]
      else:
        arg = ( self.currentItem, response['message'], response['errorCode'] )
        msg = "Error request for {0}: {1} (Code = {2})".format( *arg )
        self.logMessage( msg, CatalogPL.pluginName, QgsCore.QgsMessageLog.CRITICAL )
        self.currentItem = None
        self.pixmap = None
      loop.quit()

    def createThumbnails():
      self.currentItem = feat['id']
      arg = ( feat['meta_json'], ['item_type'] )
      ( ok, item_type ) = API_PlanetLabs.getValue( *arg )
      if not ok:
        totalError += 1
        response = { 'isOk': False, 'errorCode': -1, 'message': item_type }
        setFinished( response )
      else:
        self.apiPL.getThumbnail( feat['id'], item_type, setFinished )

    r = self._startProcess( self.apiPL.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    totalError = step = 0
    self.pixmap = None # Populate(self.apiPL.getThumbnail) and catch(setFinished)
    id_thumbnail = self.layer.fieldNameIndex('thumbnail')
    path_thumbnail = os.path.join( self.settings['path'], 'thumbnail')
    if not os.path.exists( path_thumbnail ):
      os.makedirs( path_thumbnail )
    isEditable = self.layer.isEditable()
    if not isEditable:
      self.layer.startEditing()
    loop = QtCore.QEventLoop()
    for feat in iterFeat:
      step += 1
      self.mbcancel.step( step )
      if self.mbcancel.isCancel or self.layerTree is None :
        iterFeat.close()
        step -= 1
        break
      arg = ( path_thumbnail, u"{0}_thumbnail.png".format( feat['id'] ) )
      file_thumbnail = os.path.join( *arg )
      if not QtCore.QFile.exists( file_thumbnail ):
        createThumbnails()
        loop.exec_()
        if not self.pixmap is None:
          isOk = self.pixmap.save( file_thumbnail, "PNG")
          del self.pixmap
          self.pixmap = None
          if not isOk:
            totalError += 1
          else:
            arg = ( feat.id(), id_thumbnail, file_thumbnail  ) 
            self.layer.changeAttributeValue( *arg ) 
        else:
          totalError += 1
      else:
        arg = ( feat.id(), id_thumbnail, file_thumbnail  )
        self.layer.changeAttributeValue( *arg )

    self.layer.commitChanges()
    if isEditable:
      self.layer.startEditing()

    self._endProcessing( "Download Thumbnails", totalError ) 

  @QtCore.pyqtSlot()
  def downloadImages(self):
    def createImage(suffix, location, id_table, geom, v_crs, acquired, id_image, dataLocal, add_image=False):
      def setFinished( response ):
        self.imageDownload.flush()
        self.imageDownload.close()
        if not response[ 'isOk' ] and not self._hasLimiteErrorOK(response ):
          r =  self._hasErrorDownloads(response)
          if r['isOk']:
            arg = ( self.currentItem, r['message'] )
            msg = "Error request for {0}: {1}".format( *arg )
          else:
            arg = ( self.currentItem, response['message'], response[ 'errorCode' ] )
            msg = "Error request for {0}: {1} (Code = {2})".format( *arg )
          self.logMessage( msg, CatalogPL.pluginName, QgsCore.QgsMessageLog.CRITICAL )
          self.currentItem = None
          self.isOkPL = False
          self.totalReady = None
          self.imageDownload.remove()
        else:
          self.totalReady = response[ 'totalReady' ]
          fileName = self.imageDownload.fileName()
          self.imageDownload.rename( '.'.join( fileName.rsplit('.')[:-1] ) )
        del self.imageDownload
        self.imageDownload = None
        loop.quit()

      def addImage():
        layer = QgsCore.QgsRasterLayer( file_image, os.path.split( file_image )[-1] )
        geomTransf = QgsCore.QgsGeometry( geom )
        ct = QgsCore.QgsCoordinateTransform( v_crs, layer.crs() )
        geomTransf.transform( ct )
        wkt_geom = geomTransf.exportToWkt()
        layer.setCustomProperty( 'wkt_geom', wkt_geom )
        layer.setCustomProperty( 'date', acquired )
        layer.setCustomProperty( 'id_table', id_table )
        layer.setCustomProperty( 'id_image', id_image )
        QgsCore.QgsMapLayerRegistry.instance().addMapLayer( layer, addToLegend=False )
        self.catalog['ltg'].addLayer( layer )
        self.legendRasterGeom.setLayer( layer )
      
      arg = ( path_img, u"{0}_{1}.tif".format( feat['id'], suffix ) )
      file_image = os.path.join( *arg )
      self.mbcancel.step( dataLocal['step'], file_image )
      if self.mbcancel.isCancel or self.layerTree is None :
        dataLocal['step'] -= 1
        iterFeat.close()
        return False
      self.isOkPL = True
      if not QtCore.QFile.exists( file_image ):
        self.currentItem = "'{0}({1})'".format( feat['id'], suffix )
        self.imageDownload = QtCore.QFile( "{0}.part".format( file_image ) )
        self.imageDownload.open( QtCore.QIODevice.WriteOnly )
        arg = ( location, setFinished, self.imageDownload.write, self.mbcancel.stepFile )
        self.apiPL.saveImage( *arg )
        loop.exec_()
        if not self.isOkPL:
          dataLocal['totalError'] += 1
      if add_image and self.isOkPL:
        files_in_map = map( lambda item: item.layer().source(), dataLocal['ltgRoot'].findLayers() )
        if not file_image in files_in_map:
          addImage()
      return True # Not cancel by user

    self._setGroupCatalog('TIF')
    r = self._startProcess( self.worker.kill, True )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    path_img = os.path.join( self.settings['path'], 'tif')    
    if not os.path.exists( path_img ):
      os.makedirs( path_img )
      
    crsLayer = self.layer.crs()
    id_table = self.layer.id()
    dataLocal = { 'totalError': 0, 'step': 0, 'ltgRoot': ltgRoot }
    self.totalReady = None
    loop = QtCore.QEventLoop()
    for feat in iterFeat:
      dataLocal['step'] += 1
      meta_json = json.loads( feat['meta_json'] )
      valuesAssets = self._getValuesAssets( meta_json['assets_status'] )
      arg_core = [ id_table, feat.geometry(), crsLayer, feat['acquired'], feat['id'], dataLocal ]
      asset = 'analytic'
      if valuesAssets[ asset ]['isOk'] and valuesAssets[ asset ].has_key('location'):
        arg_base = [ valuesAssets[ asset ]['location'] ] + arg_core
        arg = [ asset ] + arg_base + [ True ] 
        if not createImage( *arg ):
          break # Cancel by user
      if self.settings['udm']:
        asset = 'udm'
        if valuesAssets[ asset ]['isOk'] and valuesAssets[ asset ].has_key('location'):
          arg_base = [ valuesAssets[ asset ]['location'] ] + arg_core
          arg = [ asset] + arg_base
          if not createImage( *arg ):
            break # Cancel by user

    self._sortNameGroupCatalog()
    self._endProcessing( "Download Images", dataLocal['totalError'] ) 

  @staticmethod
  def copyExpression():
    dirname = os.path.dirname
    fromExp = os.path.join( dirname( __file__ ), CatalogPL.expressionFile )
    dirExp = os.path.join( dirname( dirname( dirname( __file__ ) ) ), CatalogPL.expressionDir )
    toExp = os.path.join( dirExp , CatalogPL.expressionFile )
    if os.path.isdir( dirExp ):
      if QtCore.QFile.exists( toExp ):
        QtCore.QFile.remove( toExp ) 
      QtCore.QFile.copy( fromExp, toExp ) 
