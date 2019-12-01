# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Map Canvas Effects
Description          : Tools for show the geometry of feature
Date                 : January, 2019
copyright            : (C) 2019 by Luiz Motta
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

__author__ = 'Luiz Motta'
__date__ = '2019-01-31'
__copyright__ = '(C) 2019, Luiz Motta'
__revision__ = '$Format:%H$'

from qgis import utils as QgsUtils
from qgis.core import QgsProject, QgsCoordinateTransform


class  MapCanvasGeometry():
    def __init__(self):
        self.project = QgsProject().instance()
        self.canvas = QgsUtils.iface.mapCanvas()

    def flash(self, geometries, layer=None):
        if layer is None:
            self.canvas.flashGeometries( geometries )
        else:
            self.canvas.flashGeometries( geometries, layer.crs() )

    def zoom(self, geometries, layer=None):
        bbox = geometries[0].boundingBox()
        for geom in geometries[1:]:
            bbox.combineExtentWith( geom.boundingBox() )
        if not layer is None:
            crsLayer = layer.crs()
            crsCanvas = self.project.crs()
            if not crsLayer == crsCanvas:
                ct = QgsCoordinateTransform( layer.crs(), self.project.crs(), self.project )
                bbox = ct.transform( bbox )
        self.canvas.setExtent( bbox )
        self.canvas.zoomByFactor( 1.05 )
        self.canvas.refresh()
        self.flash( geometries, layer )
