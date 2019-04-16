#!/usr/bin/python3
# # -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Load Form
Description          : Script for populate From from UI file
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
from qgis.PyQt.QtWidgets import QLabel, QWidget, QDialogButtonBox

import qgis.utils as QgsUtils

def getFunctionPopulateForm(pluginName):
    """
    Function from Plugin for populate Form

    :param pluginName: Name of plugin
    """
    plugins = {}
    for name, obj in QgsUtils.plugins.items():
        plugins[ name ] = obj
    if not pluginName in plugins:
        return { 'isOk': False, 'message': "Missing {name} Plugin.".format(name=pluginName) }
    if plugins [pluginName ].dock is None:
        return { 'isOk': False, 'message': "Run the {name} Plugin.".format(name=pluginName) }
    return { 'isOk': True, 'function': plugins[ pluginName ].dock.pl.populateForm }

populateForm = None

def loadForm(dialog, layer, feature):
    global populateForm

    widgets = {
        'item_id': dialog.findChild( QLabel, 'item_id'),
        'date': dialog.findChild( QLabel, 'date'),
        'thumbnail': dialog.findChild( QLabel, 'thumbnail'),
        'tabMetadata': dialog.findChild( QWidget, 'tabMetadata'),
        'message_clip': dialog.findChild( QLabel, 'message_clip'),
        'message_status': dialog.findChild( QLabel, 'message_status')
    }
    if populateForm is None:
        r = getFunctionPopulateForm('catalogpl_plugin')
        if not r['isOk']:
            widgets['message_status'].setText( r['message'] )
            return
        populateForm = r['function']
    if feature.fieldNameIndex('item_id') == -1:
        return
    populateForm( widgets, feature )
