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
from qgis.gui import ( QgsRubberBand ) 
from qgis.core import ( QGis, QgsMapLayer, QgsRectangle, QgsGeometry, QgsCoordinateTransform, QgsCoordinateReferenceSystem )

class LegendRaster(object):

  def __init__(self, parentMenu):
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
        self.legendInterface.addLegendLayerAction( item['action'], parentMenu, item['id'], QgsMapLayer.RasterLayer, False )

    self.legendInterface = qgis.utils.iface.legendInterface()
    self.legendLayer =  None
    initLegendLayer()

  def __del__(self):
    for item in self.legendLayer:
      self.legendInterface.removeLegendLayerAction( item['action'] )

  def setLayer(self, layer):
    for item in self.legendLayer:
      self.legendInterface.addLegendLayerActionForLayer( item['action'],  layer )

  def _getExtent(self, canvas, layer):
    crsCanvas = canvas.mapSettings().destinationCrs()
    crsLayer = layer.crs()
    ctCanvas = QgsCoordinateTransform( crsLayer, crsCanvas )
    return ctCanvas.transform( layer.extent() )

  def _highlight(self, canvas, extent ):
    def removeRB():
      rb.reset( True )
      canvas.scene().removeItem( rb )
    
    rb = QgsRubberBand( canvas, QGis.Polygon)
    rb.setBorderColor( QColor( 255,  0, 0 ) )
    rb.setWidth( 2 )
    rb.setToGeometry( QgsGeometry.fromRect( extent ), None )
    QTimer.singleShot( 2000, removeRB )

  @pyqtSlot()
  def highlight(self):
    canvas = qgis.utils.iface.mapCanvas()
    layer = self.legendInterface.currentLayer()
    extent = self._getExtent( canvas, layer )
    self._highlight( canvas, extent )

  @pyqtSlot()
  def zoom(self):
    canvas = qgis.utils.iface.mapCanvas()
    layer = self.legendInterface.currentLayer()
    extent = self._getExtent( canvas, layer )
    canvas.setExtent( extent )
    canvas.zoomByFactor( 1.05 )
    canvas.refresh()
    self._highlight( canvas, extent )


class LegendTMS(LegendRaster):

  def __init__(self, parentMenu):
     super(LegendTMS, self).__init__( parentMenu )

  def _getFile(self, layer):
    doc = QDomDocument()
    file = QFile( layer.source() )
    return None if not file.open( QIODevice.ReadOnly ) else file

  def hasTargetWindows(self, layer ):
    file = self._getFile( layer )
    if file is None:
     return False

    doc = QDomDocument()
    doc.setContent( file )
    file.close()

    nodes = doc.elementsByTagName( 'TargetWindow' )
    return True if nodes.count() > 0 else False

  def _getExtent(self, canvas, layer):
    def getTargetWindows():
      file = self._getFile( layer )
      if file is None:
        return None

      doc = QDomDocument()
      doc.setContent( file )
      file.close()

      nodes = doc.elementsByTagName( 'TargetWindow' )
      if nodes.count == 0:
        return None

      node = nodes.item( 0 )
      targetWindow = { 'ulX': None, 'ulY': None, 'lrX': None, 'lrY': None }
      labels = { 'UpperLeftX': 'ulX', 'UpperLeftY': 'ulY', 'LowerRightX': 'lrX', 'LowerRightY': 'lrY' }
      for key, value in labels.iteritems():
        text = node.firstChildElement( key ).text()
        if len( text ) == 0:
          continue
        targetWindow[ value ] = float( text )

      if None in targetWindow.values():
        return None

      return targetWindow

    crsCanvas = canvas.mapSettings().destinationCrs()
    crsLayer = layer.crs()
    ctCanvas = QgsCoordinateTransform( crsLayer, crsCanvas )
    tw = getTargetWindows()
    rect =  QgsRectangle( tw['ulX'], tw['lrY'], tw['lrX'], tw['ulY'] )
    return ctCanvas.transform( rect )
