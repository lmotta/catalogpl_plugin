#!/usr/bin/python3
# # -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Qt API for Catalog Planet Labs 
Description          : API for Planet Labs
Date                 : May, 2015, March, 2019 migrate to Qt5
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

import json, datetime 

from qgis.PyQt.QtCore import (
    QObject,
    pyqtSignal, pyqtSlot,
    QUrl    
)
from qgis.PyQt.QtNetwork import QNetworkReply

from qgis.core import (
    QgsGeometry, QgsPointXY
)

from .accesssite import AccessSite

class API_PlanetLabs(QObject):
    validKey = None
    urlRoot = "https://api.planet.com"
    urlQuickSearch = "https://api.planet.com/data/v1/quick-search"
    urlYXZImage = "https://tiles.planet.com/data/v1/{item_type}/{item_id}/%7Bz%7D/%7Bx%7D/%7By%7D.png"
    urlYXZMosaicMonthly = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_{year}_{month:02d}_mosaic/gmap/%7Bz%7D/%7Bx%7D/%7By%7D.png"
    urlMetadata = "https://api.planet.com/data/v1/item-types/{item_type}/items/{item_id}"
    addFeature = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.access = AccessSite()
        self.fields = [ 'item_type', 'item_id', 'date', 'meta_json', 'meta_jsize' ]
        self.fieldsDef = {
            'item_type': 'string(15)',
            'item_id': 'string(25)',
            'date': 'string(15)',
            'meta_json': 'string(-1)',
            'meta_jsize': 'integer'
        }

    def _addFeaturesLinkResponse(self, response):
        def getFeaturesResponse(data):
            def getGeometry(geometry):
                def getPolygonPoints(coordinates):
                    polylines = []
                    for line in coordinates:
                        polyline = [ QgsPointXY( p[0], p[1] ) for p in line ]
                        polylines.append( polyline )
                    return polylines

                if geometry['type'] == 'Polygon':
                    polygon = getPolygonPoints( geometry['coordinates'] )
                    return QgsGeometry.fromMultiPolygonXY( [ polygon ] )
                elif geometry['type'] == 'MultiPolygon':
                    polygons= []
                    for polygon in geometry['coordinates']:
                        polygons.append( getPolygonPoints( polygon ) )
                    return QgsGeometry.fromMultiPolygonXY( polygons )

                else:
                    None

            def finished(response):
                self.responseAsset = response

            features = []
            for feat in data['features']:
                if self.access.isKill:
                    return features
                geom = getGeometry( feat['geometry'] )
                del feat['geometry']
                item_type = feat['properties']['item_type']
                del feat['properties']['item_type']
                item = {
                    'item_type': item_type,
                    'item_id': feat['id'],
                    'date': feat['properties']['acquired'].split('T')[0],
                    'properties': feat['properties'],
                    'geometry': geom
                }
                self.addFeature.emit( item['item_id'] )
                links = {}
                for k in ('assets', 'thumbnail'):
                    links[ k ] = feat['_links'][ k ]
                item['properties']['links'] = links
                self.responseAsset = None
                self.getAssetsStatus( links['assets'], finished )
                if self.responseAsset['isOk']:
                    item['properties']['assets_status'] = self.responseAsset['assets_status']
                features.append( item )
            return features

        if response['isOk']:
            data = self.access.loadJsonData( response )
            response['_links'] = {
                '_self': data['_links']['_self'],
                '_next': data['_links']['_next']
            }
            response['features'] = getFeaturesResponse( data )
            data.clear()
            if self.access.isKill:
                del response['features']
                response['isOk'] = False
                response['message'] = 'Canceled by user'

        return response

    def setKey(self, key, setFinished):
        def addFinishedResponse(response):
            if response['isOk']:
                API_PlanetLabs.validKey = key
            else:
                if response['errorCode'] == 204: # Host requires authentication
                    response['message'] = 'Invalid Key'
            return response

        p = {
            'url': QUrl( API_PlanetLabs.urlRoot ),
            'credential': { 'user': key, 'password': ''}
        }
        self.access.requestUrl( p, addFinishedResponse, setFinished )

    def getUrlScenesJson(self, json_request, setFinished):
        p = {
            'url': QUrl( API_PlanetLabs.urlQuickSearch ),
            'credential': { 'user': self.validKey, 'password': ''},
            'json_request': json_request
        }
        self.access.requestUrl( p, self._addFeaturesLinkResponse, setFinished )

    def getUrlScenesUrl(self, url, setFinished):
        p = {
            'url': QUrl( url ),
            'credential': { 'user': self.validKey, 'password': ''}
        }
        self.access.requestUrl( p, self._addFeaturesLinkResponse, setFinished )

    def getAssetsStatus(self, url, setFinished):
        def addFinishedResponse(response):
            def setStatus(response, data, asset):
                def getDateTimeFormat(d):
                    dt = datetime.datetime.strptime( d, "%Y-%m-%dT%H:%M:%S.%f")
                    return dt.strftime( formatDateTime )

                key = "a_{0}".format( asset )
                response['assets_status'][ key ] = {}
                r = response['assets_status'][ key ]
                if not asset in data:
                    r['status'] = "*None*"
                    return
                for k in ('status', 'location'):
                    if k in data[ asset ]:
                        r[ k ] = data[ asset ][ k ]
                if '_permissions' in data[ asset ]:
                    permissions = ",".join( data[ asset ]['_permissions'])
                    r['permissions'] = permissions
                if 'expires_at' in  data[ asset ]:
                    r['expires_at'] = getDateTimeFormat( data[ asset ]['expires_at'] )
                if '_links' in data[ asset ] and 'activate' in data[ asset ]['_links']:
                    r['activate'] = data[ asset ]['_links']['activate']

            if response['isOk']:
                formatDateTime = '%Y-%m-%d %H:%M:%S'
                date_time = datetime.datetime.now().strftime( formatDateTime )
                response['assets_status'] = {
                    '_date_calculate': date_time,
                }
                data = self.access.loadJsonData( response )
                setStatus(response, data, 'analytic')
                #setStatus(response, data, 'udm')
            return response

        p = {
            'url': QUrl( url ),
            'credential': { 'user': self.validKey, 'password': ''}
        }
        self.access.requestUrl( p, addFinishedResponse, setFinished )

    def requestUrl(self, url, setFinished):
        p = {
            'url': QUrl( url ),
            'credential': { 'user': self.validKey, 'password': ''}
        }
        self.access.requestUrl( p, lambda response: response, setFinished )

    def saveImage(self, url, setFinished, writePackageImage, progressPackageImage):
        p = {
            'url': QUrl( url ),
            'credential': { 'user': self.validKey, 'password': ''},
            'notResponseAllFinished': { 'writePackageImage': writePackageImage, 'progressPackageImage': progressPackageImage }
        }
        self.access.requestUrl( p, lambda response: response, setFinished )

    def isHostLive(self, setFinished):
        self.access.isHostLive( self.urlRoot, setFinished )

    def getThumbnail(self, url, setFinished):
        self.access.getThumbnail( url, setFinished )

    def getUrlMonthly(self, year, month, setFinished):
        def addFinishedResponse(response):
            if not response['isOk']:
                return response
            if 'data' in response:
                del response['data']
                response['url'] = self.urlYXZMosaicMonthly.format( year=year, month=month )
            return response

        url = self.urlYXZMosaicMonthly.format( year=year, month=month ).replace('%7Bz%7D/%7Bx%7D/%7By%7D','0/0/0')
        url = "{url}?api_key={key}".format( url=url, key=self.validKey )
        p = { 'url': QUrl( url ) }
        self.access.requestUrl( p, addFinishedResponse, setFinished )

    def checkValidKeyImage(self, item_type, item_id, setFinished):
        def addFinishedResponse(response):
            if response['isOk']:
                del response['data']
            elif response['errorCode'] == QNetworkReply.AuthenticationRequiredError:
                response['message'] = 'Insufficent credentials for this key'
                response['isOk'] = False
            else:
                response['isOk'] = True
            return response

        url = self.urlYXZImage.format( item_type=item_type, item_id=item_id ).replace('%7Bz%7D/%7Bx%7D/%7By%7D','0/0/0')
        url = "{url}?api_key={key}".format( url=url, key=self.validKey )
        p = { 'url': QUrl( url ) }
        self.access.requestUrl( p, addFinishedResponse, setFinished )

    @pyqtSlot()
    def kill(self):
        self.access.isKill = True
        self.access.abortReply.emit()
    
