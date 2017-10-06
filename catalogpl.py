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
from legendlayer import LegendRasterGeom

from managerloginkey import ManagerLoginKey

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

class WorkerCreateTMS_GDAL_WMS(QObject):
  finished = pyqtSignal( dict )
  stepProgress = pyqtSignal( int )

  def __init__(self, logMessage, legendRasterGeom ):
    super(WorkerCreateTMS_GDAL_WMS, self).__init__()
    self.logMessage, self.legendRasterGeom = logMessage, legendRasterGeom
    self.isKilled = None # set in run
    self.path = self.ctTMS = self.iterFeat = None # setting
    self.ltgRoot = self.ltgCatalog = None # setting

  def setting(self, id_layer, path, ctTMS, iterFeat, ltgRoot, ltgCatalog):
   self.id_table = id_layer
   self.path = path
   self.ctTMS = ctTMS
   self.iterFeat = iterFeat
   self.ltgRoot = ltgRoot
   self.ltgCatalog = ltgCatalog

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
              '<ServerUrl>{server_url}</ServerUrl>\n'\
              '<Transparent>TRUE</Transparent>\n'\
              '<SRS>EPSG:3857</SRS>\n'\
              '<ImageFormat>image/png</ImageFormat>\n'\
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
              '{target_window}'\
              '<Projection>EPSG:3857</Projection>\n'\
              '<BlockSizeX>256</BlockSizeX>\n'\
              '<BlockSizeY>256</BlockSizeY>\n'\
              '<BandsCount>4</BandsCount>\n'\
              '<DataType>byte</DataType>\n'\
              '<UserAgent>Mozilla/5.0</UserAgent>\n'\
              '<ZeroBlockHttpCodes>204,303,400,404,500,501</ZeroBlockHttpCodes>\n'\
              '<ZeroBlockOnServerException>true</ZeroBlockOnServerException>\n'\
              '<MaxConnections>5</MaxConnections>\n'\
              '<UserPwd>{user_pwd}:</UserPwd>\n'\
              '<Cache>\n'\
              '<Path>{cache_path}</Path>\n'\
              '</Cache>\n'\
              '</GDAL_WMS>\n'.format( server_url=server_url, target_window=target_window, user_pwd=user_pwd, cache_path=cache_path )

      server_url = API_PlanetLabs.urlTMS.format( item_type=item_type, item_id=feat['id'] )
      # Change for GDAL_WMS
      for c in ['{z}', '{x}', '{y}']:
        server_url = server_url.replace( c, "${0}".format( c ) )
      cache_path = "{0}/cache_pl_{1}.tms".format( self.path, feat['id'] )
      target_window = contenTargetWindow()
      content_tms = contentTMS() 
      fileDownload.write( content_tms )

    def addTMS():
      if not image in sources_catalog_group:
        geomTransf = QgsGeometry(feat.geometry() )
        geomTransf.transform( self.ctTMS )
        wkt_geom = geomTransf.exportToWkt()
        layer = QgsRasterLayer( image, os.path.split( image )[-1] )
        layer.setCustomProperty( 'wkt_geom', wkt_geom )
        layer.setCustomProperty( 'date', feat['acquired'] )
        layer.setCustomProperty( 'id_table', self.id_table )
        layer.setCustomProperty( 'id_image', feat['id'] )
        QgsMapLayerRegistry.instance().addMapLayer( layer, addToLegend=False )
        self.ltgCatalog.addLayer( layer).setVisible( Qt.Unchecked )
        self.legendRasterGeom.setLayer( layer )

    mlr = QgsMapLayerRegistry.instance()
    user_pwd = API_PlanetLabs.validKey
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
      image = os.path.join( self.path, u"{0}_tms.xml".format( feat['id'] ) )
      if not QFile.exists( image ):
        fileDownload = QFile( image )
        fileDownload.open( QIODevice.WriteOnly )
        saveTMS( feat, fileDownload )
        fileDownload.close()

      addTMS()

    message  = { 'totalError': totalError }
    self.finished.emit( message )

  def kill(self):
    self.isKilled = True

# Check change in WorkerCreateTMS_GDAL_WMS(path,...)
# Not Runnig!

class WorkerCreateTMS_ServerXYZ(QObject):

  finished = pyqtSignal( dict )
  stepProgress = pyqtSignal( int )

  def __init__(self, logMessage, legendRasterGeom ):
    super(WorkerCreateTMS_ServerXYZ, self).__init__()
    self.logMessage, self.legendRasterGeom = logMessage, legendRasterGeom
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
        self.legendRasterGeom.setLayer( lyr )

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
      self.searchSettings = DialogImageSettingPL.getSettings()
      
      # Next step add all informations (DialogImageSettingPL.getSettings)
      self.searchSettings['current_asset'] = 'planet'
      self.searchSettings['udm'] = False
      date2 = QDate.currentDate()
      date1 = date2.addMonths( -1 )
      self.searchSettings['date1'] = date1 
      self.searchSettings['date2'] = date2

    super(CatalogPL, self).__init__()
    self.canvas = qgis.utils.iface.mapCanvas()
    self.msgBar = qgis.utils.iface.messageBar()
    self.logMessage = QgsMessageLog.instance().logMessage
    self.icon = icon
    self.mainWindow = qgis.utils.iface.mainWindow()

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
    del self.legendRasterGeom

  def _initThread(self):
    self.thread = QThread( self )
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

  def _setGroupCatalog(self, ltgRoot, typeCatalog):
    nameGroup = "{0} - Catalog {1}".format( self.layer.name(), typeCatalog )
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
      msg = "{0}(code {1})".format( msg, response['errorCode'] )
      return { 'isOk': True, 'message': msg }
    return { 'isOk': False }

  def _sortGroupCatalog(self, reverse=True):
    def getLayers():
      ltls = self.ltgCatalog.findLayers()
      if len( ltls ) == 0:
        return
      layers = [ ltl.layer() for ltl in ltls ] 
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
        ltg = self.ltgCatalog.insertGroup( idx, name )
        for l in groupDates[ key ]:
          ltg.addLayer( l ).setVisible( Qt.Unchecked )
        ltg.setExpanded(False)
      self.ltgCatalog.removeChildren( len( keys), len( layers) )

    layers = getLayers()
    groupDates = getGroupsDate( layers )
    addGroupDates( groupDates )

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
      self.layer = QgsMapLayerRegistry.instance().addMapLayer( vl, addToLegend=False )
      ltgRoot = QgsProject.instance().layerTreeRoot()
      self.layerTree = ltgRoot.insertLayer(0, self.layer )
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
        # Same list of DialogImageSettingPL.nameAssets
        item_types = {
          'planet':   'PSScene4Band',
          'rapideye': 'REScene',
          'landsat8': 'Landsat8L1G',
          'sentinel2': 'Sentinel2L1C'
        }
        return [ item_types[ self.searchSettings['current_asset'] ] ]

      def finished():
        self.canvas.scene().removeItem( rb )
        if not self.hasCriticalMessage:
          self.msgBar.popWidget()
          
        if self.layerTree is None:
          return
        self.layerTree.setCustomProperty ('showFeatureCount', True )
        
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
      # self.searchSettings setting by __init__.setSearchSettings()
      if self.searchSettings['isOk']:
        return True
      if not self.searchSettings['has_path']:
        msg = "Please setting the directory for download in Planet Labs Catalog layer"
      else:
        msg = "The directory '{0}' not found, please setting directory in Planet Labs Catalog layer"
        msg = msg.format( self.searchSettings['path'] )
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 6 )
      return False

    self.enableRun.emit( False )

    # Setting Layer
    if not self.layer is None:
      QgsMapLayerRegistry.instance().removeMapLayer( self.layer.id() )
    createLayer()
    self.layerTree.setVisible(Qt.Unchecked)

    if not checkLayerLegend():
      self.legendCatalogLayer.setLayer( self.layer )
      self.enableRun.emit( True )
      return

    self.hasCriticalMessage = False
    populateLayer() # addFeatures().commitFeatures() -> QEventLoop()
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
  def createTMS_ServerXYZ(self):
    @pyqtSlot( dict )
    def finished( message ):
      self.thread.quit()
      self.worker.finished.disconnect( finished )
      self._endProcessing( "Create TMS", message['totalError'] )

    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog( ltgRoot, 'TMS' )

    r = self._startProcess( self.worker.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    path_tms = os.path.join( self.searchSettings['path'], 'tms')
    if not os.path.exists( path_tms ):
      os.makedirs( path_tms )

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

    self._endProcessing( "Activate assets", dataLocal['totalError'] ) 

  @pyqtSlot()
  def CreateTMS_GDAL_WMS(self):
    @pyqtSlot( dict )
    def finished( message ):
      self.thread.quit()
      self.worker.finished.disconnect( finished )
      self._sortGroupCatalog()
      self._endProcessing( "Create TMS", message['totalError'] )

    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog( ltgRoot, 'TMS' )

    r = self._startProcess( self.worker.kill )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    path_tms = os.path.join( self.searchSettings['path'], 'tms')
    if not os.path.exists( path_tms ):
      os.makedirs( path_tms )
    cr3857 = QgsCoordinateReferenceSystem( 3857, QgsCoordinateReferenceSystem.EpsgCrsId )
    ctTMS = QgsCoordinateTransform( self.layer.crs(), cr3857 )

    self.worker.finished.connect( finished )
    arg = ( self.layer.id(), path_tms, ctTMS, iterFeat, ltgRoot, self.ltgCatalog )
    self.worker.setting( *arg )
    
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
    path_thumbnail = os.path.join( self.searchSettings['path'], 'thumbnail')
    if not os.path.exists( path_thumbnail ):
      os.makedirs( path_thumbnail )
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
        geomTransf = QgsGeometry( geom )
        ct = QgsCoordinateTransform( v_crs, layer.crs() )
        geomTransf.transform( ct )
        wkt_geom = geomTransf.exportToWkt()
        layer.setCustomProperty( 'wkt_geom', wkt_geom )
        layer.setCustomProperty( 'date', acquired )
        layer.setCustomProperty( 'id_table', id_table )
        layer.setCustomProperty( 'id_image', id_image )
        QgsMapLayerRegistry.instance().addMapLayer( layer, addToLegend=False )
        self.ltgCatalog.addLayer( layer )
        self.legendRasterGeom.setLayer( layer )
      
      arg = ( path_img, u"{0}_{1}.tif".format( feat['id'], suffix ) )
      file_image = os.path.join( *arg )
      self.mbcancel.step( dataLocal['step'], file_image )
      if self.mbcancel.isCancel or self.layerTree is None :
        dataLocal['step'] -= 1
        iterFeat.close()
        return False
      self.isOkPL = True
      if not QFile.exists( file_image ):
        self.currentItem = "'{0}({1})'".format( feat['id'], suffix )
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
    self._setGroupCatalog( ltgRoot, 'TIF' )

    r = self._startProcess( self.apiPL.kill, True )
    if not r['isOk']:
      return
    iterFeat = r['iterFeat']

    path_img = os.path.join( self.searchSettings['path'], 'tif')    
    if not os.path.exists( path_img ):
      os.makedirs( path_img )
      
    crsLayer = self.layer.crs()
    id_table = self.layer.id()
    dataLocal = { 'totalError': 0, 'step': 0, 'ltgRoot': ltgRoot }
    self.totalReady = None
    loop = QEventLoop()
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
      if self.searchSettings['udm']:
        asset = 'udm'
        if valuesAssets[ asset ]['isOk'] and valuesAssets[ asset ].has_key('location'):
          arg_base = [ valuesAssets[ asset ]['location'] ] + arg_core
          arg = [ asset] + arg_base
          if not createImage( *arg ):
            break # Cancel by user

    self._sortGroupCatalog()
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
