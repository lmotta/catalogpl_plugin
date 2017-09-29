"""
/***************************************************************************
Name                 : PlanetLabs expressions
Description          : Set of expressions for QGIS ( 2.8 or above )
Date                 : April, 2015.
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

from qgis.core import ( qgsfunction )
from catalogpl_plugin import API_PlanetLabs

@qgsfunction(args=1, group='Planet Labs')
def getValueFromMetadata(values, feature, parent):
  """
  <h4>Return</h4>Get value of key of  'meta_json' field
  <p><h4>Syntax</h4>getValueFromMetadata('list_keys')</p>
  <p><h4>Argument</h4>list_keys -> String with a sequence of keys names - '"key1","key2",...'</p>
  <p><h4>Example</h4>getValueFromMetadata( '"item_type"' )</p><p>Return: Item type</p>
  """
  if values[0].count('"') % 2 != 0:
    raise Exception("Catalog Planet: Error! Key need double quotes: %s." % values[0] )
  
  if len( values[0] ) < 1:
    raise Exception("Catalog Planet: Error! Field is empty." )
    

  name_metadata_json = 'meta_json'
  id_metadata_json = feature.fieldNameIndex( name_metadata_json )
  if id_metadata_json == -1:
    raise Exception("Catalog Planet: Error! Need have '%s' field." % name_metadata_json )

  lstKey = map( lambda item: item.strip(), values[ 0 ].split(",") )
  lstKey = map( lambda item: item.strip('"'), lstKey )

  metadata_json = feature.attributes()[ id_metadata_json ] 
  try:
    ( success, valueKey) = API_PlanetLabs.getValue( metadata_json, lstKey )
    if not success:
      raise Exception( valueKey )
  except Exception as e:
    raise Exception( e.message )

  return valueKey

@qgsfunction(args=0, group='Planet Labs')
def getLocation(values, feature, parent):
  """
  <h4>Return</h4>Get value of location of  'meta_json' field
  <p><h4>Syntax</h4>getLocation()</p>
  <p><h4>Argument</h4>None</p>
  <p><h4>Example</h4>getLocation()</p><p>Return: Value of location</p>
  """

  name_metadata_json = 'meta_json'
  id_metadata_json = feature.fieldNameIndex( name_metadata_json )
  if id_metadata_json == -1:
    raise Exception("Catalog Planet: Error! Need have '%s' field." % name_metadata_json )

  metadata_json = feature.attributes()[ id_metadata_json ] 
  try:
    ( success, valueKey) = API_PlanetLabs.getValue( metadata_json, 'location' )
    if not success:
      return "'location' not found"
  except Exception as e:
    pass

  return valueKey
