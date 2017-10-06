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

from PyQt4.QtCore import ( QObject, QTimer, QFile, QIODevice, pyqtSlot )
from PyQt4.QtGui  import ( QAction, QColor )
from PyQt4.QtXml import QDomDocument

import qgis
from qgis.gui import ( QgsRubberBand, QgsHighlight ) 
from qgis.core import ( QGis, QgsMapLayer, QgsRectangle, QgsGeometry,
                        QgsCoordinateTransform, QgsCoordinateReferenceSystem )

class PolygonEffectsCanvas():
  def __init__(self):
    self.canvas = qgis.utils.iface.mapCanvas()
    self.crs = None #  setCRS if need
    self.color = QColor(255,0,0)

  def setCRS(self, crs):
    self.crs = crs

  def zoom(self, extent):
    extentTransform = extent 
    crsCanvas = self.canvas.mapSettings().destinationCrs()
    if not self.crs == crsCanvas:
      ct = QgsCoordinateTransform( self.crs, crsCanvas )
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
      ct = QgsCoordinateTransform( self.crs, crsCanvas )
      geomTransform.transform( ct )

    rb = QgsRubberBand( self.canvas, QGis.Polygon)
    rb.setBorderColor( self.color )
    rb.setWidth(2)
    rb.setToGeometry( geomTransform, None )
    QTimer.singleShot( seconds*1000, removeRB )

class LegendRaster(object):
  def __init__(self, labelMenu):
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
        }
      ]
      for item in self.legendLayer:
        item['action'] = QAction( item['menu'], None )
        item['action'].triggered.connect( item['slot'] )
        self.legendInterface.addLegendLayerAction( item['action'], labelMenu, item['id'], QgsMapLayer.RasterLayer, False )

    self.legendInterface = qgis.utils.iface.legendInterface()
    initLegendLayer() # Set self.legendLayer 
    self.polygonEC = PolygonEffectsCanvas()

  def __del__(self):
    for item in self.legendLayer:
      self.legendInterface.removeLegendLayerAction( item['action'] )

  def setLayer(self, layer):
    for item in self.legendLayer:
      self.legendInterface.addLegendLayerActionForLayer( item['action'],  layer )

  @pyqtSlot()
  def zoom(self):
    layer = self.legendInterface.currentLayer()
    extent = layer.extent()
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.zoom( extent )
    geom = QgsGeometry.fromRect( extent )
    self.polygonEC.highlight( geom )

  @pyqtSlot()
  def highlight(self):
    layer = self.legendInterface.currentLayer()
    geom = QgsGeometry.fromRect( layer.extent() )
    self.polygonEC.highlight( geom )

class LegendTMSXml(LegendRaster):
  def __init__(self, labelMenu):
     super(LegendRasterGeom, self).__init__( labelMenu )

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

    doc = QDomDocument()
    file = QFile( layer.source() )
    doc.setContent( file )
    file.close()

    tw = getTargetWindow()
    return QgsRectangle( tw['ulX'], tw['lrY'], tw['lrX'], tw['ulY'] )

  @pyqtSlot()
  def zoom(self):
    layer = self.legendInterface.currentLayer()
    extent = self._getExtent( layer )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.zoom( extent )
    geom = QgsGeometry.fromRect( extent )
    self.polygonEC.highlight( geom )

  @pyqtSlot()
  def highlight(self):
    layer = self.legendInterface.currentLayer()
    extent = self.self._getExtent( layer )
    geom = QgsGeometry.fromRect( extent )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.highlight( geom )

class LegendRasterGeom(LegendRaster):
  def __init__(self, labelMenu):
     super(LegendRasterGeom, self).__init__( labelMenu )

  def _getGeometry(self, layer):
    wkt_geom = layer.customProperty('wkt_geom')
    return QgsGeometry.fromWkt( wkt_geom )

  @pyqtSlot()
  def zoom(self):
    layer = self.legendInterface.currentLayer()
    geom = self._getGeometry( layer )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.zoom( geom.boundingBox() )
    self.polygonEC.highlight( geom )

  @pyqtSlot()
  def highlight(self):
    layer = self.legendInterface.currentLayer()
    geom = self._getGeometry( layer )
    self.polygonEC.setCRS( layer.crs() )
    self.polygonEC.highlight( geom )
