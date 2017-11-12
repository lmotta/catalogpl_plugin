# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Legend Layer
Description          : Classes for add legend in layer
Date                 : July, 2015
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

from PyQt4 import QtCore, QtGui, QtXml

from qgis import core as QgsCore, gui as QgsGui, utils as QgsUtils


class PolygonEffectsCanvas():
  def __init__(self):
    self.canvas = QgsUtils.iface.mapCanvas()
    self.crs = None #  setCRS if need
    self.color = QtGui.QColor(255,0,0)

  def setCRS(self, crs):
    self.crs = crs

  def zoom(self, extent):
    extentTransform = extent 
    crsCanvas = self.canvas.mapSettings().destinationCrs()
    if not self.crs == crsCanvas:
      ct = QgsCore.QgsCoordinateTransform( self.crs, crsCanvas )
      extentTransform = ct.transform( extent )
    self.canvas.setExtent( extentTransform )
    self.canvas.zoomByFactor(1.05)
    self.canvas.refresh()
    
  def highlight(self, geom, seconds=2):
    def removeRB():
      rb.reset( True )
      self.canvas.scene().removeItem( rb )

    geomTransform = geom
    crsCanvas = self.canvas.mapSettings().destinationCrs()
    if not self.crs == crsCanvas:
      ct = QgsCore.QgsCoordinateTransform( self.crs, crsCanvas )
      geomTransform.transform( ct )

    rb = QgsGui.QgsRubberBand( self.canvas, QgsCore.QGis.Polygon)
    rb.setBorderColor( self.color )
    rb.setWidth(2)
    rb.setToGeometry( geomTransform, None )
    QtCore.QTimer.singleShot( seconds*1000, removeRB )

class LegendRaster(object):
  def __init__(self, pluginName):
    def initLegendLayer():
      self.legendLayer = [
        {
          'menu': u"Highlight",
          'id': "idHighlight",
          'slot': self.highlight,
          'action': None
        },
        {
          'menu': u"Zoom to",
          'id': "idZoom",
          'slot': self.zoom,
          'action': None
        },
        {
          'menu': u"Open form(table)",
          'id': "idForm",
          'slot': self.openForm,
          'action': None
        }
      ]
      for item in self.legendLayer:
        item['action'] = QtGui.QAction( item['menu'], None )
        item['action'].triggered.connect( item['slot'] )
        self.legendInterface.addLegendLayerAction( item['action'], self.pluginName, item['id'], QgsCore.QgsMapLayer.RasterLayer, False )

    self.pluginName = pluginName
    self.msgBar = QgsUtils.iface.messageBar()
    self.legendInterface = QgsUtils.iface.legendInterface()
    initLegendLayer() # Set self.legendLayer 
    self.polygonEC = PolygonEffectsCanvas()
    
  def __del__(self):
    for item in self.legendLayer:
      self.legendInterface.removeLegendLayerAction( item['action'] )

  def setLayer(self, layer):
    for item in self.legendLayer:
      self.legendInterface.addLegendLayerActionForLayer( item['action'],  layer )

  @QtCore.pyqtSlot()
  def zoom(self):
    layer = self.legendInterface.currentLayer()
    extent = layer.extent()
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.zoom( extent )
    geom = QgsCore.QgsGeometry.fromRect( extent )
    self.polygonEC.highlight( geom )

  @QtCore.pyqtSlot()
  def highlight(self):
    layer = self.legendInterface.currentLayer()
    geom = QgsCore.QgsGeometry.fromRect( layer.extent() )
    self.polygonEC.highlight( geom )

  @QtCore.pyqtSlot()
  def openForm(self):
    pass

class LegendTMSXml(LegendRaster):
  def __init__(self, pluginName):
     super(LegendRasterGeom, self).__init__( pluginName )

  def _getExtent(self, layer):
    def getTargetWindow():
      nodes = doc.elementsByTagName('TargetWindow')
      node = nodes.item( 0 )
      targetWindow = { 'ulX': None, 'ulY': None, 'lrX': None, 'lrY': None }
      labels = { 'UpperLeftX': 'ulX', 'UpperLeftY': 'ulY', 'LowerRightX': 'lrX', 'LowerRightY': 'lrY' }
      for key, value in labels.iteritems():
        text = node.firstChildElement( key ).text()
        if len( text ) == 0:
          continue
        targetWindow[ value ] = float( text )
      return targetWindow

    doc = QtXml.QDomDocument()
    file = QtCore.QFile( layer.source() )
    doc.setContent( file )
    file.close()

    tw = getTargetWindow()
    return QgsCore.QgsRectangle( tw['ulX'], tw['lrY'], tw['lrX'], tw['ulY'] )

  @QtCore.pyqtSlot()
  def zoom(self):
    layer = self.legendInterface.currentLayer()
    extent = self._getExtent( layer )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.zoom( extent )
    geom = QgsCore.QgsGeometry.fromRect( extent )
    self.polygonEC.highlight( geom )

  @QtCore.pyqtSlot()
  def highlight(self):
    layer = self.legendInterface.currentLayer()
    extent = self.self._getExtent( layer )
    geom = QgsCore.QgsGeometry.fromRect( extent )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.highlight( geom )

class LegendRasterGeom(LegendRaster):
  def __init__(self, pluginName):
     super(LegendRasterGeom, self).__init__( pluginName )

  def _getGeometry(self, layer):
    wkt_geom = layer.customProperty('wkt_geom')
    return QgsCore.QgsGeometry.fromWkt( wkt_geom )

  @QtCore.pyqtSlot()
  def zoom(self):
    layer = self.legendInterface.currentLayer()
    geom = self._getGeometry( layer )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.zoom( geom.boundingBox() )
    self.polygonEC.highlight( geom )

  @QtCore.pyqtSlot()
  def highlight(self):
    layer = self.legendInterface.currentLayer()
    geom = self._getGeometry( layer )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.highlight( geom )

  @QtCore.pyqtSlot()
  def openForm(self):
    layer = self.legendInterface.currentLayer()
    id_table = layer.customProperty('id_table')
    layers_table = [ l for l in self.legendInterface.layers() if id_table == l.id() ]
    if len( layers_table ) == 0:
      msg = "Layer used for create this image not found."
      arg = ( self.pluginName, msg, QgsGui.QgsMessageBar.WARNING, 4 ) 
      self.msgBar.pushMessage( *arg )
      return
    table = layers_table[0]
    id_image = layer.customProperty('id_image')
    request = QgsCore.QgsFeatureRequest().setFilterExpression( u'"id" = \'{0}\''.format( id_image ) )
    request.setFlags( QgsCore.QgsFeatureRequest.NoGeometry )
    feats = [ f for f in table.getFeatures(request) ]
    if len( feats ) == 0:
      msg = "Image '{}' not found in '{}'.".format( id_image, table.name() )
      arg = ( self.pluginName, msg, QgsGui.QgsMessageBar.WARNING, 4 ) 
      self.msgBar.pushMessage( *arg )
      return
    form = QgsUtils.iface.getFeatureForm( table, feats[0] )
    form.show()
