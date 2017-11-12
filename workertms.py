# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Worker TMS
Description          : Use to create TMS
Date                 : November, 2017
copyright            : (C) 2017 by Luiz Motta
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

from PyQt4 import QtCore

from qgis import core as QgsCore


class WorkerCreateTMS_GDAL_WMS(QtCore.QObject):
  finished = QtCore.pyqtSignal( dict )
  stepProgress = QtCore.pyqtSignal( int )

  def __init__(self, logMessage, legendRasterGeom):
    super(WorkerCreateTMS_GDAL_WMS, self).__init__()
    self.logMessage, self.legendRasterGeom = logMessage, legendRasterGeom
    self.ltgRoot = QgsCore.QgsProject.instance().layerTreeRoot()
    self.isKilled = None # set in run
    self.ltgCatalog = None # setting

  def setting(self, data):
   self.id_table = data['id_layer']
   self.path = data['path']
   self.ct = data['ctTMS'] # QgsCoordinateTransform
   self.iterFeat = data['iterFeat'] # feat['id'], feat['acquired'], feat['meta_json']
   self.ltgCatalog = data['ltgCatalog']
   self.pluginName = data['pluginName']
   key = 'user_pwd' # { 'user', 'pwd' }
   self.user_pwd = None if not data.has_key( key ) else data[ key ]
   key = 'rgb' # [ 'r', 'g', 'b' ]
   self.rgb  = None if not data.has_key( key ) else data[ key ]
   self.getURL = data['getURL']     # ( feat, self.rgb )

  @QtCore.pyqtSlot()
  def run(self):
    def saveTMS(feat, fileName):
      def contentTMS():
        def contenTargetWindow():
          r = self.ct.transform( feat.geometry().boundingBox() )
          targetWindow  = { 'ulX': r.xMinimum(), 'ulY': r.yMaximum(), 'lrX': r.xMaximum(), 'lrY': r.yMinimum() }
          l = [
            '  <TargetWindow>',
            '    <UpperLeftX>{}</UpperLeftX>',
            '    <UpperLeftY>{}</UpperLeftY>',
            '    <LowerRightX>{}</LowerRightX>',
            '    <LowerRightY>{}</LowerRightY>',
            '  </TargetWindow>'
          ]
          arg = ( targetWindow['ulX'], targetWindow['ulY'], targetWindow['lrX'], targetWindow['lrY'] )
          return '\n'.join(l).format( *arg )

        def getCacheName():
          dirname = os.path.dirname( fileName )
          name = os.path.splitext( os.path.basename( fileName ) )[0]
          name = "cache_{}".format( name ) 
          
        server_url = self.getURL( feat, self.rgb )
        # Change for GDAL_WMS
        for c in ['{z}', '{x}', '{y}']:
          server_url = server_url.replace( c, "${}".format( c ) )
        path, name = os.path.split(fileName)
        name = "cache_{}".format( os.path.splitext( name )[0] )
        cache_path = os.path.join( path, name )
        l = [
          "<GDAL_WMS>",
          "<!-- {} -->".format( self.pluginName ),
          '  <Service name="TMS">',
          "    <ServerUrl>{}</ServerUrl>".format( server_url ),
          "    <Transparent>TRUE</Transparent>",
          "    <SRS>EPSG:3857</SRS>",
          "    <ImageFormat>image/png</ImageFormat>",
          "  </Service>",
          "  <DataWindow>",
          "    <UpperLeftX>-20037508.34</UpperLeftX>",
          "    <UpperLeftY>20037508.34</UpperLeftY>",
          "    <LowerRightX>20037508.34</LowerRightX>",
          "    <LowerRightY>-20037508.34</LowerRightY>",
          "    <TileLevel>15</TileLevel>",
          "    <TileCountX>1</TileCountX>",
          "    <TileCountY>1</TileCountY>",
          "    <YOrigin>top</YOrigin>",
          "  </DataWindow>",
          "{}".format( contenTargetWindow() ),
          "  <Projection>EPSG:3857</Projection>",
          "  <BlockSizeX>256</BlockSizeX>",
          "  <BlockSizeY>256</BlockSizeY>",
          "  <BandsCount>4</BandsCount>",
          "  <DataType>byte</DataType>",
          "  <UserAgent>Mozilla/5.0</UserAgent>",
          "  <UnsafeSSL>true</UnsafeSSL>",
          "  <ZeroBlockHttpCodes>204,303,400,404,500,501</ZeroBlockHttpCodes>",
          "  <ZeroBlockOnServerException>true</ZeroBlockOnServerException>",
          "  <MaxConnections>5</MaxConnections>",
          "  <Cache>",
          "    <Path>{}</Path>".format( cache_path ),
          "  </Cache>",
          "</GDAL_WMS>"
        ]
        if not self.user_pwd is None:
          arg = ( self.user_pwd['user'], self.user_pwd['pwd'] )
          user_pwd = "  <UserPwd>{}:{}</UserPwd>".format( *arg )
          l.insert( len(l)-1, user_pwd )
        return '\n'.join( l )

      fileDownload = QtCore.QFile( fileName )
      fileDownload.open( QtCore.QIODevice.WriteOnly )
      fileDownload.write( contentTMS() )
      fileDownload.close()

    def addTMS():
      geomTransf = QgsCore.QgsGeometry(feat.geometry() )
      geomTransf.transform( self.ct )
      wkt_geom = geomTransf.exportToWkt()
      layer = QgsCore.QgsRasterLayer( image, os.path.split( image )[-1] )
      layer.setCustomProperty( 'wkt_geom', wkt_geom )
      layer.setCustomProperty( 'date', feat['acquired'] )
      layer.setCustomProperty( 'id_table', self.id_table )
      layer.setCustomProperty( 'id_image', feat['id'] )
      QgsCore.QgsMapLayerRegistry.instance().addMapLayer( layer, addToLegend=False )
      self.ltgCatalog.addLayer( layer).setVisible( QtCore.Qt.Unchecked )
      self.legendRasterGeom.setLayer( layer )

    mlr = QgsCore.QgsMapLayerRegistry.instance()
    self.isKilled = False
    formatImage = u"{}_tms.xml" 
    if not self.rgb is None:
      formatImage = u"{{}}_{}_tms.xml".format( '-'.join( self.rgb ) )
    step = totalError = 0
    for feat in self.iterFeat:
      step += 1
      self.stepProgress.emit( step )  
      if self.isKilled:
        self.iterFeat.close()
        break
      image = os.path.join( self.path, formatImage.format( feat['id'] ) )
      if not QtCore.QFile.exists( image ):
        saveTMS( feat, image )
      addTMS()

    message  = { 'totalError': totalError }
    self.finished.emit( message )

  def kill(self):
    self.isKilled = True


class WorkerCreateTMS_ServerXYZ(QtCore.QObject): # Obsolete, need changes!
  finished = QtCore.pyqtSignal( dict )
  stepProgress = QtCore.pyqtSignal( int )

  def __init__(self, logMessage, legendRasterGeom ):
    super(WorkerCreateTMS_ServerXYZ, self).__init__()
    self.logMessage, self.legendRasterGeom = logMessage, legendRasterGeom
    self.isKilled = None # set in run
    self.iterFeat = self.ltgRoot = self.ltgCatalog = self.msgDownload = None # setting

  def setting(self, iterFeat, ltgRoot, ltgCatalog):
   self.iterFeat, self.ltgRoot, self.ltgCatalog  = iterFeat, ltgRoot, ltgCatalog

  @QtCore.pyqtSlot()
  def run(self):
    def addTMS():
      server_url = API_PlanetLabs.urlTMS.format( item_type=item_type, item_id=item_id )
      urlkey = "{0}?api_key={1}".format( server_url, user_pwd )
      uri.setParam('url', urlkey )
      lyr = QgsCore.QgsRasterLayer( str( uri.encodedUri() ), item_id , 'wms')
      if not lyr.isValid():
        msg = "Error create TMS from {0}: Invalid layer".format( item_id )
        self.logMessage( msg, CatalogPL.pluginName, QgsCore.QgsMessageLog.CRITICAL )
        totalError += 1
        return
      if not lyr.source() in sources_catalog_group:
        lyr.setCustomProperty( 'wkt_geom', wkt_geom )
        mlr.addMapLayer( lyr, addToLegend=False )
        self.ltgCatalog.addLayer( lyr ).setVisible( QtCore.Qt.Unchecked )
        self.legendRasterGeom.setLayer( lyr )

    mlr = QgsCore.QgsMapLayerRegistry.instance()
    user_pwd = API_PlanetLabs.validKey
    uri = QgsCore.QgsDataSourceURI()
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
        self.logMessage( msg, CatalogPL.pluginName, QgsCore.QgsMessageLog.CRITICAL )
        totalError += 1
        continue
      wkt_geom = feat.geometry().exportToWkt()
      addTMS()
      uri.removeParam('url')

    message  = { 'totalError': totalError }
    self.finished.emit( message )

  def kill(self):
    self.isKilled = True
