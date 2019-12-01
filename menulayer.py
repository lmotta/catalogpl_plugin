#!/usr/bin/python3
# # -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Menu Layer
Description          : Classes for add Menu in layer
Date                 : July, 2015, migrate to QGIS 3 at March, 2019
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

from qgis.PyQt.QtCore import QObject, pyqtSlot
from qgis.PyQt.QtWidgets import QApplication, QAction

from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsGeometry,
    QgsFeature, QgsFeatureRequest
)
import qgis.utils as QgsUtils

from .mapcanvaseffects import MapCanvasGeometry

class MenuCatalogPlanet(QObject):
    def __init__(self, menuName, funcActions):
        def initMenuLayer(menuName):
            self.menuLayer = [
            {
                'menu': u"Add XYZ tiles",
                'slot': self.addXYZtiles,
                'action': None
            },
            {
                'menu': u"Download images",
                'slot': self.downloadImages,
                'action': None
            }
            ]
            for item in self.menuLayer:
                item['action'] = QAction( item['menu'], None )
                item['action'].triggered.connect( item['slot'] )
                QgsUtils.iface.addCustomActionForLayerType( item['action'], menuName, QgsMapLayer.VectorLayer, False )

        super().__init__()
        initMenuLayer( menuName )
        self.funcActions = funcActions

    def __del__(self):
        for item in self.menuLayer:
            QgsUtils.iface.removeCustomActionForLayerType( item['action'] )

    def setLayer(self, layer):
        for item in self.menuLayer:
            QgsUtils.iface.addCustomActionForLayer( item['action'],  layer )

    @pyqtSlot(bool)
    def addXYZtiles(self, checked):
        self.funcActions['addXYZtiles']()

    @pyqtSlot(bool)
    def downloadImages(self, checked):
        self.funcActions['downloadImages']()


class MenuXYZTiles(QObject):
    def __init__(self, menuName):
        def initMenuLayer(menuName):
            self.menuLayer = [
            {
                'menu': u"Highlight",
                'slot': self.highlight,
                'action': None
            },
            {
                'menu': u"Zoom",
                'slot': self.zoom,
                'action': None
            },
            {
                'menu': u"Open form",
                'slot': self.openForm,
                'action': None
            },
            {
                'menu': u"Add to selection",
                'slot': self.addSelection,
                'action': None
            },
            ]
            for item in self.menuLayer:
                item['action'] = QAction( item['menu'], None )
                item['action'].triggered.connect( item['slot'] )
                QgsUtils.iface.addCustomActionForLayerType( item['action'], menuName, QgsMapLayer.RasterLayer, False )

        super().__init__()
        initMenuLayer( menuName )
        self.menuName = menuName
        self.msgBar = QgsUtils.iface.messageBar()
        self.canvasEffects = MapCanvasGeometry()
        self.project = QgsProject.instance()

    def __del__(self):
        for item in self.menuLayer:
            QgsUtils.iface.removeCustomActionForLayerType( item['action'] )

    def _getFeature(self):
        layer = QgsUtils.iface.activeLayer()
        table_id = layer.customProperty('layer_id')
        field_id = layer.customProperty('field_id')
        table = self.project.mapLayer( table_id )
        if table is None:
            msg = f"Layer used for create this image('{table_id}') not found."
            self.msgBar.pushWarning( self.menuName, msg )
            return None
        request = QgsFeatureRequest().setFlags( QgsFeatureRequest.NoGeometry)
        request = request.setSubsetOfAttributes( [ field_id['name'] ], table.fields() )
        expr = f"\"{field_id['name']}\" = '{field_id['value']}'"
        request = request.setFilterExpression( expr )
        it = table.getFeatures( request )
        feat = QgsFeature()
        if not it.nextFeature( feat ):
            msg = f"Image '{field_id['value']}' not found in '{table.name()}'."
            self.msgBar.pushWarning( self.menuName, msg )
            return None
        return {
            'table': table,
            'feature': feat
        }

    def setLayer(self, layer):
        for item in self.menuLayer:
            QgsUtils.iface.addCustomActionForLayer( item['action'],  layer )

    @pyqtSlot(bool)
    def zoom(self, checked):
        layer = QgsUtils.iface.activeLayer()
        wkt_geom = layer.customProperty('wkt_geom')
        geom = QgsGeometry.fromWkt( wkt_geom )
        self.canvasEffects.zoom( [ geom ], layer )

    @pyqtSlot(bool)
    def highlight(self, checked):
        layer = QgsUtils.iface.activeLayer()
        wkt_geom = layer.customProperty('wkt_geom')
        geom = QgsGeometry.fromWkt( wkt_geom )
        self.canvasEffects.flash( [ geom ], layer )

    @pyqtSlot(bool)
    def openForm(self, checked):
        r = self._getFeature()
        if r is None:
            return
        QgsUtils.iface.getFeatureForm( r['table'], r['feature'] ).show()

    @pyqtSlot(bool)
    def addSelection(self, checked):
        r = self._getFeature()
        if r is None:
            return
        r['table'].selectByIds( [ r['feature'].id() ], r['table'].AddToSelection )
