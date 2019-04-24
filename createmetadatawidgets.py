#!/usr/bin/python3
# # -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : TreeWidget Metadata
Description          : Create tree widget from metadata(json format)
                       for use in Form
Date                 : March, 2019
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
import os
from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis.PyQt.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QLabel
from qgis.core import QgsEditFormConfig

"""
form.ui and form.py:
    - The QWidget, 'tabMetadata' objectName, should have only a QLabel('lblClip') and with layout
"""
class TreeWidgetMetadata(object):
    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.messageHelp = "* Double click copy item to clipboard. Inside 'key' item = Expression, otherwise, value"

    def create(self, wgtTabMetadata, lblClip, name_exp_json, meta_json):
        """
        Create QTreeWidget and QLabel inside a Widget(with layout) for show metata(JSON).
        Used inside for Form

        :param wgtTabMetadata: QWidget
        :name_exp_json: Field's name of layer for expression
        :meta_json: Value of JSON(dictionary) from name_exp_json
        """
        def getExpression(keys):
            exp = "map_get( json_to_map( \"{name}\" ), '{key}' )".format( name=name_exp_json, key=keys[-1] )
            vStop = -1 * (1+len( keys ))
            for idx in range(-2, vStop, -1):
                exp = "map_get( {exp}, '{key}' )".format( exp=exp, key=keys[ idx ] )
            return exp

        def populate(treeWidget, jsonMetadataFeature):
            def fill_item(item, value):
                item.setExpanded( True )
                if not isinstance( value, ( dict, list ) ):
                    item.setData( 1, Qt.DisplayRole, value )
                    return
                if isinstance( value, dict ):
                    for key, val in value.items():
                        child = QTreeWidgetItem()
                        child.setText( 0, key )
                        item.addChild( child )
                        fill_item( child, val )
                    return
                if isinstance( value, list ):
                    for val in value:
                        if not isinstance( val, ( dict, list ) ):
                            item.setData( 1, Qt.DisplayRole, val )
                        else:
                            child = QTreeWidgetItem()
                            item.addChild( child )
                            text = '[dict]' if isinstance( value, dict ) else '[list]'
                            child.setText( 0, text )
                            fill_item( child , val )

                        child.setExpanded(True)
                        
            treeWidget.setColumnCount(2)
            item = treeWidget.invisibleRootItem()
            item.setDisabled( False )
            fill_item( item, jsonMetadataFeature )

        @pyqtSlot('QTreeWidgetItem*', int)
        def itemDoubleClicked(item, col):
            def addKey(item, keys):
                if item is None:
                    return
                keys.append( item.text(0) )
                addKey( item.parent(), keys )

            value = item.data( 1, Qt.DisplayRole )
            if value is None:
                msg = "Item need have Value"
                lblClip.setText( msg )
                lblClip.setStyleSheet('color: red')
                return
            if col == 0:
                keys = []
                addKey(item, keys)
                msg = getExpression( keys)
            else:
                msg = str( value )
            self.clipboard.setText( msg )
            msg = "Copied to clipboard: {msg}".format( msg=msg )
            lblClip.setText( msg )
            lblClip.setStyleSheet('color: blue')

        cols = 2
        tw = wgtTabMetadata.findChild( QTreeWidget, 'metadata')
        if tw is None:
            tw = QTreeWidget( wgtTabMetadata )
            tw.setAutoScroll(False)
            tw.setSelectionBehavior( tw.SelectItems )
            tw.setObjectName('metadata')
            header = tw.headerItem()
            header.setText(0, 'Key')
            header.setText(1, 'Value')
            tw.setColumnCount( cols )
            tw.itemDoubleClicked.connect( itemDoubleClicked )
            wgtTabMetadata.layout().addWidget( tw )
        else:
            tw.clear()
        populate( tw, meta_json )
        [ tw.resizeColumnToContents(c) for c in range(cols) ]

    @staticmethod
    def setForm(layer):
        config = QgsEditFormConfig()
        vfile = os.path.join( os.path.dirname( __file__ ), 'form.ui' )
        config.setUiForm( vfile)
        config.setInitCodeSource( QgsEditFormConfig.CodeSourceFile )
        config.setInitFunction('loadForm')
        vfile = os.path.join( os.path.dirname( __file__ ), 'form.py' )
        config.setInitFilePath( vfile)
        layer.setEditFormConfig(config)        
