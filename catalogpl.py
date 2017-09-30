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

from PyQt4.QtCore import ( Qt, QObject, QDate, QDateTime, QFile, QDir, QIODevice, pyqtSignal,
                           pyqtSlot, QEventLoop, QThread, QRect )
from PyQt4.QtGui  import ( QApplication, QDialog, QMessageBox, QLabel, QToolButton,
                           QColor, QProgressBar )

import qgis
from qgis.core import ( QgsApplication, QgsProject, QgsMapLayerRegistry,
                        QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsGeometry, QgsPoint,
                        QgsCoordinateTransform, QgsCoordinateReferenceSystem,
                        QgsMessageLog, QgsDataSourceURI )
from qgis.gui  import ( QgsMessageBar, QgsRubberBand )

from apiqtpl import API_PlanetLabs
from legendlayerpl import ( DialogImageSettingPL, LegendCatalogLayer )
from legendlayer import ( LegendRaster, LegendTMS )

from managerloginkey import ManagerLoginKey
from curses.has_key import has_key
from __builtin__ import True

class MessageBarCancelProgressDownload(QObject):

  def __init__(self, msgBar, msg, maximum, funcKill, hasProgressFile=False):
    def initGui():
      self.pb = QProgressBar( self.msgBar )
      self.pb.setAlignment( Qt.AlignLeft )
      self.lb = QLabel( self.msgBar )
      self.tbCancel = QToolButton( self.msgBar )
      self.tbCancel.setIcon( QgsApplication.getThemeIcon( "/mActionCancelAllEdits.svg" ) )
      self.tbCancel.setToolTip( "Cancel download")
      self.tbCancel.setText( "Cancel")
      self.tbCancel.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
      self.widget = self.msgBar.createMessage( CatalogPL.pluginName, msg )

      widgets = [ self.tbCancel, self.lb, self.pb ]
      lyt = self.widget.layout()
      for item in widgets:
        lyt.addWidget( item )
      del widgets[:]

      if hasProgressFile:
        self.pbFile = QProgressBar( self.msgBar )
        self.pbFile.setAlignment( Qt.AlignLeft )
        self.pbFile.setValue( 1 )
        lyt.addWidget( self.pbFile )

    super(MessageBarCancelProgressDownload, self).__init__()
    ( self.msgBar, self.maximum ) = ( msgBar, maximum )
    self.pb = self.lb = self.widget = self.isCancel = self.pbFile = None
    initGui()
    self.tbCancel.clicked.connect( self.clickedCancel )
    self.pb.destroyed.connect( self.destroyed)

    self.msgBar.pushWidget( self.widget, QgsMessageBar.INFO )
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

  @pyqtSlot( 'QObject' )
  def destroyed(self, obj):
    self.pb = None

  @pyqtSlot(bool)
  def clickedCancel(self, checked):
    if self.pb is None:
      return
    self.kill()
    self.isCancel = True

  @pyqtSlot(int, int)
  def stepFile(self, bytesReceived, bytesTotal):
    if self.pb is None:
      return

    self.pbFile.setMaximum( bytesTotal )
    self.pbFile.setValue( bytesReceived )

class MessageBarCancel(QObject):

  def __init__(self, msgBar, msg, funcKill):
    def initGui():
      self.tbCancel = QToolButton( msgBar )
      self.tbCancel.setIcon( QgsApplication.getThemeIcon( "/mActionCancelAllEdits.svg" ) )
      self.tbCancel.setText( "Cancel")
      self.tbCancel.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
      self.widget = msgBar.createMessage( CatalogPL.pluginName, msg )

      lyt = self.widget.layout()
      lyt.addWidget( self.tbCancel )

    super(MessageBarCancel, self).__init__()
    self.widget = self.isCancel = None
    initGui()
    self.tbCancel.clicked.connect( self.clickedCancel )

    msgBar.pushWidget( self.widget, QgsMessageBar.INFO )
    self.isCancel = False
    self.kill = funcKill

  def message(self, msg):
    if not self.isCancel:
      self.widget.setText( msg )

  @pyqtSlot(bool)
  def clickedCancel(self, checked):
    self.kill()
    self.isCancel = True

class WorkerSaveTMS(QObject):

  finished = pyqtSignal( dict )
  stepProgress = pyqtSignal( int )

  def __init__(self, legendTMS ):
    super(WorkerSaveTMS, self).__init__()
    self.legendTMS = legendTMS
    self.isKilled = None # set in run
    self.path = self.ctTMS = self.iterFeat = None # setting
    self.ltgRoot = self.ltgCatalog, self.msgDownload = None # setting

  def setting(self, path, ctTMS, iterFeat, ltgRoot, ltgCatalog, msgDownload):
   self.path = path
   self.ctTMS = ctTMS
   self.iterFeat = iterFeat
   self.ltgRoot = ltgRoot
   self.ltgCatalog = ltgCatalog
   self.msgDownload = msgDownload

  @pyqtSlot()
  def run(self):
    def saveTMS(feat, fileDownload):
      def contenTargetWindow():
        r = self.ctTMS.transform( feat.geometry().boundingBox() )
        targetWindow  = { 'ulX': r.xMinimum(), 'ulY': r.yMaximum(), 'lrX': r.xMaximum(), 'lrY': r.yMinimum() }
        return '<TargetWindow>\n'\
              '  <UpperLeftX>%f</UpperLeftX>\n'\
              '  <UpperLeftY>%f</UpperLeftY>\n'\
              '  <LowerRightX>%f</LowerRightX>\n'\
              '  <LowerRightY>%f</LowerRightY>\n'\
              '</TargetWindow>\n' % (
                targetWindow['ulX'], targetWindow['ulY'], targetWindow['lrX'], targetWindow['lrY'] )

      def contentTMS():
        return '<GDAL_WMS>\n'\
              '<!-- Planet Labs -->\n'\
              '<Service name="TMS">\n'\
              '<ServerUrl>%s</ServerUrl>\n'\
              '<Transparent>TRUE</Transparent>\n'\
              '</Service>\n'\
              '<DataWindow>\n'\
              '<UpperLeftX>-20037508.34</UpperLeftX>\n'\
              '<UpperLeftY>20037508.34</UpperLeftY>\n'\
              '<LowerRightX>20037508.34</LowerRightX>\n'\
              '<LowerRightY>-20037508.34</LowerRightY>\n'\
              '<TileLevel>15</TileLevel>\n'\
              '<TileCountX>1</TileCountX>\n'\
              '<TileCountY>1</TileCountY>\n'\
              '<YOrigin>top</YOrigin>\n'\
              '</DataWindow>\n'\
              '%s'\
              '<Projection>EPSG:3857</Projection>\n'\
              '<BlockSizeX>256</BlockSizeX>\n'\
              '<BlockSizeY>256</BlockSizeY>\n'\
              '<BandsCount>4</BandsCount>\n'\
              '<DataType>byte</DataType>\n'\
              '<ZeroBlockHttpCodes>204,303,400,404,500,501</ZeroBlockHttpCodes>\n'\
              '<ZeroBlockOnServerException>true</ZeroBlockOnServerException>\n'\
              '<MaxConnections>5</MaxConnections>\n'\
              '<UserPwd>%s</UserPwd>\n'\
              '<Cache>\n'\
              '<Path>%s</Path>\n'\
              '</Cache>\n'\
              '</GDAL_WMS>\n' % ( server_url, target_window, user_pwd, cache_path )

      ( ok, item_type ) = API_PlanetLabs.getValue( feat['meta_json'], [ 'item_type' ] )
      if not ok:
        return
      server_url = API_PlanetLabs.urlTMS.format( item_type=item_type, item_id=feat['id'] )
      user_pwd = API_PlanetLabs.validKey
      cache_path = "%s/cache_pl_%s.tms" % ( self.path, feat['id'] )
      target_window = contenTargetWindow()
      content_tms = contentTMS() 
      fileDownload.write( content_tms )

    def addImage(image):
      if not image in map( lambda item: item.layer().source(), self.ltgRoot.findLayers() ):
        layer = QgsRasterLayer( image, os.path.split( image )[-1] )
        QgsMapLayerRegistry.instance().addMapLayer( layer, addToLegend=False )
        self.ltgCatalog.addLayer( layer).setVisible( Qt.Unchecked )
        self.legendTMS.setLayer( layer )

    self.isKilled = False
    numError = step = 0
    for feat in self.iterFeat:
      step += 1
      self.stepProgress.emit( step )  
      if self.isKilled:
        self.iterFeat.close()
        break
      image = os.path.join( self.path, u"%s_tms.xml" % feat['id'] )
      if not QFile.exists( image ):
        fileDownload = QFile( image )
        fileDownload.open( QIODevice.WriteOnly )
        saveTMS( feat, fileDownload )
        fileDownload.close()

      addImage( image )

    self.msgDownload = self.msgDownload.replace( str( 'Download_total' ), str ( step  ) ) 
    message  = { 'numError': numError, 'msgDownload': self.msgDownload }
    self.finished.emit( message )

  def kill(self):
    self.isKilled = True

class WorkerCreateTMS(QObject):

  finished = pyqtSignal( dict )
  stepProgress = pyqtSignal( int )

  def __init__(self, logMessage, legendTMS ):
    super(WorkerCreateTMS, self).__init__()
    self.logMessage, self.legendTMS = logMessage, legendTMS
    self.isKilled = None # set in run
    self.iterFeat = self.ltgRoot = self.ltgCatalog = self.msgDownload = None # setting

  def setting(self, iterFeat, ltgRoot, ltgCatalog):
   self.iterFeat, self.ltgRoot, self.ltgCatalog  = iterFeat, ltgRoot, ltgCatalog

  @pyqtSlot()
  def run(self):
    def addTMS():
      server_url = API_PlanetLabs.urlTMS.format( item_type=item_type, item_id=item_id )
      urlkey = "{0}?api_key={1}".format( server_url, user_pwd )
      uri.setParam('url', urlkey )
      lyr = QgsRasterLayer( str( uri.encodedUri() ), item_id , 'wms')
      if not lyr.isValid():
        msg = "Error create TMS from {0}: Invalid layer".format( item_id )
        self.logMessage( msg, CatalogPL.pluginName, QgsMessageLog.CRITICAL )
        totalError += 1
        return
      if not lyr.source() in sources_catalog_group:
        lyr.setCustomProperty( 'wkt_geom', wkt_geom )
        mlr.addMapLayer( lyr, addToLegend=False )
        self.ltgCatalog.addLayer( lyr ).setVisible( Qt.Unchecked )
        self.legendTMS.setLayer( lyr )

    mlr = QgsMapLayerRegistry.instance()
    user_pwd = API_PlanetLabs.validKey
    uri = QgsDataSourceURI()
    uri.setParam('type', 'xyz' )
    sources_catalog_group = map( lambda item: item.layer().source(), self.ltgRoot.findLayers() )

    self.isKilled = False
    step = totalError = 0
    for feat in self.iterFeat:
      step += 1
      self.stepProgress.emit( step )
      if self.isKilled:
        self.iterFeat.close()
        break
      item_id = feat['id']
      ( ok, item_type ) = API_PlanetLabs.getValue( feat['meta_json'], [ 'item_type' ] )
      if not ok:
        msg = "Error create TMS from {0}: {1}".format( item_id, item_type)
        self.logMessage( msg, CatalogPL.pluginName, QgsMessageLog.CRITICAL )
        totalError += 1
        continue
      wkt_geom = feat.geometry().exportToWkt()
      addTMS()
      uri.removeParam('url')

    message  = { 'totalError': totalError }
    self.finished.emit( message )

  def kill(self):
    self.isKilled = True

class CatalogPL(QObject):

  pluginName = u'Catalog Planet Labs'
  styleFile = 'pl_scenes.qml'
  expressionFile = 'pl_expressions.py'
  expressionDir = 'expressions'

  enableRun = pyqtSignal( bool )
  
  def __init__(self, iface, icon):
    def setLegendCatalogLayer():
      # keys = LegendCatalogLayer.legendMenuIDs 
      slots = { 
         'clear_key': self.clearKey,
         'clipboard_key': self.clipboardKey,
         'setting_images': self.settingImages,
         'calculate_status_assets': self.calculateAssetStatus,
         'activate_assets': self.activateAssets,
         'create_tms': self.createTMS,
         'download_images': self.downloadImages,
         'download_thumbnails': self.downloadThumbnails
      }
      arg = ( CatalogPL.pluginName, slots, self.getTotalAssets )
      self.legendCatalogLayer = LegendCatalogLayer( *arg )

    def setSearchSettings():
      self.searchSettings = DialogImageSettingPL.getDownloadSettings()
      
      # Next step add all informations (DialogImageSettingPL.getDownloadSettings)
      # 'planet', 'rapideye', 'landsat8', 'sentinel2', 'date1', 'date2'
      # planet = self.searchSettings['planet'] ...
      # date1 = self.searchSettings['date1'] ...
      #
      self.searchSettings['planet']    = True
      self.searchSettings['rapideye']  = False
      self.searchSettings['landsat8']  = False
      self.searchSettings['sentinel2'] = False

      date2 = QDate.currentDate()
      date1 = date2.addMonths( -1 )
      self.searchSettings['date1'] = date1 
      self.searchSettings['date2'] = date2

    super(CatalogPL, self).__init__()
    self.canvas = iface.mapCanvas()
    self.msgBar = iface.messageBar()
    self.logMessage = QgsMessageLog.instance().logMessage
    self.icon = icon
    self.mainWindow = iface.mainWindow()

    self.apiPL = API_PlanetLabs()
    self.mngLogin = ManagerLoginKey('catalogpl_plugin')
    self.legendRaster = LegendRaster( CatalogPL.pluginName )
    self.legendTMS = LegendTMS( CatalogPL.pluginName )
    self.thread = self.worker = None # initThread
    self.mbcancel = None # Need for worker it is be class attribute
    self.isHostLive = False
    self.hasRegisterKey = False

    self.layer = self.layerTree = None
    self.hasCriticalMessage = None
    self.url_scenes = self.scenes = self.total_features_scenes = None 
    self.pixmap = self.messagePL = self.isOkPL = None
    self.legendCatalogLayer = self.searchSettings = None
    self.imageDownload = self.totalReady = None
    self.currentItem = None
    self.ltgCatalog = None

    setLegendCatalogLayer()
    setSearchSettings()
    self._connect()
    self._initThread()

  def __del__(self):
    self._connect( False )
    self._finishThread()
    del self.legendRaster
    del self.legendTMS

  def _initThread(self):
    self.thread = QThread( self )
    self.thread.setObjectName( "QGIS_Plugin_Catalog_PlanetLabs" )
    self.worker = WorkerCreateTMS( self.logMessage, self.legendTMS )
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
    s = { 'signal': QgsMapLayerRegistry.instance().layerWillBeRemoved, 'slot': self.layerWillBeRemoved }
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
      arg = ( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 ) 
      self.msgBar.pushMessage( *arg )
      return { 'isOk': False }

    msg = "selected" if hasSelected else "all"
    msg = "Processing {0} images({1})...".format( totalFeat, msg )
    arg = ( self.msgBar, msg, totalFeat, funcKill, hasProgressFile )
    self.mbcancel = MessageBarCancelProgressDownload( *arg )
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
      arg = ( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 4 )
      self.msgBar.pushMessage( *arg )
      return

    if self.mbcancel.isCancel:
      f_msg = "Canceled '{0}' by user"
      typMessage = QgsMessageBar.WARNING
    else:
      f_msg = "Finished '{0}'"
      typMessage = QgsMessageBar.INFO
    
    msg = f_msg.format( nameProcessing )
    self.msgBar.clearWidgets()
    self.msgBar.pushMessage( self.pluginName, msg, typMessage, 4 )

  def _setGroupCatalog(self, ltgRoot):
    nameGroup = "{0} - Catalog".format( self.layer.name() )
    self.ltgCatalog = ltgRoot.findGroup( nameGroup  )
    if self.ltgCatalog is None:
      self.ltgCatalog = ltgRoot.addGroup( nameGroup )
    else:
      self.ltgCatalog.removeAllChildren()

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
      return { 'isOk': True, 'message': msg }
    return { 'isOk': False }

  def hostLive(self):
    def setFinished(response):
      self.isOkPL = response[ 'isHostLive' ]
      if not self.isOkPL:
        self.messagePL = response[ 'message' ]
      loop.quit()

    loop = QEventLoop()
    msg = "Checking server..."
    self.msgBar.pushMessage( self.pluginName, msg, QgsMessageBar.INFO )
    self.enableRun.emit( False )
    self.apiPL.isHostLive( setFinished )
    loop.exec_()
    self.msgBar.popWidget()
    if not self.isOkPL:
      self.msgBar.pushMessage( self.pluginName, self.messagePL, QgsMessageBar.CRITICAL, 4 )
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
    self.msgBar.pushMessage( self.pluginName, msg, QgsMessageBar.INFO )
    loop = QEventLoop()
    self.apiPL.setKey( key, setFinished )
    loop.exec_()
    self.msgBar.popWidget()
    if not self.isOkPL :
      msg = "Your registered Key not is valid. It will be removed in QGis setting! Please enter a new key."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 4 ) 
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
      vl = QgsVectorLayer( uri, "pl_scenes", "memory" )
      self.layer = QgsMapLayerRegistry.instance().addMapLayer( vl )
      self.layerTree = QgsProject.instance().layerTreeRoot().findLayer( self.layer.id() )
      self.layer.loadNamedStyle( os.path.join( os.path.dirname( __file__ ), CatalogPL.styleFile ) )
      qgis.utils.iface.legendInterface().refreshLayerSymbology( self.layer )

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

        loop = QEventLoop()
        self.apiPL.getUrlScenes( json_request, setFinishedPL )
        loop.exec_()
        if not self.isOkPL: 
          self.hasCriticalMessage = True
          self.msgBar.popWidget()
          self.msgBar.pushMessage( CatalogPL.pluginName, self.messagePL, QgsMessageBar.CRITICAL, 4 )
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
                qpolygon = map ( lambda polyline: map( lambda item: QgsPoint( item[0], item[1] ), polyline ), geomCoords )
                geom = QgsGeometry.fromMultiPolygon( [ qpolygon ] )
              elif geomItem['type'] == 'MultiPolygon':
                qmultipolygon = []
                for polygon in geomCoords:
                    qpolygon = map ( lambda polyline: map( lambda item: QgsPoint( item[0], item[1] ), polyline ), polygon )
                    qmultipolygon.append( qpolygon )
                geom = QgsGeometry.fromMultiPolygon( qmultipolygon )
              else:
                continue
              feat = QgsFeature()
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
            self.msgBar.pushMessage( CatalogPL.pluginName, self.messagePL, QgsMessageBar.CRITICAL, 4 )
            self.messagePL = None
            self.url_scenes = None
            self.scenes = []

        loop = QEventLoop()
        self.apiPL.getScenes( self.url_scenes,  setFinishedPL )
        loop.exec_()
        setScenesResponse()

      def createRubberBand():

        def canvasRect( ):
          # Adaption from "https://github.com/sourcepole/qgis-instantprint-plugin/blob/master/InstantPrintTool.py" 
          mtp  = self.canvas.mapSettings().mapToPixel()
          rect = self.canvas.extent().toRectF()
          p1 = mtp.transform( QgsPoint( rect.left(), rect.top() ) )
          p2 = mtp.transform( QgsPoint( rect.right(), rect.bottom() ) )
          return QRect( p1.x(), p1.y(), p2.x() - p1.x(), p2.y() - p1.y() )

        rb = QgsRubberBand( self.canvas, False )
        rb.setBorderColor( QColor( 0, 255 , 255 ) )
        rb.setWidth( 2 )
        rb.setToCanvasRectangle( canvasRect() )
        return rb

      def extentFilter():
        crsCanvas = self.canvas.mapSettings().destinationCrs()
        crsLayer = self.layer.crs()
        ct = QgsCoordinateTransform( crsCanvas, crsLayer )
        extent = self.canvas.extent() if crsCanvas == crsLayer else ct.transform( self.canvas.extent() )
        return json.loads( QgsGeometry.fromRect( extent ).exportToGeoJSON() )

      def get_item_types():
        keys = ('planet', 'rapideye', 'landsat8', 'sentinel2')
        item_types = {
          'planet':   'PSScene4Band',
          'rapideye': 'REScene',
          'landsat8': 'Landsat8L1G',
          'sentinel2': 'Sentinel2L1C'
        }
        return [ item_types[k] for k in keys if self.searchSettings[k] ]

      def finished():
        self.canvas.scene().removeItem( rb )
        if not self.hasCriticalMessage:
          self.msgBar.popWidget()
          
        if self.layerTree is None:
          return
        
        msg = "Finished the search of images. Found %d images" % self.total_features_scenes
        typeMessage = QgsMessageBar.INFO
        if self.mbcancel.isCancel:
          self.msgBar.popWidget()
          removeFeatures()
          typeMessage = QgsMessageBar.WARNING
          msg = "Canceled the search of images. Removed %d features" % self.total_features_scenes
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, typeMessage, 4 )

      date1 = self.searchSettings['date1']
      date2 = self.searchSettings['date2']
      days = date1.daysTo( date2)
      date1, date2 = date1.toString( Qt.ISODate ), date2.toString( Qt.ISODate )
      sdate1 = "{0}T00:00:00.000000Z".format( date1 )
      sdate2 = "{0}T00:00:00.000000Z".format( date2 )

      self.msgBar.clearWidgets()
      msg = "Starting the search of images - %s(%d days)..." % ( date2, days ) 
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.INFO )
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
      config = [ geometry_filter, date_range_filter, permission_filter ] 
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
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 2 )
        return

      self.msgBar.popWidget()
      item_types = ",".join( json_request['item_types'] )
      msg = "Item types: {2}".format( date2, days, item_types )
      self.mbcancel = MessageBarCancel( self.msgBar, msg, self.apiPL.kill )
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

      # self.layerTree is None by slot layerWillBeRemoved
      if self.layerTree is None:   
        return

      self.layerTree.setVisible(Qt.Unchecked)
      
      # self.searchSettings setting by __init__.setSearchSettings()
      if not self.searchSettings['isOk']:
        msg = "Please setting the Planet Labs Catalog layer"
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 )
        self.legendCatalogLayer.enabledProcessing( False )
        return
      if not QDir( self.searchSettings[ 'path' ] ).exists() :
        msg = "Register directory '%s' does not exist! Please setting the Planet Labs Catalog layer" % self.searchSettings['path']
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 4 )
        self.legendCatalogLayer.enabledProcessing( False )
        return

    self.enableRun.emit( False )

    # Setting Layer
    if not self.layer is None:
      QgsMapLayerRegistry.instance().removeMapLayer( self.layer.id() )
    createLayer()

    self.hasCriticalMessage = False
    populateLayer() # addFeatures().commitFeatures() -> QEventLoop()
    self.legendCatalogLayer.setLayer( self.layer )
    checkLayerLegend()
    self.enableRun.emit( True )

  def getTotalAssets_origin(self):
    r = {
      'analytic': { 'images': 0, 'activate': 0 },
      'udm':      { 'images': 0, 'activate': 0 }
    }
    return r

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

  @pyqtSlot(str)
  def layerWillBeRemoved(self, id):
    if not self.layerTree is None and id == self.layer.id():
      self.apiPL.kill()
      self.worker.kill()
      self.legendCatalogLayer.clean()
      self.layerTree = self.layer = None

  @pyqtSlot()
  def clearKey(self):
    def dialogQuestion():
      title = "Planet Labs"
      msg = "Are you sure want clear the register key?"
      msgBox = QMessageBox( QMessageBox.Question, title, msg, QMessageBox.Yes | QMessageBox.No,  self.mainWindow )
      msgBox.setDefaultButton( QMessageBox.No )
      return msgBox.exec_()

    if self.mngLogin.getKeySetting() is None:
      msg = "Already cleared the register key. Next run QGIS will need enter the key."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.INFO, 4 )
      self.legendCatalogLayer.enabledClearKey( False )
      return
    
    if QMessageBox.Yes == dialogQuestion():
      self.mngLogin.removeKey()
      msg = "Cleared the register key. Next run QGIS will need enter the key."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.INFO, 4 )
      self.legendCatalogLayer.enabledClearKey( False )

  @pyqtSlot()
  def clipboardKey(self):
    cb = QApplication.clipboard()
    key = self.mngLogin.getKeySetting()
    if key is None:
      key = "Don't have key registered"
    cb.setText( key, mode=cb.Clipboard )    

  @pyqtSlot()
  def settingImages(self):
    settings = self.searchSettings if self.searchSettings['isOk'] else None 
    dlg = DialogImageSettingPL( self.mainWindow, self.icon, settings )
    if dlg.exec_() == QDialog.Accepted:
      self.searchSettings = dlg.getData()
      self.legendCatalogLayer.enabledProcessing()

  @pyqtSlot()
  def createTMS(self):
    @pyqtSlot( dict )
    def finished( message ):
      self.thread.quit()
      self.worker.finished.disconnect( finished )
      self._endProcessing( "Create TMS", message['totalError'] )

    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog(ltgRoot)

    r = self._startProcess( self.worker.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    self.worker.finished.connect( finished )
    self.worker.setting( iterFeat, ltgRoot, self.ltgCatalog )
    self.worker.stepProgress.connect( self.mbcancel.step )
    self.thread.start() # Start Worker
    #self.worker.run() #DEBUGER

  @pyqtSlot()
  def calculateAssetStatus(self):
    @pyqtSlot( dict )
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
    loop = QEventLoop()
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
  
  @pyqtSlot()
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
          self.logMessage( msg, CatalogPL.pluginName, QgsMessageLog.CRITICAL )
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
    #self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 8 )
    #return
    r = self._startProcess( self.apiPL.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    dataLocal = { 'totalError': 0, 'step': 0 }
    loop = QEventLoop()
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

    self._endProcessing( "Download Images", dataLocal['totalError'] ) 

  @pyqtSlot()
  def downloadTMS(self):
    @pyqtSlot( dict )
    def finished( message ):
      numError =  message[ 'numError' ]
      msgDownload =  message[ 'msgDownload' ]
      
      self.thread.quit()
      self.worker.finished.disconnect( finished )
      self.enableRun.emit( True )
  
      if not self.mbcancel.isCancel and self.worker.isKilled:
        self.msgBar.popWidget()
        msg = "Canceled by user"
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 8 )
        return
      
      if numError > 0:
        msg = "Error request: %s (Code = %d)" % ( response[ 'message' ], response[ 'errorCode' ] )
        self.logMessage( msg, CatalogPL.pluginName, QgsMessageLog.CRITICAL )

      self.legendCatalogLayer.enabledProcessing()
      self._endProcessing( numError, msgDownload )

    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog(ltgRoot)

    ( path, total, msgDownload, iterFeat ) = self._getFeatureIteratorTotal( "TMS" )
    if total == 0:
      msg = "Not images for download."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 )
      return

    cr3857 = QgsCoordinateReferenceSystem( 3857, QgsCoordinateReferenceSystem.EpsgCrsId )
    ctTMS = QgsCoordinateTransform( self.layer.crs(), cr3857 )
    self.mbcancel = MessageBarCancelProgressDownload( self.msgBar, "%s..." % msgDownload, total, self.worker.kill )
    msgDownload = msgDownload.replace( str( total ), 'Download_total' )
    
    self.worker.finished.connect( finished )
    self.worker.setting( path, ctTMS, iterFeat, ltgRoot, self.ltgCatalog, msgDownload )
    self.worker.stepProgress.connect( self.mbcancel.step )
    self.thread.start() # Start Worker
    #self.worker.run() #DEBUGER

  @pyqtSlot()
  def downloadThumbnails(self):
    def setFinished( response ):
      if response[ 'isOk' ]:
        self.pixmap = response[ 'pixmap' ]
      else:
        arg = ( self.currentItem, response['message'], response['errorCode'] )
        msg = "Error request for {0}: {1} (Code = {2})".format( *arg )
        self.logMessage( msg, CatalogPL.pluginName, QgsMessageLog.CRITICAL )
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
    path_thumbnail = self.searchSettings['path']
    isEditable = self.layer.isEditable()
    if not isEditable:
      self.layer.startEditing()
    loop = QEventLoop()
    for feat in iterFeat:
      step += 1
      self.mbcancel.step( step )
      if self.mbcancel.isCancel or self.layerTree is None :
        iterFeat.close()
        step -= 1
        break
      arg = ( path_thumbnail, u"{0}_thumbnail.png".format( feat['id'] ) )
      file_thumbnail = os.path.join( *arg )
      if not QFile.exists( file_thumbnail ):
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

  @pyqtSlot()
  def downloadImages_original(self):
    def setFinished( response ):
      self.imageDownload.flush()
      self.imageDownload.close()

      if response[ 'isOk' ]:
        self.totalReady = response[ 'totalReady' ]
        fileName = self.imageDownload.fileName()
        self.imageDownload.rename( '.'.join( fileName.rsplit('.')[:-1] ) )
      else:
        msg = "Error request for %s: %s (Code = %d)" % ( self.currentItem, response[ 'message' ], response[ 'errorCode' ] )
        self.logMessage( msg, CatalogPL.pluginName, QgsMessageLog.CRITICAL )
        self.currentItem = None
        self.totalReady = None
        self.imageDownload.remove()

      del self.imageDownload
      self.imageDownload = None
      loop.quit()

    def addImage():
      if not image in map( lambda item: item.layer().source(), ltgRoot.findLayers() ):
        layer = QgsRasterLayer( image, os.path.split( image )[-1] )
        QgsMapLayerRegistry.instance().addMapLayer( layer, addToLegend=False )
        self.ltgCatalog.addLayer( layer)
        self.legendRaster.setLayer( layer )

    msg = "Sorry! I am working this feature for API Planet V1"
    self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 8 )
    return
    
    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog(ltgRoot)

    ( path, total, msgDownload, iter ) = self._getFeatureIteratorTotal( "images" )
    if total == 0:
      msg = "Not images for download."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 )
      return

    self.mbcancel = MessageBarCancelProgressDownload( self.msgBar, "%s..." % msgDownload, total, self.apiPL.kill, True )
    step = 1

    isVisual = self.searchSettings['isVisual']
    suffix = u"visual" if isVisual else u"analytic"
    self.totalReady = None
    loop = QEventLoop()

    self.enableRun.emit( False )
    self.legendCatalogLayer.enabledProcessing( False )
    numError = 0
    for feat in iter:
      image = os.path.join( path, u"%s_%s.tif" % ( feat['id'], suffix ) )
      self.mbcancel.step( step, image )
      if self.mbcancel.isCancel or self.layerTree is None :
        step -= 1
        iter.close()
        break
      if not QFile.exists( image ):
        self.currentItem = feat['id']
        self.imageDownload = QFile( "%s.part" % image )
        self.imageDownload.open( QIODevice.WriteOnly )
        json = feat['meta_json']
        self.apiPL.saveImage( json, isVisual, setFinished, self.imageDownload.write, self.mbcancel.stepFile )
        loop.exec_()
        if self.totalReady is None:
          numError += 1
        else:
          addImage()
      else:
        addImage()
      step += 1

    self.enableRun.emit( True )
    if self.layerTree is None:
      self.msgBar.popWidget()
      return

    self.legendCatalogLayer.enabledProcessing()
    step -= 1
    msg = msgDownload.replace( str( total ), str ( step  ) ) 
    self._endProcessing( numError, msg )

  @pyqtSlot()
  def downloadImages(self):
    def createImageAsset(asset, location, dataLocal, add_image=False):
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
          self.logMessage( msg, CatalogPL.pluginName, QgsMessageLog.CRITICAL )
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
        layer = QgsRasterLayer( file_image, os.path.split( file_image )[-1] )
        QgsMapLayerRegistry.instance().addMapLayer( layer, addToLegend=False )
        self.ltgCatalog.addLayer( layer)
        self.legendRaster.setLayer( layer )
  
      arg = ( self.searchSettings['path'], u"{0}_{1}.tif".format( feat['id'], asset ) )
      file_image = os.path.join( *arg )
      self.mbcancel.step( dataLocal['step'], file_image )
      if self.mbcancel.isCancel or self.layerTree is None :
        dataLocal['step'] -= 1
        iterFeat.close()
        return False
      self.isOkPL = True
      if not QFile.exists( file_image ):
        self.currentItem = "'{0}({1})'".format( feat['id'], asset )
        self.imageDownload = QFile( "{0}.part".format( file_image ) )
        self.imageDownload.open( QIODevice.WriteOnly )
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

    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog(ltgRoot)

    r = self._startProcess( self.apiPL.kill, True )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    dataLocal = { 'totalError': 0, 'step': 0, 'ltgRoot': ltgRoot }
    self.totalReady = None
    loop = QEventLoop()
    for feat in iterFeat:
      dataLocal['step'] += 1
      meta_json = json.loads( feat['meta_json'] )
      valuesAssets = self._getValuesAssets( meta_json['assets_status'] )
      asset = 'analytic'
      if valuesAssets[ asset ]['isOk'] and valuesAssets[ asset ].has_key('location'):
        if not createImageAsset( asset, valuesAssets[ asset ]['location'], dataLocal, True ):
          break # Cancel by user
      asset = 'udm'
      if valuesAssets[ asset ]['isOk'] and valuesAssets[ asset ].has_key('location'):
        if not createImageAsset( asset, valuesAssets[ asset ]['location'], dataLocal ):
          break # Cancel by user

    self._endProcessing( "Download Images", dataLocal['totalError'] ) 

  @staticmethod
  def copyExpression():
    dirname = os.path.dirname
    fromExp = os.path.join( dirname( __file__ ), CatalogPL.expressionFile )
    dirExp = os.path.join( dirname( dirname( dirname( __file__ ) ) ), CatalogPL.expressionDir )
    toExp = os.path.join( dirExp , CatalogPL.expressionFile )
    if os.path.isdir( dirExp ):
      if QFile.exists( toExp ):
        QFile.remove( toExp ) 
      QFile.copy( fromExp, toExp ) 
