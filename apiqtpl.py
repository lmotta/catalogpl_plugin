# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Qt API for Catalog Planet Labs 
Description          : API for Planet Labs
Date                 : May, 2015
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

from PyQt4.QtCore import ( Qt, QObject, QByteArray, QUrl, pyqtSignal, pyqtSlot )
from PyQt4.QtNetwork import ( QNetworkAccessManager, QNetworkRequest, QNetworkReply )
from PyQt4.QtGui import( QPixmap )
import json

class AccessSite(QObject):

  # Signals
  finished = pyqtSignal( dict)
  send_data = pyqtSignal(QByteArray)
  status_download = pyqtSignal(int, int)
  status_erros = pyqtSignal(list)
  
  ErrorCodeAttribute = { 
     10: 'Canceled request',
    400: 'Bad request syntax',
    401: 'Unauthorized',
    402: 'Payment required',
    403: 'Forbidden',
    404: 'Not found',
    500: 'Internal error',
    501: 'Not implemented',
    502: 'Bad Gateway'  
  }

  def __init__(self):
    super( AccessSite, self ).__init__()
    self.networkAccess = QNetworkAccessManager( self )
    self.totalReady = self.reply = self.triedAuthentication = self.isKilled = None
    # Input by self.run
    self.key = self.responseAllFinished = None

  def run(self, url, key='', responseAllFinished=False):
    ( self.key, self.responseAllFinished ) = ( key, responseAllFinished )
    self._connect()
    self.totalReady = 0
    self.isKilled = False
    request = QNetworkRequest( url )
    reply = self.networkAccess.get( request )
    if reply is None:
      response = { 'isOk': False, 'message': "Network error", 'errorCode': -1 }
      self._connect( False )
      self.finished.emit( response )
      return

    self.triedAuthentication = False
    self.reply = reply
    self._connectReply()
  
  def kill(self):
    self.isKilled = True
  
  def isRunning(self):
    return ( not self.reply is None and self.reply.isRunning() )  

  def _connect(self, isConnect=True):
    ss = [
      { 'signal': self.networkAccess.finished, 'slot': self.replyFinished },
      { 'signal': self.networkAccess.authenticationRequired, 'slot': self.authenticationRequired }
    ]
    if isConnect:
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def _connectReply(self, isConnect=True):
    ss = [
      { 'signal': self.reply.readyRead, 'slot': self.readyRead },
      { 'signal': self.reply.downloadProgress, 'slot': self.downloadProgress },
      { 'signal': self.reply.sslErrors, 'slot': self.sslErrors }
    ]
    if isConnect:
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def _clearConnect(self):
    self._connect( False ) # self.reply.close() -> emit signal self.networkAccess.finished
    self._connectReply( False )
    self.reply.close()
    self.reply.deleteLater();
    del self.reply
    self.reply = None

  def _redirectionReply(self, url):
    self._clearConnect()
    self._connect()
    if url.isRelative():
      url = url.resolved( url )

    request = QNetworkRequest( url )
    reply = self.networkAccess.get( request )
    if reply is None:
      response = { 'isOk': False, 'message': "Netwok error", 'errorCode': -1 }
      self._connect( False )
      self.finished.emit( response )
      return

    self.reply = reply
    self._connectReply()
    
  def _errorCodeAttribute(self, code):
    msg = 'Error network' if not code in self.ErrorCodeAttribute.keys() else AccessSite.ErrorCodeAttribute[ code ]
    response = { 'isOk': False, 'message': msg, 'errorCode': code }
    self._clearConnect()
    self.finished.emit( response )

  @pyqtSlot('QNetworkReply')
  def replyFinished(self, reply) :
    if self.isKilled:
      self._errorCodeAttribute(10)

    if reply.error() != QNetworkReply.NoError :
      response = { 'isOk': False, 'message': reply.errorString(), 'errorCode': reply.error() }
      self._clearConnect()
      self.finished.emit( response )
      return

    urlRedir = reply.attribute( QNetworkRequest.RedirectionTargetAttribute )
    if not urlRedir is None and urlRedir != reply.url():
      self._redirectionReply( urlRedir )
      return

    codeAttribute = reply.attribute( QNetworkRequest.HttpStatusCodeAttribute )
    if codeAttribute != 200:
      self._errorCodeAttribute( codeAttribute )
      return

    statusRequest = {
      'contentTypeHeader': reply.header( QNetworkRequest.ContentTypeHeader ),
      'lastModifiedHeader': reply.header( QNetworkRequest.LastModifiedHeader ),
      'contentLengthHeader': reply.header( QNetworkRequest.ContentLengthHeader ),
      'statusCodeAttribute': reply.attribute( QNetworkRequest.HttpStatusCodeAttribute ),
      'reasonPhraseAttribute': reply.attribute( QNetworkRequest.HttpReasonPhraseAttribute )
    }
    response = { 'isOk': True, 'statusRequest': statusRequest }
    if self.responseAllFinished:
      response[ 'data' ] = reply.readAll()
    else:
      response[ 'totalReady' ] = self.totalReady

    self._clearConnect()
    self.finished.emit( response )

  @pyqtSlot('QNetworkReply', 'QAuthenticator')
  def authenticationRequired (self, reply, authenticator):
    if not self.triedAuthentication: 
      authenticator.setUser( self.key )
      authenticator.setPassword ('')
      self.triedAuthentication = True
    else:
      self._errorCodeAttribute( 401 )

  @pyqtSlot()
  def readyRead(self):
    if self.isKilled:
      self._errorCodeAttribute(10)
      return

    if self.responseAllFinished:
      return

    urlRedir = self.reply.attribute( QNetworkRequest.RedirectionTargetAttribute )
    if not urlRedir is None and urlRedir != self.reply.url():
      self._redirectionReply( urlRedir )
      return

    codeAttribute = self.reply.attribute( QNetworkRequest.HttpStatusCodeAttribute )
    if codeAttribute != 200:
      self._errorCodeAttribute( codeAttribute )
      return

    data = self.reply.readAll()
    if data is None:
      return
    self.totalReady += len ( data )
    self.send_data.emit( data )

  @pyqtSlot(int, int)
  def downloadProgress(self, bytesReceived, bytesTotal):
    if self.isKilled:
      self._errorCodeAttribute(10)
    else:
      self.status_download.emit( bytesReceived, bytesTotal )

  @pyqtSlot( list )
  def sslErrors(self, errors):
    lstErros = map( lambda e: e.errorString(), errors )
    self.status_erros.emit( lstErros )
    self.reply.ignoreSslErrors()


class API_PlanetLabs(QObject):

  urlRoot = "https://api.planet.com/"
  urlScenesOrtho = "https://api.planet.com/v0/scenes/ortho/"
  validKey = None

  def __init__(self):
    super( API_PlanetLabs, self ).__init__()
    self.access = AccessSite()

  def kill(self):
    self.access.kill()

  def isRunning(self):
    return self.access.isRunning()

  def isHostLive(self, setFinished):
    @pyqtSlot(dict)
    def finished( response):
      self.access.finished.disconnect( finished )
      if response['isOk']:
        response[ 'isHostLive' ] = True

        response[ 'data' ].clear()
        del response[ 'data' ]
        del response[ 'statusRequest' ]
      else:
        if response['errorCode'] == QNetworkReply.HostNotFoundError:
          response[ 'isHostLive' ] = False
          response[ 'message' ] += "\nURL = %s" % API_PlanetLabs.urlRoot
        else:
          response[ 'isHostLive' ] = True

      setFinished( response )

    url = QUrl( API_PlanetLabs.urlRoot )
    self.access.finished.connect( finished )
    self.access.run( url, '', True ) # Send all data in finished

  def setKey(self, key, setFinished):
    @pyqtSlot(dict)
    def finished( response):
      self.access.finished.disconnect( finished )
      if response['isOk']:
        API_PlanetLabs.validKey = key

        response[ 'data' ].clear()
        del response[ 'data' ]
        del response[ 'statusRequest' ]

      setFinished( response )

    url = QUrl( API_PlanetLabs.urlRoot )
    self.access.finished.connect( finished )
    self.access.run( url, key, True ) # Send all data in finished

  def getTotalScenesOrtho(self, url, setFinished):
    @pyqtSlot(dict)
    def finished( response):
      self.access.finished.disconnect( finished )
      if response[ 'isOk' ]:
        data = json.loads( str( response[ 'data' ] ) )
        response[ 'total' ] = data[ 'count' ]

        data.clear()
        response[ 'data' ].clear()
        del response[ 'data' ]
        del response[ 'statusRequest' ]

      setFinished( response )

    url = QUrl.fromEncoded( url )
    self.access.finished.connect( finished )
    self.access.run( url, API_PlanetLabs.validKey, True )

  def getScenesOrtho(self, url, setFinished):
    @pyqtSlot(dict)
    def finished( response):
      self.access.finished.disconnect( finished )
      if response[ 'isOk' ]:
        data = json.loads( str( response[ 'data' ] ) )
        response[ 'url' ] = data[ 'links' ][ 'next' ]
        response[ 'scenes' ] = data[ 'features' ]

        response[ 'data' ].clear()
        del response[ 'data' ]
        del response[ 'statusRequest' ]

      setFinished( response )

    url = QUrl.fromEncoded( url )
    self.access.finished.connect( finished )
    self.access.run( url, API_PlanetLabs.validKey, True )

  def getThumbnail(self, jsonMetadataFeature, square, setFinished):
    @pyqtSlot(dict)
    def finished( response ):
      self.access.finished.disconnect( finished )
      if response['isOk']:
        pixmap = QPixmap()
        pixmap.loadFromData( response[ 'data' ] )
        response[ 'pixmap' ] = pixmap

        response[ 'data' ].clear()
        del response[ 'data' ]
        del response[ 'statusRequest' ]

      setFinished( response )

    keyThumbnail = 'square_thumbnail' if square else 'thumbnail'
    ( ok, url ) = API_PlanetLabs.getValue( jsonMetadataFeature, [ 'links', keyThumbnail ] )
    if not ok:
      response = { 'isOk': False, 'message': url }
      setFinished( response )
    else:
      url = QUrl( url )
      self.access.finished.connect( finished )
      self.access.run( url, API_PlanetLabs.validKey, True )

  def saveImage(self, jsonMetadataFeature, isVisual, setFinished, setSave, setProgress):
    @pyqtSlot(dict)
    def finished( response ):
      self.access.finished.disconnect( finished )
      if response['isOk']:
        del response[ 'statusRequest' ]
      setFinished( response ) # response[ 'totalReady' ]
      
    keyVisual = 'visual' if isVisual else 'analytic'
    keys = [ 'data', 'products', keyVisual, 'full' ]
    ( ok, url ) = API_PlanetLabs.getValue( jsonMetadataFeature, keys )
    if not ok:
      response = { 'isOk': False, 'message': url }
      setFinished( response )
    else:
      url = QUrl( url )
      self.access.finished.connect( finished )
      self.access.send_data.connect( setSave )
      self.access.status_download.connect( setProgress )
      self.access.run( url, API_PlanetLabs.validKey, False )

  def saveTMS(self, fid, path, targetWindow, jsonMetadataFeature, setFinished, setSave):
    def contenTargetWindow():
      return '<TargetWindow>\n'\
             '  <UpperLeftX>%f</UpperLeftX>\n'\
             '  <UpperLeftY>%f</UpperLeftY>\n'\
             '  <LowerRightX>%f</LowerRightX>\n'\
             '  <LowerRightY>%f</LowerRightY>\n'\
             '</TargetWindow>\n' % (
               targetWindow['ulX'], targetWindow['ulY'], targetWindow['lrX'], targetWindow['lrY'] )

    def contentTMS():
      return '<GDAL_WMS>\n'\
             '<!-- Planet Labs -->\n'\
             '<Service name="TMS">\n'\
             '<ServerUrl>%s</ServerUrl>\n'\
             '<Transparent>TRUE</Transparent>\n'\
             '</Service>\n'\
             '<DataWindow>\n'\
             '<UpperLeftX>-20037508.34</UpperLeftX>\n'\
             '<UpperLeftY>20037508.34</UpperLeftY>\n'\
             '<LowerRightX>20037508.34</LowerRightX>\n'\
             '<LowerRightY>-20037508.34</LowerRightY>\n'\
             '<TileLevel>15</TileLevel>\n'\
             '<TileCountX>1</TileCountX>\n'\
             '<TileCountY>1</TileCountY>\n'\
             '<YOrigin>top</YOrigin>\n'\
             '</DataWindow>\n'\
             '%s'\
             '<Projection>EPSG:3857</Projection>\n'\
             '<BlockSizeX>256</BlockSizeX>\n'\
             '<BlockSizeY>256</BlockSizeY>\n'\
             '<BandsCount>4</BandsCount>\n'\
             '<DataType>byte</DataType>\n'\
             '<ZeroBlockHttpCodes>204,303,400,404,500,501</ZeroBlockHttpCodes>\n'\
             '<ZeroBlockOnServerException>true</ZeroBlockOnServerException>\n'\
             '<MaxConnections>5</MaxConnections>\n'\
             '<UserPwd>%s</UserPwd>\n'\
             '<Cache>\n'\
            '<Path>%s</Path>\n'\
             '</Cache>\n'\
             '</GDAL_WMS>\n' % ( server_url, target_window, user_pwd, cache_path )

    keys = [ 'links', 'self' ]
    ( ok, url ) = API_PlanetLabs.getValue( jsonMetadataFeature, keys )
    if not ok:
      setFinished( { 'isOk': False, 'totalReady': 0 } )
    else:
      server_url = "%s/${z}/${x}/${y}.png" % url.replace( "https://api", "https://tiles")
      user_pwd = API_PlanetLabs.validKey
      cache_path = "%s/cache_pl_%s.tms" % ( path, fid )
      target_window = contenTargetWindow()
      content_tms = contentTMS() 
      setSave( content_tms )
      setFinished( { 'isOk': True, 'totalReady': 1 } )

  @staticmethod
  def getUrlFilterScenesOrtho(filters):
    items = []
    for item in filters.iteritems():
      skey = str( item[0] )
      svalue = str( item[1] )
      items.append( ( skey, svalue ) )

    url = QUrl( API_PlanetLabs.urlScenesOrtho )
    url.setQueryItems( items )

    return url.toEncoded()

  @staticmethod
  def getJsonByObjectPy( objPy ):
    return json.dumps( objPy )

  @staticmethod
  def getValue(jsonMetadataFeature, keys):
    dicMetadata = json.loads( jsonMetadataFeature )
    msgError = None
    e_keys = map( lambda item: "'%s'" % item, keys )
    try:
      value = reduce( lambda d, k: d[ k ], [ dicMetadata ] + keys )
    except KeyError as e:
      msgError = "Have invalid key: %s" % ' -> '.join( e_keys)
    except TypeError as e:
      msgError = "The last key is invalid: %s" % ' -> '.join( e_keys)

    if msgError is None and isinstance( value, dict):
      msgError = "Missing key: %s" % ' -> '.join( e_keys)

    return ( True, value ) if msgError is None else ( False, msgError ) 

  @staticmethod
  def getTextTreeMetadata( jsonMetadataFeature ):
    def fill_item(strLevel, value):
      if not isinstance( value, ( dict, list ) ):
        items[-1] += ": %s" % value
        return

      if isinstance( value, dict ):
        for key, val in sorted( value.iteritems() ):
          items.append( "%s%s" % ( strLevel, key ) )
          strLevel += signalLevel
          fill_item( strLevel, val )
          strLevel = strLevel[ : -1 * len( signalLevel ) ]
      return

      if isinstance( value, list ):
        for val in value:
          if not isinstance( value, ( dict, list ) ):
            items[-1] += ": %s" % value
          else:
            text = '[dict]' if isinstance( value, dict ) else '[list]'
            items.append( "%s%s" % ( strLevel, text ) )
            strLevel += signalLevel
            fill_item( strLevel, val )
            strLevel = strLevel[ : -1 * len( signalLevel ) ]

    signalLevel = "- "
    items = []
    fill_item( '', json.loads( jsonMetadataFeature ) )
    
    return '\n'.join( items )

  @staticmethod
  def getTextValuesMetadata( dicMetadataFeature ):
    def fill_item(value):
      def addValue(_value):
        _text = "'%s' = %s" % (", ".join( keys ),  _value )
        items.append( _text )

      if not isinstance( value, ( dict, list ) ):
        addValue( value )
        return

      if isinstance( value, dict ):
        for key, val in sorted( value.iteritems() ):
          keys.append( '"%s"' % key )
          fill_item( val )
          del keys[ -1 ]
      return

      if isinstance( value, list ):
        for val in value:
          if not isinstance( val, ( dict, list ) ):
            addValue( val )
          else:
            text = "[dict]" if isinstance( val, dict ) else "[list]"
            keys.append( '"%s"' % text )
            fill_item( val )
            del keys[ -1 ]

    keys = []
    items = []
    fill_item( dicMetadataFeature )
    
    return '\n'.join( items )

  @staticmethod
  def getQTreeWidgetMetadata( jsonMetadataFeature, parent=None ):
    def createTreeWidget():
      tw = QTreeWidget(parent)
      tw.setColumnCount( 2 )
      tw.header().hide()
      tw.clear()
      return tw
 
    def fill_item(item, value):
      item.setExpanded( True )
      if not isinstance( value, ( dict, list ) ):
        item.setData( 1, Qt.DisplayRole, value )
        return

      if isinstance( value, dict ):
        for key, val in sorted( value.iteritems() ):
          child = QTreeWidgetItem()
          child.setText( 0, unicode(key) )
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

    tw = createTreeWidget()
    fill_item( tw.invisibleRootItem(), json.loads( jsonMetadataFeature ) )
    tw.resizeColumnToContents( 0 )
    tw.resizeColumnToContents( 1 )
    
    return tw
