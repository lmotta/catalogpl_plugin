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

from PyQt4.QtCore import ( Qt, QObject, QDate, QFile, QDir, QIODevice, pyqtSignal,
                           pyqtSlot, QEventLoop, QThread, QRect )
from PyQt4.QtGui  import ( QDialog, QLabel, QToolButton, QColor, QProgressBar )

import qgis
from qgis.core import ( QgsApplication, QgsProject, QgsMapLayerRegistry,
                        QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsGeometry, QgsPoint,
                        QgsCoordinateTransform, QgsCoordinateReferenceSystem )
from qgis.gui  import ( QgsMessageBar, QgsRubberBand )

from apiqtpl import API_PlanetLabs
from legendlayerpl import ( DialogImageSettingPL, LegendCatalogLayer )
from legendlayer import ( LegendRaster, LegendTMS )

from managerloginkey import ManagerLoginKey

class MessageBarProgressDownload(QObject):

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

    super(MessageBarProgressDownload, self).__init__()
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


class WorkerSaveTMS(QObject):

  finished = pyqtSignal( dict )
  stepProgress = pyqtSignal( int )

  def __init__(self, legendTMS ):
    super(WorkerSaveTMS, self).__init__()
    self.legendTMS = legendTMS
    self.isKilled = None # set in run
    self.path = self.ctTMS = self.funcStep = self.iterFeat = None # setting
    self.ltgRoot = self.ltgCatalog = None # setting

  def setting(self, path, ctTMS, iterFeat, ltgRoot, ltgCatalog, msgDownload):
   self.path = path
   self.ctTMS = ctTMS
   self.iterFeat = iterFeat
   self.ltgRoot = ltgRoot
   self.ltgCatalog = ltgCatalog
   self.msgDownload = msgDownload

  @pyqtSlot()
  def run(self):
    def saveTMS(url, feat, fileDownload):
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

      server_url = "%s/${z}/${x}/${y}.png" % url.replace( "https://api", "https://tiles")
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

    keys = [ 'links', 'self' ]
    self.isKilled = False
    numError = 0
    step = 1
    for feat in self.iterFeat:
      image = os.path.join( self.path, u"%s_tms.xml" % feat['id'] )
      self.stepProgress.emit( step )
      if not QFile.exists( image ):
        jsonMetadata = feat['metadata_json']
        ( ok, url ) = API_PlanetLabs.getValue( jsonMetadata, keys )
        if not ok:
          numError += 1
          continue
        fileDownload = QFile( image )
        fileDownload.open( QIODevice.WriteOnly )
        saveTMS( url, feat, fileDownload )
        fileDownload.close()

      if self.isKilled:
        self.iterFeat.close()
        break

      addImage( image )
      step += 1

    step -= 1
    self.msgDownload = self.msgDownload.replace( str( 'Download_total' ), str ( step  ) ) 
    message  = { 'numError': numError, 'msgDownload': self.msgDownload }
    self.finished.emit( message )

  def kill(self):
    self.isKilled = True


class CatalogPL(QObject):

  pluginName = "Catalog Planet Labs"
  styleFile = "pl_scenes.qml"
  expressionFile = "pl_expressions.py"
  expressionDir = "expressions"

  enableRun = pyqtSignal( bool )
  
  def __init__(self, iface, icon):
    def setLegendCatalogLayer():
      slots = { 
         'setting': self.settingImages,
         'tms': self.downloadTMS,
         'images': self.downloadImages,
         'thumbnails': self.downloadThumbnails
      }
      self.legendCatalogLayer = LegendCatalogLayer( slots )
      self.downloadSettings = DialogImageSettingPL.getDownloadSettings()
      date2 = QDate.currentDate()
      date1 = date2.addMonths( -1 )
      self.downloadSettings['date1'] = date1 
      self.downloadSettings['date2'] = date2

    super(CatalogPL, self).__init__()
    self.canvas = iface.mapCanvas()
    self.msgBar = iface.messageBar()
    self.icon = icon
    self.mainWindow = iface.mainWindow()

    self.apiPL = API_PlanetLabs()
    self.mngLogin = ManagerLoginKey( "catalogpl_plugin" )
    self.legendRaster = LegendRaster( 'Catalog Planet Labs' )
    self.legendTMS = LegendTMS( 'Catalog Planet Labs' )
    self.thread = self.worker = None # initThread
    self.mbpd = None # Need for worker it is be class attribute
    self.isHostLive = False
    self.hasRegisterKey = False

    self.layer = self.layerTree = None
    self.hasCriticalMessage = None
    self.url_scenes = self.scenes = self.process_scenes = None 
    self.pixmap = self.messagePL = self.isOkPL = None
    self.legendCatalogLayer = self.downloadSettings = None
    self.imageDownload = self.totalReady = None
    self.ltgCatalog = None

    setLegendCatalogLayer()
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
    self.worker = WorkerSaveTMS( self.legendTMS )
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

  def _getInitDataDownload(self, txtDownload):
    path = self.downloadSettings['path']
    total = msg1 = None 
    iter = self.layer.selectedFeaturesIterator()
    if not iter.isClosed():
      total = self.layer.selectedFeatureCount()
      msg1 = "Download %d %s (selected)" % ( total, txtDownload )
    else:
      iter = self.layer.getFeatures()
      total = self.layer.featureCount()
      msg1 = "Download %d %s (total)" % ( total, txtDownload )
    return ( path, total, msg1, iter )

  def _endDownload(self, numError, msg):
    self.msgBar.popWidget()
    if not self.mbpd.isCancel and numError > 0:
      msg2 = "Has error in download (total = %d)" % numError
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 8 )
      return

    msg2 = "Canceled %s" % msg if self.mbpd.isCancel else "Finished %s" % msg 
    self.msgBar.clearWidgets()
    typMessage = QgsMessageBar.WARNING if self.mbpd.isCancel else QgsMessageBar.INFO
    self.msgBar.pushMessage( self.pluginName, msg2, typMessage, 4 )

  def _setGroupCatalog(self, ltgRoot):
    ltgCatalogName = "%s - Catalog" % self.layer.name()
    self.ltgCatalog = ltgRoot.findGroup( ltgCatalogName  )
    if self.ltgCatalog is None:
      self.ltgCatalog = ltgRoot.addGroup( ltgCatalogName )

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
    self.isHostLive = self.isOkPL
    self.enableRun.emit( True )

  def registerKey(self):
    
    def dialogGetKey():
      def setResult( isValid ):
        self.hasRegisterKey = isValid

      dataDlg = {
       'parent': self.mainWindow,
       'windowTitle': "Catalog Planet Labs",
       'icon': self.icon
      }
      dataMsgBox = {
        'title': "Planet Labs Register Key",
        'msg': "Do you would like register your Planet Labs key (QGIS setting)?"
      }
      # Accept -> set Key in API_PlanetLabs
      self.mngLogin.dialogLogin( dataDlg, dataMsgBox, setResult )

    def dialogRemoveKey():
      parent = self.mainWindow
      title = "Planet Labs Register Key"
      msg = "Your registered Key not is valid. It will be removed in QGis setting! Please enter a new key."
      self.mngLogin.dialogRemoveKey( parent, title, msg )

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
      dialogRemoveKey()
    self.hasRegisterKey = self.isOkPL
    self.enableRun.emit( True )

  def downloadScenes(self):

    def createLayer():
      fields = "field=id:string(25)&field=acquired:string(35)&field=metadata_json:string(2000)&field=metadata_values:string(2000)&field=thumbnail:string(2000)"
      uri = "Polygon?crs=epsg:4326&%s&index=yes" % fields
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

      def processScenesOrtho():
        def setFinishedPL(response):
          self.isOkPL = response[ 'isOk' ]
          if self.isOkPL:
            self.process_scenes = response[ 'total' ]
          else:
            self.messagePL = response[ 'message' ]

          loop.quit()

        def setScenesResponse():
          if not self.isOkPL: 
            self.hasCriticalMessage = True
            self.msgBar.popWidget()
            self.msgBar.pushMessage( CatalogPL.pluginName, self.messagePL, QgsMessageBar.CRITICAL, 4 )
            self.process_scenes = None

        loop = QEventLoop()
        self.apiPL.getTotalScenesOrtho( self.url_scenes,  setFinishedPL )
        loop.exec_()
        setScenesResponse()

      def addFeatures( ):
        def setFinishedPL(response):
          self.isOkPL = response[ 'isOk' ]
          if self.isOkPL:
            ( self.url_scenes, self.scenes ) = ( response['url'], response['scenes'] )
          else:
            self.messagePL = response[ 'message' ]

          loop.quit()

        def setScenesResponse():
          def getFeatures():
            fields = [ 'id', 'acquired', 'metadata_json', 'metadata_values', 'thumbnail' ] # See FIELDs order from createMemoryLayer
            features = []
            for item in self.scenes:
              # Fields
              metadata_json = item['properties']
              vFields =  { }
              vFields[ fields[0] ] = item['id']
              vFields[ fields[1] ] = metadata_json['acquired']
              del metadata_json['acquired']
              vFields[ fields[2] ] = API_PlanetLabs.getJsonByObjectPy( metadata_json ) 
              vFields[ fields[3] ] = API_PlanetLabs.getTextValuesMetadata( metadata_json )
              vFields[ fields[4] ] = "Need download thumbnail"
              # Geom
              polygon = item['geometry']['coordinates']
              qpolygon = map ( lambda polyline: map( lambda item: QgsPoint( item[0], item[1] ), polyline ), polygon )
              geom = QgsGeometry.fromPolygon( qpolygon )
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
            features = getFeatures()
            del self.scenes[:]
            self.process_scenes += len( features ) 
            self.mbpd.step( self.process_scenes  )
            commitFeatures()
            del features[:]
          else:
            self.hasCriticalMessage = True
            self.msgBar.popWidget()
            self.msgBar.pushMessage( CatalogPL.pluginName, self.messagePL, QgsMessageBar.CRITICAL, 4 )
            self.url_scenes = None
            self.scenes = []

        loop = QEventLoop()
        self.apiPL.getScenesOrtho( self.url_scenes,  setFinishedPL )
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
        return QgsGeometry.fromRect( extent ).exportToGeoJSON()

      def finished():

        self.canvas.scene().removeItem( rb )
        if not self.hasCriticalMessage:
          self.msgBar.popWidget()
          
        if self.layerTree is None:
          return
        
        msg = "Finished the search of images. Found %d images" % self.process_scenes
        typeMessage = QgsMessageBar.INFO
        if self.mbpd.isCancel:
          self.msgBar.popWidget()
          removeFeatures()
          typeMessage = QgsMessageBar.WARNING
          msg = "Canceled the search of images. Removed %d features" % self.process_scenes
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, typeMessage, 4 )

        if not self.layerTree is None:
          self.legendCatalogLayer.enabledDownload( not self.mbpd.isCancel )

      date1 = self.downloadSettings['date1']
      date2 = self.downloadSettings['date2']
      days = date1.daysTo( date2)
      date1 = date1.toString( Qt.ISODate )
      date2 = date2.toString( Qt.ISODate )

      self.msgBar.clearWidgets()
      msg = "Starting the search of images - %s(%d days)..." % ( date2, days ) 
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.INFO )
      rb = createRubberBand() # Show Rectangle of Query (coordinate in pixel)
      filters = {
          'intersects': extentFilter(),
          'acquired.gte': date1,
          'acquired.lte': date2
      }
      self.url_scenes = self.apiPL.getUrlFilterScenesOrtho( filters )

      processScenesOrtho()
      if self.hasCriticalMessage:
        self.canvas.scene().removeItem( rb )
        return
      if self.process_scenes == 0:
        self.canvas.scene().removeItem( rb )
        msg = "Not found images"
        self.msgBar.popWidget()
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 2 )
        return

      self.msgBar.popWidget()
      msg = "Getting %d images - %s(%d days)..." % ( self.process_scenes, date2, days )
      self.mbpd = MessageBarProgressDownload( self.msgBar, msg, self.process_scenes, self.apiPL.kill )
      self.process_scenes = 0

      prov = self.layer.dataProvider()
      while self.url_scenes:
        if self.mbpd.isCancel or self.layerTree is None :
          break
        addFeatures()

      finished()

    def checkLayerLegend():

      # self.layerTree is None by slot layerWillBeRemoved
      if self.layerTree is None:   
        return

      # self.downloadSettings setting by __init__.setLegendCatalogLayer()
      if not self.downloadSettings['isOk']:
        msg = "Please setting the Planet Labs Catalog layer"
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 )
        self.legendCatalogLayer.enabledDownload( False )
        return
      if not QDir( self.downloadSettings[ 'path' ] ).exists() :
        msg = "Register directory '%s' does not exist! Please setting the Planet Labs Catalog layer" % self.downloadSettings['path']
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 4 )
        self.legendCatalogLayer.enabledDownload( False )
        return

    self.enableRun.emit( False )

    # Setting Layer
    if self.layerTree is None: # Use this because slot layerWillBeRemoved 
      createLayer()
      self.legendCatalogLayer.setLayer( self.layer )
    else:
      self.layer.removeSelection() # Before can be had selected
      removeFeatures()
      self.legendCatalogLayer.enabledDownload( False )

    self.hasCriticalMessage = False

    populateLayer() # addFeatures().commitFeatures() -> QEventLoop()
    checkLayerLegend()
    self.enableRun.emit( True )

  @pyqtSlot(str)
  def layerWillBeRemoved(self, id):
    if not self.layerTree is None and id == self.layer.id():
      self.apiPL.kill()
      self.worker.kill()
      self.legendCatalogLayer.clean()
      self.layerTree = None

  @pyqtSlot()
  def settingImages(self):
    settings = self.downloadSettings if self.downloadSettings['isOk'] else None 
    dlg = DialogImageSettingPL( self.mainWindow, self.icon, settings )
    if dlg.exec_() == QDialog.Accepted:
      self.downloadSettings = dlg.getData()
      self.legendCatalogLayer.enabledDownload()

  @pyqtSlot()
  def downloadTMS(self):
    @pyqtSlot( dict )
    def finished( message ):
      numError =  message[ 'numError' ]
      msgDownload =  message[ 'msgDownload' ]
      
      self.thread.quit()
      self.worker.finished.disconnect( finished )
      self.enableRun.emit( True )
  
      if not self.mbpd.isCancel and self.worker.isKilled:
        self.msgBar.popWidget()
        msg = "Canceled by user"
        self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.CRITICAL, 8 )
        return
  
      self.legendCatalogLayer.enabledDownload()
      self._endDownload( numError, msgDownload )

    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog(ltgRoot)

    ( path, total, msgDownload, iterFeat ) = self._getInitDataDownload( "TMS" )
    if total == 0:
      msg = "Not images for download."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 )
      return

    cr3857 = QgsCoordinateReferenceSystem( 3857, QgsCoordinateReferenceSystem.EpsgCrsId )
    ctTMS = QgsCoordinateTransform( self.layer.crs(), cr3857 )
    self.mbpd = MessageBarProgressDownload( self.msgBar, "%s..." % msgDownload, total, self.worker.kill )
    msgDownload = msgDownload.replace( str( total ), 'Download_total' )
    
    self.worker.finished.connect( finished )
    self.worker.setting( path, ctTMS, iterFeat, ltgRoot, self.ltgCatalog, msgDownload )
    self.worker.stepProgress.connect( self.mbpd.step )
    self.thread.start() # Start Worker
    #self.worker.run() #DEBUGER

  @pyqtSlot()
  def downloadImages(self):
    def setFinished( response ):
      self.imageDownload.flush()
      self.imageDownload.close()

      if response[ 'isOk' ]:
        self.totalReady = response[ 'totalReady' ]
        fileName = self.imageDownload.fileName()
        self.imageDownload.rename( '.'.join( fileName.rsplit('.')[:-1] ) )
      else:
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

    ltgRoot = QgsProject.instance().layerTreeRoot()
    self._setGroupCatalog(ltgRoot)

    ( path, total, msgDownload, iter ) = self._getInitDataDownload( "images" )
    if total == 0:
      msg = "Not images for download."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 )
      return

    self.mbpd = MessageBarProgressDownload( self.msgBar, "%s..." % msgDownload, total, self.apiPL.kill, True )
    step = 1

    isVisual = self.downloadSettings['isVisual']
    suffix = u"visual" if isVisual else u"analytic"
    self.totalReady = None
    loop = QEventLoop()

    self.enableRun.emit( False )
    self.legendCatalogLayer.enabledDownload( False )
    numError = 0
    for feat in iter:
      image = os.path.join( path, u"%s_%s.tif" % ( feat['id'], suffix ) )
      self.mbpd.step( step, image )
      if self.mbpd.isCancel or self.layerTree is None :
        step -= 1
        iter.close()
        break
      if not QFile.exists( image ):
        self.imageDownload = QFile( "%s.part" % image )
        self.imageDownload.open( QIODevice.WriteOnly )
        json = feat['metadata_json']
        self.apiPL.saveImage( json, isVisual, setFinished, self.imageDownload.write, self.mbpd.stepFile )
        loop.exec_()
        if self.totalReady is None:
          numError += 1
      addImage()
      step += 1

    self.enableRun.emit( True )
    if self.layerTree is None:
      self.msgBar.popWidget()
      return

    self.legendCatalogLayer.enabledDownload()
    step -= 1
    msg = msgDownload.replace( str( total ), str ( step  ) ) 
    self._endDownload( numError, msg )

  @pyqtSlot()
  def downloadThumbnails(self):
    def setFinished( response ):
      if response[ 'isOk' ]:
        self.pixmap = response[ 'pixmap' ]
      else:
        self.pixmap = None
      loop.quit()

    ( path, total, msgDownload, iter ) = self._getInitDataDownload( "thumbnails" )
    if total == 0:
      msg = "Not images for download."
      self.msgBar.pushMessage( CatalogPL.pluginName, msg, QgsMessageBar.WARNING, 4 )
      return

    self.mbpd = MessageBarProgressDownload( self.msgBar, "%s..." % msgDownload, total, self.apiPL.kill )
    step = 1

    square = self.downloadSettings['isSquare']
    suffix = u"square_thumbnail" if square  else u"thumbnail"
    self.pixmap = None
    loop = QEventLoop()

    self.enableRun.emit( False )
    self.legendCatalogLayer.enabledDownload( False )
    commitFeats = []
    for feat in iter:
      thumbnail = os.path.join( path, u"%s_%s.png" % ( feat['id'], suffix ) )
      self.mbpd.step( step )
      commitItem = { 'fid': feat.id(), 'thumbnail': thumbnail, 'isOk': True }
      if self.mbpd.isCancel or self.layerTree is None :
        step -= 1
        break
      if not QFile.exists( thumbnail ):
        json = feat['metadata_json']
        self.apiPL.getThumbnail( json, square, setFinished )
        loop.exec_()
        if not self.pixmap is None:
          isOk = self.pixmap.save( thumbnail, "PNG")
          commitItem['isOk'] = isOk
          del self.pixmap
          self.pixmap = None
        else:
          commitItem['isOk'] = False

      commitFeats.append( commitItem )
      step += 1

    self.enableRun.emit( True )
    if self.layerTree is None:
      self.msgBar.popWidget()
      return
    else:
      self.legendCatalogLayer.enabledDownload()

    step -= 1
    numError = 0
    isEditable = self.layer.isEditable()
    if not isEditable:
      self.layer.startEditing()
    for item in commitFeats:
      if item['isOk']:
        isOk = self.layer.changeAttributeValue( item['fid'],  4, item['thumbnail'] )
        if not isOk:
          numError += 1
      else:
        numError += 1
    del commitFeats[:]
    self.layer.commitChanges()

    if isEditable:
      self.layer.startEditing()

    msg = msgDownload.replace( str( total ), str ( step  ) ) 
    self._endDownload( numError, msg )

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
