#!/usr/bin/python3
# # -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Planet Labs 
Description          : Class for work with Planet Labs
Date                 : March, 2019 migrate to Qt5
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
import json, os

from qgis.PyQt.QtCore import (
    QObject, Qt,
    QSettings,
    QDate, QDateTime, QTime,
    QDir, QFile, QFileInfo, QIODevice,
    pyqtSlot, pyqtSignal
)
from qgis.PyQt.QtWidgets import (
  QApplication,
  QStyle,
  QWidget, QDockWidget, QTabWidget,
  QGroupBox, QHBoxLayout, QVBoxLayout,
  QLabel, QPushButton, QLineEdit,
  QRadioButton, QCheckBox, QSpinBox,
  QDateEdit,
  QSpacerItem, QSizePolicy,
  QFileDialog, QDialog
)
from qgis.PyQt.QtNetwork import QNetworkReply

from qgis.core import (
    Qgis, QgsProject,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFeatureRequest,
    QgsVectorLayer, QgsRasterLayer, QgsMapLayer,
    QgsFeature, QgsGeometry,
    QgsMessageLog
)
from qgis.gui import QgsMessageBar

from .apipl import API_PlanetLabs
from .mapcanvaseffects import MapCanvasGeometry
from .menulayer import MenuXYZTiles, MenuCatalogPlanet
from .createmetadatawidgets import TreeWidgetMetadata
from .widgetprogressbar import WidgetProgressBar


class DockWidgetPlanetLabs(QDockWidget):
    buttonSearchImageClicked = pyqtSignal(str, QDate, QDate)
    buttonAddMosaicsClicked = pyqtSignal(QDate, QDate)
    buttonLoginClicked = pyqtSignal(str, bool)
    buttonKeyClicked = pyqtSignal(str)
    cancelProcess = pyqtSignal()
    changeButtonCancel = pyqtSignal(QPushButton)
    def __init__(self, iface):
        def getIconApplyCancelDir():
            fIcon = self.style().standardIcon
            return (
                fIcon( QStyle.SP_DialogApplyButton ),
                fIcon( QStyle.SP_DialogCancelButton ),
                fIcon( QStyle.SP_DirIcon )
            )

        def setupUi():
            def createRadioButton(name, layout, parent):
                w = QRadioButton( name, parent )
                w.setObjectName( "obj{}".format( name) )
                layout.addWidget( w )

            def createDateEdit(name, objectName, layout, displayFormat, hasCalendar, parent):
                layout.addWidget( QLabel( name ) )
                w = QDateEdit( parent )
                w.setObjectName( objectName )
                w.setCalendarPopup( True )
                w.setDisplayFormat( displayFormat )
                w.setCalendarPopup( hasCalendar )
                layout.addWidget( w )

            def getPageImage(wgtMain):
                wgtPage = QWidget( wgtMain )
                wgtPage.setObjectName('objPageImage')
                lytPage = QHBoxLayout()

                lytAssets = QHBoxLayout()
                for name in sorted(self.nameAssets.keys() ):
                    createRadioButton( name, lytAssets, wgtPage )
                lytPage.addLayout( lytAssets )

                w = QPushButton( self.titleSelectDirectory, wgtPage)
                w.setIcon( iconDir )
                w.setObjectName('objPath')
                w.setToolTip( self.titleSelectDirectory )
                lytPage.addWidget( w )

                lytDates = QHBoxLayout()
                for name in ('From', 'To'):
                    objectName = "obj{}Image".format( name) 
                    createDateEdit( name, objectName, lytDates, 'yyyy-MM-dd', True, wgtPage )
                lytPage.addLayout( lytDates )

                w = QSpinBox( wgtPage )
                w.setObjectName('objDays')
                w.setSingleStep( 1 )
                w.setSuffix(' Days')
                w.setRange( 1, 360000 )
                lytPage.addWidget( w )

                self.btnSearchImage = QPushButton('Search', wgtPage )
                self.btnSearchImage.setIcon( self.iconApply )
                lytPage.addWidget( self.btnSearchImage )

                w = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
                lytPage.addItem( w )

                wgtPage.setLayout( lytPage )
                return wgtPage

            def getPageMosaic(wgtMain):
                wgtPage = QWidget( wgtMain )
                wgtPage.setObjectName('objPageMosaic')
                lytPage = QHBoxLayout()

                lyt = QHBoxLayout()
                for name in ('From', 'To'):
                    objectName = "obj{}Mosaic".format( name) 
                    createDateEdit( name, objectName, lyt, 'yyyy-MM', False, wgtPage )
                lytPage.addLayout( lyt )

                w = QSpinBox( wgtPage )
                w.setObjectName('objMonths')
                w.setSingleStep( 1 )
                w.setSuffix(' Month')
                w.setRange( 1, 12000 )
                lytPage.addWidget( w )

                self.btnMosaic = QPushButton('Add', wgtPage ) # More words add &
                self.btnMosaic.setIcon( self.iconApply )
                lytPage.addWidget( self.btnMosaic )

                w = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
                lytPage.addItem( w )

                wgtPage.setLayout( lytPage )
                return wgtPage

            def getPageKey(wgtMain):
                wgtPage = QWidget( wgtMain )
                wgtPage.setObjectName('objPageKey')
                lytPage = QHBoxLayout()

                # SEE object names in: self.pageKey 
                
                # Layout Password
                lyt = QHBoxLayout()
                w = QLabel("Key:")
                w.setObjectName('objKey')
                lyt.addWidget( w )
                w = QLineEdit( wgtPage )
                w.setObjectName('objPasswordEdit')
                w.setEchoMode( QLineEdit.Password )
                lyt.addWidget( w )
                w = QCheckBox('Register', wgtPage )
                w.setToolTip('Save in QGIS Config')
                w.setObjectName('objRegister')
                lyt.addWidget( w )
                w = QPushButton('Login', wgtPage )
                w.setObjectName('objButtonLogin')
                lyt.addWidget( w )
                lytPage.addLayout( lyt )

                # Layout Choice
                lyt = QHBoxLayout()
                for name in ('Copy clipboard', 'Clean register' ):
                    createRadioButton( name, lyt, wgtPage )
                w = QPushButton('Key', wgtPage )
                w.setIcon( self.iconApply )
                w.setObjectName('objButtonKey')
                lyt.addWidget( w )
                lytPage.addLayout( lyt )

                w = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
                lytPage.addItem( w )

                wgtPage.setLayout( lytPage )
                return wgtPage

            self.setObjectName('planetlabs_dockwidget')
            wgtMain = QWidget( self )
            wgtMain.setAttribute(Qt.WA_DeleteOnClose)

            tabMain = QTabWidget( wgtMain )
            tabMain.setObjectName('objTabMain')
            tabMain.addTab( getPageImage( wgtMain ), 'Images')
            tabMain.addTab( getPageMosaic( wgtMain ), 'Monthly mosaics' )
            tabMain.addTab( getPageKey( wgtMain ), 'Key' )

            self.msgBar = QgsMessageBar(wgtMain)

            layout = QVBoxLayout()
            layout.addWidget( self.msgBar )
            layout.addWidget( tabMain )
            layout.addWidget( self.wgtProgressBar )
            wgtMain.setLayout( layout )

            self.setWidget( wgtMain )

        def getSetting():
            params = {}
            s = QSettings()
            for k in ('key', 'assets', 'path'):
                params[ k ] = s.value( self.pl.localSetting.format( k ), None )
            if not params['path'] is None and not QDir( params['path'] ).exists():
                params['path'] = None
            return params

        def populateUi(paramsSetting):
            # Page Images
            assets = 'objPlanet' if paramsSetting['assets'] is None else "obj{}".format( paramsSetting['assets'] )
            w = self.findChild( QRadioButton, assets )
            w.setChecked( True )
            if not paramsSetting['path'] is None:
                name = paramsSetting['path']
                w = self.findChild( QPushButton, 'objPath')
                w.setToolTip( name )
                args = ['...'] + name.split(os.path.sep)[-2:]
                lblName =  os.path.join( *args)
                w.setText( lblName )
            d2 = QDate.currentDate()
            d1 = d2.addMonths( -1 )
            w1 = self.findChild( QDateEdit, 'objFromImage' )
            w1.setDate( d1 )
            w2 = self.findChild( QDateEdit, 'objToImage' )
            w2.setDate( d2 )
            w1.setMaximumDate( d2.addDays( -1 ) )
            w2.setMinimumDate( d1.addDays( +1 ) )
            w = self.findChild( QSpinBox, 'objDays' )
            w.setValue( d1.daysTo( d2 ) )
            # Page Mosaic
            months = 12
            m2 = QDate.currentDate()
            day = m2.day()
            m2 = m2.addDays( 1-day )
            m1 = m2.addMonths( -1*months )
            w1 = self.findChild( QDateEdit, 'objFromMosaic' )
            w1.setDate( m1 )
            w2 = self.findChild( QDateEdit, 'objToMosaic' )
            w2.setDate( m2 )
            w1.setMaximumDate( m2.addMonths( -1 ) )
            w2.setMinimumDate( m1.addMonths( +1 ) )
            w = self.findChild( QSpinBox, 'objMonths' )
            w.setValue( months )
            # Page Key
            w = self.findChild( QRadioButton, 'objCopy clipboard' )
            w.setChecked( True )
            w = self.findChild( QCheckBox, 'objRegister' )
            w.setCheckState( Qt.Unchecked )

        def checkServer(key):
            self.msgBar.pushInfo('Planet server', 'Checking server...')
            r = self.pl.checkServer( key )
            if not r['live']:
                msg = "'Check server Planet:{}".format( r['message'] )
                self.msgBar.clearWidgets()
                self.msgBar.pushMessage( msg, Qgis.Critical, 0 )
                for name in ('objPageImage', 'objPageMosaic', 'objPageKey'):
                    self._setEnabledPage( name, False )
                return
            if r['hasKey']:
                self._setVisiblePages( r['isValidKey'] )
                return
            self._setVisiblePages( False )

        def connect():
            # Change buttons
            self.changeButtonCancel.connect( self._changeButtonCancel )
            # Images
            self.btnSearchImage.clicked.connect( self._onSearchImage )
            self.findChild( QPushButton, 'objPath').clicked.connect( self._onPath )
            self.findChild( QDateEdit, 'objFromImage').dateChanged.connect( self._onDateFromImage )
            self.findChild( QDateEdit, 'objToImage').dateChanged.connect( self._onDateToImage )
            self.findChild( QSpinBox, 'objDays').valueChanged.connect( self._onValueChangedImage )
            # Mosaic
            self.btnMosaic.clicked.connect( self._onAddMosaics )
            self.findChild( QDateEdit, 'objFromMosaic' ).dateChanged.connect( self._onDateFromMosaic )
            self.findChild( QDateEdit, 'objToMosaic' ).dateChanged.connect( self._onDateToMosaic )
            self.findChild( QSpinBox, 'objMonths' ).valueChanged.connect( self._onValueChangedMosaic )
            # Key
            self.findChild( QPushButton, 'objButtonLogin').clicked.connect( self._onLogin )
            self.findChild( QPushButton, 'objButtonKey').clicked.connect( self._onKey )

        super().__init__('Planet Labs', iface.mainWindow() )
        self.wgtProgressBar = WidgetProgressBar(self)
        self.pl = PlanetLabs( iface, self )
        self.titleLog, self.currentProcess, self.countFeatures = 'Planet', None, None
        self.nameAssets = {
            'Planet': 'PSScene4Band',
            'Rapideye': 'REOrthoTile',
            'Skysat': 'SkySatScene',
        }
        self.titleSelectDirectory = "Select download directory"
        self.btnSearchImage, self.btnMosaic, self.msgBar = None, None, None
        ( self.iconApply, self.iconCancel, iconDir ) = getIconApplyCancelDir()
        setupUi()
        self.wgtProgressBar.hide()
        self.nameOptionsKey = ('Copy clipboard', 'Clean register')
        ojbNamesKey = [ "obj{}".format( k ) for k in self.nameOptionsKey ] + ['objButtonKey']
        self.pageKey = { # Define in setupUi()
            'login': ('objKey', 'objPasswordEdit', 'objRegister', 'objButtonLogin'),
            'key': ojbNamesKey
        }
        paramsSetting = getSetting()
        populateUi( paramsSetting )
        checkServer( paramsSetting['key'] )
        connect()

    def __del__(self):
        del self.pl

    def _setNamePath(self, name):
        w = self.findChild( QPushButton, 'objPath' )
        w.setToolTip( name )
        args = ['...'] + name.split(os.path.sep)[-2:]
        lblName =  os.path.join( *args)
        w.setText( lblName )
        self.msgBar.pushInfo("Download's Diretory", name )

    def _getValues(self):
        def getOptionRadioButton(names):
            for k in names:
                name = "obj{}".format( k )
                w = self.findChild( QRadioButton, name )
                if w.isChecked():
                    return k
            return None

        image = {
            'assets': getOptionRadioButton( self.nameAssets.keys() ),
            'path': self.findChild( QPushButton, 'objPath').toolTip(),
            'date1': self.findChild( QDateEdit, 'objFromImage').date(),
            'date2': self.findChild( QDateEdit, 'objToImage').date()
        }
        mosaic = {
            'date1': self.findChild( QDateEdit, 'objFromMosaic').date(),
            'date2': self.findChild( QDateEdit, 'objToMosaic').date()
        }
        # 
        key = {
            'optionKey': getOptionRadioButton( self.nameOptionsKey ),
            'password': self.findChild( QLineEdit, 'objPasswordEdit').text(),
            'hasRegister': self.findChild( QCheckBox, 'objRegister').checkState() == Qt.Checked
        }
        return {
            'image': image,
            'mosaic': mosaic,
            'key': key
        }

    def _setSpin(self, date1, date2, objectName, slot, isMonth=False ):
        w = self.findChild( QSpinBox, objectName )
        w.valueChanged.disconnect( slot )
        days = date1.daysTo( date2 )
        value =  days if not isMonth else int( days / 30)
        w.setValue( value )
        w.valueChanged.connect( slot )

    def _valueChangedSpin(self, vTime, objectNameDate1, objectNameDate2, slotDate1, isMonth=False ):
        date1 = self.findChild( QDateEdit, objectNameDate1 )
        date2 = self.findChild( QDateEdit, objectNameDate2 )
        newDate = date2.date().addDays( -1*vTime ) if not isMonth else date2.date().addMonths( -1*vTime )
        date1.dateChanged.disconnect( slotDate1 )
        date1.setDate( newDate )
        date2.setMinimumDate( newDate.addDays(+1) )
        date1.dateChanged.connect( slotDate1 )

    def _dateFromChanged(self, date, objTo, objSpin, slotSpin, isMonth=False):
        date2 = self.findChild( QDateEdit, objTo )
        f = date.addDays if not isMonth else date.addMonths
        date2.setMinimumDate( f( +1 ) )
        args = ( date, date2.date(), objSpin, slotSpin, isMonth )
        self._setSpin( *args)

    def _dateToChanged(self, date, objFrom, objSpin, slotSpin, isMonth=False):
        date1 = self.findChild( QDateEdit, objFrom )
        f = date.addDays if not isMonth else date.addMonths
        date1.setMaximumDate( f( -1 ) )
        args = ( date1.date(), date, objSpin, slotSpin, isMonth )
        self._setSpin( *args)

    def _setEnabledPage(self, name, enable):
        w = self.findChild( QWidget, name )
        w.setEnabled( enable )

    def _setVisiblePages(self, enable):
        def setVisiblePageKey(group, visible):
            for name in self.pageKey[ group ]:
                w = self.findChild( QWidget, name )
                w.show() if visible else w.hide()

        for name in ('objPageImage', 'objPageMosaic'):
            self._setEnabledPage( name, enable )
        setVisiblePageKey('key', enable )
        setVisiblePageKey('login', not enable )
        w = self.findChild( QTabWidget, 'objTabMain')
        idx = 0 if enable else 2 # Key Tab
        w.setCurrentIndex( idx )

    def writeSetting(self):
        values = self._getValues()
        vpath = values['image']['path']
        if vpath == self.titleSelectDirectory or not QDir( vpath ).exists():
            vpath = None
        assets = values['image']['assets']
        s = QSettings()
        s.setValue( self.pl.localSetting.format( 'path' ),  vpath )
        s.setValue( self.pl.localSetting.format( 'assets' ), assets )

    def getDownloadDir(self):
        values = self._getValues()
        vpath = values['image']['path']
        if vpath == self.titleSelectDirectory:
            return None
        return vpath

    @pyqtSlot(str)
    def changeButtonApply(self, label):
        if label == 'Search':
            button = self.btnSearchImage
        elif label == 'Add':
            button = self.btnMosaic
        button.setText( label)
        button.setIcon( self.iconApply )

    @pyqtSlot(QPushButton)
    def _changeButtonCancel(self, button):
        button.setText('Cancel')
        button.setIcon( self.iconCancel )

    @pyqtSlot(bool)
    def _onSearchImage(self, checked):
        label = 'Search'
        if self.btnSearchImage.text() == label:
            self.changeButtonCancel.emit( self.btnSearchImage )
            v = self._getValues()
            asset = self.nameAssets[ v['image']['assets'] ]
            self.buttonSearchImageClicked.emit( asset, v['image']['date1'], v['image']['date2'] )
        else:
            self.cancelProcess.emit()

    @pyqtSlot(bool)
    def _onAddMosaics(self, checked):
        label = 'Add'
        if self.btnMosaic.text() == label:
            self.changeButtonCancel.emit( self.btnMosaic )
            v = self._getValues()
            self.buttonAddMosaicsClicked.emit( v['mosaic']['date1'], v['mosaic']['date2'] )
        else:
            self.cancelProcess.emit()

    @pyqtSlot(bool)
    def _onLogin(self, checked):
        v = self._getValues()
        self.buttonLoginClicked.emit( v['key']['password'], v['key']['hasRegister'] )

    @pyqtSlot(bool)
    def _onKey(self, checked):
        v = self._getValues()
        self.buttonKeyClicked.emit( v['key']['optionKey'] )

    @pyqtSlot(bool)
    def _onPath(self, checked):
        vpath = self._getValues()['image']['path']
        if vpath == self.titleSelectDirectory:
            vpath = None
        sdir = QFileDialog.getExistingDirectory(self, self.titleSelectDirectory, vpath )
        if len(sdir) > 0:
            self._setNamePath( sdir )

    @pyqtSlot(QDate)
    def _onDateFromImage(self, date):
        self._dateFromChanged( date, 'objToImage', 'objDays', self._onValueChangedImage )

    @pyqtSlot(QDate)
    def _onDateFromMosaic(self, date):
        self._dateFromChanged( date, 'objToMosaic', 'objMonths', self._onValueChangedMosaic, True )

    @pyqtSlot(QDate)
    def _onDateToImage(self, date):
        self._dateToChanged( date, 'objFromImage', 'objDays', self._onValueChangedImage )

    @pyqtSlot(QDate)
    def _onDateToMosaic(self, date):
        self._dateToChanged( date, 'objFromMosaic', 'objMonths', self._onValueChangedMosaic, True )

    @pyqtSlot(int)
    def _onValueChangedImage(self, days ):
        args = ( days, 'objFromImage', 'objToImage', self._onDateFromImage )
        self._valueChangedSpin( *args )

    @pyqtSlot(int)
    def _onValueChangedMosaic(self, months ):
        args = ( months, 'objFromMosaic', 'objToMosaic', self._onDateFromMosaic, True )
        self._valueChangedSpin( *args )

    @pyqtSlot(bool)
    def visiblePages(self, enable):
        self._setVisiblePages( enable )

    @pyqtSlot(str)
    def currentProcess(self, process):
        self.currentProcess = process
        self.wgtProgressBar.currentProcess( process )
        self.wgtProgressBar.resetCount()

    @pyqtSlot(str)
    def currentImage(self, image):
        self.wgtProgressBar.currentFile( image )
        self.wgtProgressBar.resetFile()

    @pyqtSlot(Qgis.MessageLevel, str, list)
    def message(self, level, message, itemsLog):
        if level == Qgis.Info:
            f = self.msgBar.pushInfo
        elif level == Qgis.Warning:
            f = self.msgBar.pushWarning
        elif level == Qgis.Critical:
            f = self.msgBar.pushCritical
        elif level == Qgis.Success:
            f = self.msgBar.pushSuccess
        else:
            return
        self.msgBar.popWidget()
        f( self.currentProcess, message )
        if len(itemsLog) > 0:
            msg = "{}. Items: {}".format( message, ','.join( itemsLog ) )
            QgsMessageLog.logMessage( msg, self.titleLog, Qgis.Warning )

    @pyqtSlot()
    def requestBulkFeatures(self):
        self.msgBar.clearWidgets()
        msg = "{}: Request a bulk features...".format( self.currentProcess )
        self.msgBar.pushMessage( msg, Qgis.Info, 0 )

    @pyqtSlot()
    def startCountFeatures(self):
        self.countFeatures = 0

    @pyqtSlot(str)
    def receivedFeature(self, item_id):
        self.msgBar.clearWidgets()
        self.countFeatures += 1
        msg = "{}: Received feature '{}'(Total {})".format( self.currentProcess, item_id, self.countFeatures )
        self.msgBar.pushMessage( msg, Qgis.Info, 0 )

    @pyqtSlot(bool)
    def showProgressBar(self, hasFile):
        self.wgtProgressBar.setHasFile( hasFile )
        self.wgtProgressBar.show()
       
    @pyqtSlot()
    def hideProgressBar(self):
        self.wgtProgressBar.hide()


class PlanetLabs(QObject):
    visiblePages = pyqtSignal(bool)
    currentProcess = pyqtSignal(str)
    currentImage = pyqtSignal(str)
    message = pyqtSignal(Qgis.MessageLevel, str, list)
    requestBulkFeatures = pyqtSignal()
    startCountFeatures = pyqtSignal()
    receivedBytesImage = pyqtSignal(int, int, int)
    processingFeatures = pyqtSignal(int, int, int)
    showProgressBar = pyqtSignal(bool)
    hideProgressBar = pyqtSignal()
    changeButtonApply = pyqtSignal(str)
    killProcess = pyqtSignal()
    def __init__(self, iface, dockWidget):
        def getCoordinateTransform():
            crsXYZtile = QgsCoordinateReferenceSystem('EPSG:3857')
            return QgsCoordinateTransform( self.crsCatalog, crsXYZtile, self.project )

        super().__init__()
        self.dockWidget = dockWidget
        self.iface = iface
        self.localSetting = 'catalogpl_v3_plugin/{}'
        self.clipboard = QApplication.clipboard()
        self.apiPL = API_PlanetLabs()
        self._connect()
        self.canvas = iface.mapCanvas()
        self.project = QgsProject.instance()
        self.layerTreeRoot = self.project.layerTreeRoot()
        self.wdgMetadata = TreeWidgetMetadata()
        self.mapCanvasGeom = MapCanvasGeometry()
        self.pluginName = 'Planet Labs'
        self.menuXYZTiles = MenuXYZTiles( self.pluginName )
        funcActions = {
            'addXYZtiles': self.addXYZtiles,
            'updateAssetsStatus': self.updateAssetsStatus,
            'activeAssets': self.activeAssets,
            'downloadImages': self.downloadImages
        }
        self.menuCatalog = MenuCatalogPlanet( self.pluginName, funcActions)
        self.crsCatalog = QgsCoordinateReferenceSystem('EPSG:4326')
        self.coordTransform = getCoordinateTransform()
        self.styleFile = 'pl_scenes.qml'
        self.downloadDir = '/home/lmotta/data/pl_download'
        self.formatCatalogName = "{}({} .. {})"        
        self.catalog = None
        self.catalog_id = None
        self.calculateMetadata = None
        self.response = None
        self.imageDownload = None
        self.limitPercentImage = 5

    def __del__(self):
        del self.menuXYZTiles
        del self.menuCatalog
        self._connect( False )

    def _connect(self, isConnect=True):
        ss = [
            { 'signal': self.dockWidget.buttonSearchImageClicked, 'slot': self.searchImage },
            { 'signal': self.dockWidget.buttonAddMosaicsClicked, 'slot': self.addMosaics },
            { 'signal': self.dockWidget.buttonLoginClicked, 'slot': self.onLogin },
            { 'signal': self.dockWidget.buttonKeyClicked, 'slot': self.onKey },
            { 'signal': self.dockWidget.cancelProcess, 'slot': self.onCancel },
            { 'signal': self.dockWidget.wgtProgressBar.buttonCancelClicked, 'slot': self.onCancel },
            { 'signal': self.visiblePages, 'slot': self.dockWidget.visiblePages },
            { 'signal': self.currentProcess, 'slot': self.dockWidget.currentProcess },
            { 'signal': self.currentImage, 'slot': self.dockWidget.currentImage },
            { 'signal': self.message, 'slot': self.dockWidget.message },
            { 'signal': self.requestBulkFeatures, 'slot': self.dockWidget.requestBulkFeatures },
            { 'signal': self.startCountFeatures, 'slot': self.dockWidget.startCountFeatures },
            { 'signal': self.apiPL.addFeature, 'slot': self.dockWidget.receivedFeature},
            { 'signal': self.processingFeatures, 'slot': self.dockWidget.wgtProgressBar.processingCount },
            { 'signal': self.receivedBytesImage, 'slot': self.dockWidget.wgtProgressBar.receivedBytesFile },
            { 'signal': self.showProgressBar, 'slot': self.dockWidget.showProgressBar },
            { 'signal': self.hideProgressBar, 'slot': self.dockWidget.hideProgressBar },
            { 'signal': self.changeButtonApply, 'slot': self.dockWidget.changeButtonApply },
            { 'signal': self.killProcess, 'slot': self.apiPL.kill }
        ]
        if isConnect:
            for item in ss:
                item['signal'].connect( item['slot'] )  
        else:
            for item in ss:
                item['signal'].disconnect( item['slot'] )

    def _setPropertyCatalog(self, item_type, date1, date2):
        self.catalog.setCustomProperty('item_type', item_type )
        self.catalog.setCustomProperty('date1', date1 )
        self.catalog.setCustomProperty('date2', date2 )

    def _createCatalog(self, item_type, date1, date2):
        l_fields = [ "field={key}:{value}".format( key=k, value=self.apiPL.fieldsDef[ k ] ) for k in self.apiPL.fields ]
        l_fields.insert( 0, "Multipolygon?crs={}".format( self.crsCatalog.authid().lower() ) )
        l_fields.append( "index=yes" )
        uri = '&'.join( l_fields )
        arg = ( item_type, date1, date2 )
        name = self.formatCatalogName.format( *arg )
        self.catalog = QgsVectorLayer( uri, name, 'memory' )
        self.catalog.loadNamedStyle( os.path.join( os.path.dirname( __file__ ), self.styleFile ) )
        self._setPropertyCatalog( item_type, date1, date2 )
        TreeWidgetMetadata.setForm( self.catalog )
        self.menuCatalog.setLayer( self.catalog )
        self.catalog_id = self.catalog.id()

    def _responseFinished(self, response):
        self.response = response

    def addXYZtiles(self):
        def getGroup():
            args = ( item_type, date1, date2 )
            name = self.formatCatalogName.format( *args )
            ltg = self.layerTreeRoot.findGroup( name )
            if ltg is None:
                ltg = self.layerTreeRoot.addGroup( name )
            else:
                ltg.removeAllChildren()
            return ltg

        def setCustomProperty(layer, item_type, item_id):
            geom = feat.geometry()
            geom.transform( self.coordTransform )
            layer.setCustomProperty('layer_id', self.catalog_id )
            layer.setCustomProperty('field_id', { 'name': 'item_id', 'value': item_id } ) # Field'type = String
            layer.setCustomProperty('wkt_geom', geom.asWkt() )
            self.menuXYZTiles.setLayer( layer )
        
        def getXYZTiles(item_type, item_id):
            url = self.apiPL.urlYXZImage.format( item_type=item_type, item_id=item_id )
            return "type=xyz&url={url}&username={username}&zmax=19&zmin=0".format( url=url, username=self.apiPL.validKey )

        self.currentProcess.emit('Add XYZ tiles images')
        self.apiPL.access.isKill = False
        item_type = self.catalog.customProperty('item_type')
        date1 = self.catalog.customProperty('date1')
        date2 = self.catalog.customProperty('date2')
        request = QgsFeatureRequest().setFlags( QgsFeatureRequest.NoGeometry)
        request = request.setSubsetOfAttributes( ['item_id', 'date'], self.catalog.fields() )
        totalData = self.catalog.featureCount()
        totalSelected = self.catalog.selectedFeatureCount()
        if totalSelected > 0:
            totalData = totalSelected
            idxs = self.catalog.selectedFeatureIds()
            request = request.setFilterFids( idxs )
        self.showProgressBar.emit(False)
        countData = 0
        it = self.catalog.getFeatures( request )
        messageInvalidKey = None
        lstInvalidKey = []
        dates = {}
        for feat in it:
            if self.apiPL.access.isKill:
                self.hideProgressBar.emit()
                self.message.emit( Qgis.Critical, 'Canceled by user', [] )
                return
            self.apiPL.checkValidKeyImage( item_type, feat['item_id'], self._responseFinished )
            countData += 1
            self.processingFeatures.emit( countData, totalData, int( countData / totalData * 100) )
            if not self.response['isOk']:
                if messageInvalidKey is None:
                    messageInvalidKey = self.response['message']
                lstInvalidKey.append( feat['item_id'] )
                continue
            url = getXYZTiles( item_type, feat['item_id'] )
            layer = QgsRasterLayer( url, feat['item_id'], 'wms')
            setCustomProperty( layer, item_type, feat['item_id'] )
            self.project.addMapLayer( layer, addToLegend=False )
            date = feat['date']
            if date in dates:
                dates[ date ].append( layer )
            else:
                dates[date] = [ layer ]
        self.hideProgressBar.emit()
        total = len( lstInvalidKey )
        if total == totalData:
            msg = "{message}(total = {total}).".format( message=messageInvalidKey,  total=total )
            self.message.emit( Qgis.Critical, msg, lstInvalidKey )
            return
        ltg = getGroup()
        ltg.setItemVisibilityChecked( False )
        for date in sorted( dates, reverse=True ):
            name = "{}(Total {})".format( date, len( dates[ date ] ) )
            ltgDate = ltg.addGroup( name )
            ltgDate.setItemVisibilityChecked( False )
            ltgDate.setExpanded(False)
            for layer in dates[ date ]:
                ltgDate.addLayer( layer )
                ltgDate.setItemVisibilityChecked( False )
        if total > 0:
            msg = "{message}(total = {total}).".format( message=messageInvalidKey,  total=total )
            self.message.emit( Qgis.Warning, msg, lstInvalidKey )
        else:
            self.message.emit( Qgis.Success, 'Finished OK', [] )

    def updateAssetsStatus(self):
        self.currentProcess.emit('Update assets status')
        self.apiPL.access.isKill = False
        request = QgsFeatureRequest().setFlags( QgsFeatureRequest.NoGeometry)
        request = request.setSubsetOfAttributes( ['meta_json'], self.catalog.fields() )
        totalData = self.catalog.featureCount()
        totalSelected = self.catalog.selectedFeatureCount()
        if totalSelected > 0:
            totalData = totalSelected
            idxs = self.catalog.selectedFeatureIds()
            request = request.setFilterFids( idxs )
        self.showProgressBar.emit(False)
        countData = 0
        idMetaJson = self.catalog.fields().indexFromName('meta_json')
        idMetaJsize = self.catalog.fields().indexFromName('meta_jsize')
        self.calculateMetadata = True
        self.catalog.startEditing()
        it = self.catalog.getFeatures( request )
        item_id_no_set_assets = []
        for feat in it:
            if self.apiPL.access.isKill:
                self.catalog.commitChanges()
                self.hideProgressBar.emit()
                self.message.emit( Qgis.Critical, 'Canceled by user', [] )
                return
            meta_json = json.loads( feat['meta_json'] )
            self.apiPL.getAssetsStatus(meta_json['links']['assets'], self._responseFinished )
            if self.response['isOk']:
                assets_status = self.response['assets_status']
            else:
                item_id_no_set_assets.append( feat['item_id'] )
                continue
            if 'assets_status' in meta_json:
                del meta_json['assets_status']
            meta_json['assets_status'] = assets_status
            featId = feat.id()
            meta_json = json.dumps( meta_json )
            self.catalog.changeAttributeValue( featId, idMetaJson, meta_json )
            self.catalog.changeAttributeValue( featId, idMetaJsize, len( meta_json) )
            countData += 1
            self.processingFeatures.emit( countData, totalData, int( countData / totalData * 100) )
        self.catalog.commitChanges()
        self.calculateMetadata = False
        total = len( item_id_no_set_assets )
        if total > 0:
            msg = "Error set assets(total {}).".format( total )
            self.message.emit( Qgis.Critical, msg, item_id_no_set_assets )
        else:
            self.message.emit( Qgis.Success, 'Finished OK', [] )
        self.hideProgressBar.emit()

    def activeAssets(self):
        def exitsActivate(meta_json):
            return 'assets_status' in meta_json and \
                   'a_analytic' in meta_json['assets_status'] and \
                   'activate' in meta_json['assets_status']['a_analytic']


        self.currentProcess.emit('Active assets')
        self.apiPL.access.isKill = False
        request = QgsFeatureRequest().setFlags( QgsFeatureRequest.NoGeometry)
        request = request.setSubsetOfAttributes( ['meta_json','item_id'], self.catalog.fields() )
        totalData = self.catalog.featureCount()
        totalSelected = self.catalog.selectedFeatureCount()
        if totalSelected > 0:
            totalData = totalSelected
            idxs = self.catalog.selectedFeatureIds()
            request = request.setFilterFids( idxs )
        self.showProgressBar.emit(False)
        countData = 0
        it = self.catalog.getFeatures( request )
        item_id_no_assets_status = []
        for feat in it:
            if self.apiPL.access.isKill:
                self.hideProgressBar.emit()
                self.message.emit( Qgis.Critical, 'Canceled by user', [] )
                return
            meta_json = json.loads( feat['meta_json'] )
            if not exitsActivate( meta_json ):
                item_id_no_assets_status.append( feat['item_id'] )
                continue
            url = meta_json['assets_status']['a_analytic']['activate']
            self.apiPL.requestUrl( url, self._responseFinished )
            countData += 1
            self.processingFeatures.emit( countData, totalData, int( countData / totalData * 100) )
        total = len( item_id_no_assets_status )
        if total > 0:
            msg = "Missing ['assets_status']['a_analytic']['activate'] in metadata of features(total {}).".format( total )
            self.message.emit( Qgis.Critical, msg, item_id_no_assets_status )
        else:
            self.message.emit( Qgis.Success, 'Finished OK', [] )
        self.hideProgressBar.emit()

    def downloadImages(self):
        def getGroup(item_type):
            name = "Download_{}".format( item_type )
            ltg = self.layerTreeRoot.findGroup( name )
            if ltg is None:
                ltg = self.layerTreeRoot.addGroup( name )
            return ltg

        def getRasterSources():
            it = filter( lambda ltl: ltl.layer().type() == QgsMapLayer.RasterLayer, ltgDonwload.findLayers() )
            return [ ltl.layer().source() for ltl in it ]

        def addLayer(fileName, item_id):
            layer = QgsRasterLayer( fileName, item_id )
            self.project.addMapLayer( layer, addToLegend=False )
            ltgDonwload.addLayer( layer ).setItemVisibilityChecked( False )

        def saveImage(url, item_type, item_id, downloadDir):
            @pyqtSlot(int, int)
            def progressImage(bytesReceived, bytesTotal):
                perc = int( bytesReceived / bytesTotal * 100)
                if perc % self.limitPercentImage == 0:
                    self.receivedBytesImage.emit( bytesReceived, bytesTotal, perc )
            
            fileName = "{}_{}.part".format( item_type, item_id )
            self.currentImage.emit( fileName )
            fileName = os.path.join( downloadDir, fileName )
            self.imageDownload = QFile( fileName )
            self.imageDownload.open( QIODevice.WriteOnly )
            self.apiPL.saveImage( url, self._responseFinished, self.imageDownload.write, progressImage )
            self.imageDownload.flush()
            self.imageDownload.close()
            if self.response['isOk']:
                fileNameEnd = "{}.tif".format( fileName.rsplit('.')[0] )
                self.imageDownload.rename( fileNameEnd )
            else:
                self.imageDownload.remove()
                msg = "Error Download: {}".format( self.response['message'] )
                self.message.emit( Qgis.Critical, msg, [] )
            del self.imageDownload
            self.imageDownload = None
            return self.response['isOk']

        self.currentProcess.emit('Download images')
        downloadDir = self.dockWidget.getDownloadDir()
        self.apiPL.access.isKill = False
        if downloadDir is None:
            self.message.emit( Qgis.Critical, 'Select download directory', [] )
            return
        item_type = self.catalog.customProperty('item_type')
        ltgDonwload = getGroup( item_type )
        ltgDonwload.setItemVisibilityChecked( False )
        sourcesRaster = getRasterSources()
        request = QgsFeatureRequest().setFlags( QgsFeatureRequest.NoGeometry)
        request = request.setSubsetOfAttributes( ['item_id', 'meta_json'], self.catalog.fields() )
        totalData = self.catalog.featureCount()
        totalSelected = self.catalog.selectedFeatureCount()
        if totalSelected > 0:
            totalData = totalSelected
            idxs = self.catalog.selectedFeatureIds()
            request = request.setFilterFids( idxs )
        self.showProgressBar.emit(True)
        countData = 0
        it = self.catalog.getFeatures( request )
        item_id_no_assets_status = []
        item_id_no_active = []
        item_id_error_download = []
        for feat in it:
            if self.apiPL.access.isKill:
                self.hideProgressBar.emit()
                self.message.emit( Qgis.Critical, 'Canceled by user', [] )
                return
            countData += 1
            self.processingFeatures.emit( countData, totalData, int( countData / totalData * 100) )
            item_id = feat['item_id']
            fileName = "{}_{}.tif".format( item_type, item_id )
            fileName = os.path.join( downloadDir, fileName )
            info = QFileInfo( fileName )
            if info.exists():
                if not fileName in sourcesRaster:
                    addLayer( fileName, item_id )
                continue
            meta_json = json.loads( feat['meta_json'] )
            if not 'assets_status' in meta_json:
                item_id_no_assets_status.append( item_id )
                continue
            assets_status = meta_json['assets_status']
            if not assets_status['a_analytic']['status'] == 'active':
                item_id_no_active.append( item_id )
                continue
            url = assets_status['a_analytic']['location']
            if not saveImage( url, item_type, item_id, downloadDir):
                item_id_error_download.append( item_id )
            else:
                addLayer( fileName, item_id )

        total = len( item_id_no_assets_status )
        if total > 0:
            msg = "Missing 'assets_status' in metadata of features(total {}).".format( total )
            self.message.emit( Qgis.Critical, msg, item_id_no_assets_status )
        else:
            total = len( item_id_no_active )
            if total > 0:
                msg = "Status 'assets_status'.'a_analytic' is not 'active' in metadata of features(total {}).".format( total )
                self.message.emit( Qgis.Critical, msg, item_id_no_active )
            else:
                total = len( item_id_error_download )
                if total > 0:
                    msg = "Error download images(total {}).".format( total )
                    self.message.emit( Qgis.Critical, msg, item_id_error_download )
                else:
                    self.message.emit( Qgis.Success, 'Finished OK', [] )
        self.hideProgressBar.emit()

    def populateForm(self, widgets, feature):
        """
        Populate widgets from 'form.py'

        :param widgets: List fo widgets('form.py')
        :feature: Feature from open table(Form) in QGIS
        """
        def setErrorMessage(msg):
            widgets['message_status'].setText( msg )
            widgets['message_status'].setStyleSheet('color: red')

        def finishedThumbnail(response):
            if not response['isOk']:
                setErrorMessage( response['message'] )
                widgets['thumbnail'].setText('')
                return
            widgets['thumbnail'].setPixmap( response['thumbnail'] )
            widgets['message_status'].setText('')

        # Clean
        for name in ( 'message_status', 'message_clip'):
            widgets[ name ].setStyleSheet('color: black')
            widgets[ name ].setText('')
        widgets['thumbnail'].setText('')

        if self.apiPL.validKey is None:
            setErrorMessage('Need run the plugin Planet Catalog')
            return
        if self.calculateMetadata:
            setErrorMessage('Updating metadata. Wait finish the edition.')
            return

        # Tab Item
        # Populate 'item_id', 'date
        [ widgets[ name ].setText( feature[ name ] ) for name in ('item_id', 'date') ]

        # Populate 'thumbnail'
        meta_json = json.loads( feature['meta_json'] )
        widgets['message_status'].setText("Fetching thumbnail...")
        url = "{url}?api_key={key}".format(url=meta_json['links']['thumbnail'], key=self.apiPL.validKey )
        self.apiPL.getThumbnail( url, finishedThumbnail )

        # Tab Metadata
        # Message 'message_clip'
        msg = "* Double click for copy 'Expression item' in Clipboard"
        widgets['message_clip'].setText( msg )
        self.wdgMetadata.create( widgets['tabMetadata'], widgets['message_clip'], 'meta_json', meta_json )

    def actionsForm(self, nameAction, feature_id=None):
        """
        Run action defined in layer, provide by style file(API_PlanetLabs.styleFile)

        :param nameAction: Name of action
        :params feature_id: Feature ID
        :meta_json: Value of JSON(dictionary) from name_exp_json
        """
        # Actions functions
        def highlight(feature_id):
            geom = self.catalog.getFeature( feature_id ).geometry()
            self.mapCanvasGeom.highlight( self.catalog, geom )
            return { 'isOk': True }

        def zoom(feature):
            geom = self.catalog.getFeature( feature_id ).geometry()
            self.mapCanvasGeom.zoom( self.catalog, geom )
            return { 'isOk': True }

        def addXYZtiles(feature=None):
            self.addXYZtiles()
            return { 'isOk': True }

        def updateAssetsStatus(feature=None):
            self.updateAssetsStatus()
            return { 'isOk': True }

        def activeAssets(feature=None):
            self.activeAssets()
            return { 'isOk': True }

        def downloadImages(feature=None):
            self.downloadImages()
            return { 'isOk': True }

        actionsFunc = {
            'highlight':   highlight,
            'zoom':        zoom,
            'addxyztiles': addXYZtiles,
            'updateAssetsStatus': updateAssetsStatus,
            'activeAssets': activeAssets,
            'downloadImages': downloadImages
        }
        if not nameAction in actionsFunc.keys():
            return { 'isOk': False, 'message': "Missing action '{}'".format( nameAction ) }
        return actionsFunc[ nameAction ]( feature_id )

    def requestHostLive(self):
        self.currentProcess.emit('Check Planet is live')
        self.apiPL.isHostLive( self._responseFinished )
        if self.response['isOk']:
            self.message.emit( Qgis.Success, 'Finished OK', [] )
        else:
            self.message.emit( Qgis.Critical, 'Planet server is out', [] )

    def requestPopulateCatalog(self, item_type, date1, date2):
        def getJsonExtent():
            crsCanvas = self.canvas.mapSettings().destinationCrs()
            ct = QgsCoordinateTransform( crsCanvas, self.crsCatalog, self.project )
            rectCanvas = self.canvas.extent() if crsCanvas == self.crsCatalog else ct.transform( self.canvas.extent() )
            geom = QgsGeometry.fromRect( rectCanvas )
            return json.loads( geom.asJson() )
        
        def getDateRangeFilter(dateGte, dateLte):
            def getStringDate(date):
                return "{}Z".format( QDateTime( date ).toString( Qt.ISODate ) )

            dtGte = QDateTime( dateGte )
            dtLte = QDateTime( dateLte )
            dtLte.setTime( QTime(23,59,59) )
            return  {
                "gte": "{}Z".format( dtGte.toString( Qt.ISODate ) ),
                "lte": "{}Z".format( dtLte.toString( Qt.ISODate ) )
            }

        def finished(response):
            if not response['isOk']:
                self.response = response
                return
            if len( response['features'] ) == 0:
                self.response = response
                self.response['exitsFeatures'] = False
            else:
                args = ( self.catalog, self.apiPL, self.requestBulkFeatures )
                pfc = PopulateFeaturesCatalog( *args )
                params = { 'features': response['features'], '_next': response['_links']['_next'] }
                pfc.populate( params )
                self.response = pfc.response
                self.response['exitsFeatures'] = True

        def getNameCatalog():
            item_type = self.catalog.customProperty('item_type')
            date1 = self.catalog.customProperty('date1')
            date2 = self.catalog.customProperty('date2')
            arg = ( item_type, date1, date2 )
            return self.formatCatalogName.format( *arg )

        def closeTableAttribute():
            layer_id = self.catalog_id
            widgets = QApplication.instance().allWidgets()
            for tb in filter( lambda w: isinstance( w, QDialog ) and layer_id in w.objectName(),  widgets ):
                tb.close()

        self.currentProcess.emit('Populate Catalog')
        self.startCountFeatures.emit()
        geometry_filter = {
            "type": "GeometryFilter",
            "field_name": "geometry",
            "config": getJsonExtent()
        }
        date_range_filter = {
            "type": "DateRangeFilter",
            "field_name": "acquired",
            "config": getDateRangeFilter(  date1, date2 )
        }
        json_request = {
            "item_types": [ item_type ],
            "filter": {
                "type": "AndFilter",
                "config": [ geometry_filter, date_range_filter ]
            }
        }
        d1 = date1.toString( Qt.ISODate )
        d2 = date2.toString( Qt.ISODate )
        existsCatalog = not self.catalog is None and not self.project.mapLayer( self.catalog_id ) is None
        if not existsCatalog:
            self._createCatalog( item_type, d1, d2 )
        else:
            arg = ( item_type, d1, d2 )
            name = self.formatCatalogName.format( *arg )
            name = "Receiving... - {}".format( name )
            self.catalog.setName( name )
            self._setPropertyCatalog( item_type, d1, d2 )
            self.catalog.dataProvider().truncate() # Delete all features
            closeTableAttribute()
        self.response = None
        self.calculateMetadata = True
        self.requestBulkFeatures.emit()
        self.apiPL.getUrlScenesJson( json_request, finished )
        self.calculateMetadata = False
        if self.response['isOk']:
            if not existsCatalog:
                self.project.addMapLayer( self.catalog, addToLegend=False )
                self.layerTreeRoot.insertLayer( 0, self.catalog ).setCustomProperty("showFeatureCount", True)
            else:
                self.catalog.setName( getNameCatalog() )
                self.catalog.triggerRepaint()

    def checkServer(self, key):
        self.requestHostLive()
        if not self.response['isOk']:
            return { 'live': False, 'message': self.response['message'] }
        r = { 'live': True}
        if not key is None:
            r['hasKey'] = True
            self.apiPL.setKey( key, self._responseFinished )
            if not self.response['isOk']:
                r['isValidKey'] = False
                return r
            r['isValidKey'] = True
            return r
        r['hasKey'] = False
        return r

    @pyqtSlot(str, QDate, QDate)
    def searchImage(self, item_type, date1, date2):
        self.currentProcess.emit('Search image')
        self.apiPL.access.isKill = False
        if self.iface.mapCanvas().layerCount() == 0:
            msg = 'Need layer(s) in map'
            self.message.emit( Qgis.Critical, msg, [] )
        else:
            self.requestPopulateCatalog( item_type, date1, date2 )
            if not self.response['isOk']:
                self.message.emit( Qgis.Critical, self.response['message'], [] )
            elif not self.response['exitsFeatures']:
                self.message.emit( Qgis.Warning, 'No scene in map view', [] )
            else:
                self.message.emit( Qgis.Success, 'Finished OK', [] )
            
        self.changeButtonApply.emit('Search')

    @pyqtSlot(QDate, QDate)
    def addMosaics(self, date1, date2):
        def getGroup():
            y1, m1 = date1.year(), date1.month()
            y2, m2 = date2.year(), date2.month()
            name = "Mosaic {year1}_{month1:02d}...{year2}_{month2:02d}".format( year1=y1, month1=m1, year2=y2, month2=m2 )
            ltg = self.layerTreeRoot.findGroup( name )
            if ltg is None:
                ltg = self.layerTreeRoot.addGroup( name )
            else:
                ltg.removeAllChildren()
            return ltg

        def addLayer(name, group):
            url = self.response['url']
            url = "type=xyz&url={url}&username={username}&zmax=19&zmin=0".format( url=url, username=self.apiPL.validKey )
            layer = QgsRasterLayer( url, name, 'wms')
            self.project.addMapLayer( layer, addToLegend=False )
            group.addLayer( layer ).setItemVisibilityChecked( False )

        def outFunction(message):
            self.message.emit( Qgis.Critical, message, [] )
            self.changeButtonApply.emit('Add')

        def checkValidKey(vdate):
            year, month = vdate.year(), vdate.month()
            self.apiPL.getUrlMonthly( year, month, self._responseFinished )
            if not self.response['isOk'] and self.response['errorCode'] == QNetworkReply.AuthenticationRequiredError:
                return {'isOk': False, 'message': 'Insufficent credentials for this key' }
            return {'isOk': True }

        self.currentProcess.emit('Add XYZ tiles mosaics')
        self.apiPL.access.isKill = False
        lstMissing = []
        vdate_ini = QDate( date1.year(),  date1.month(), 1 )
        vdate = QDate( date2.year(),  date2.month(), 1 )
        r = checkValidKey( vdate )
        if not r['isOk']:
            outFunction( r['message'] )
            return
        ltg = getGroup()
        ltg.setItemVisibilityChecked( False )
        while( vdate > vdate_ini.addMonths(-1) ):
            if self.apiPL.access.isKill:
                self.layerTreeRoot.removeChildNode( ltg )
                outFunction('Canceled by user')
                return
            year, month = vdate.year(), vdate.month()
            name = "{year}_{month:02d}".format( year=year, month=month )
            self.apiPL.getUrlMonthly( year, month, self._responseFinished )
            if not self.response['isOk']:
                lstMissing.append( name )
                continue
            self.message.emit( Qgis.Info, name, [] )
            addLayer( name, ltg )
            vdate = vdate.addMonths(-1)
        total = len( lstMissing )
        if total > 0:
            msg = "Missing mosaic(total {})".format( total )
            self.message.emit( Qgis.Critical, msg, lstMissing )
        else:
            self.message.emit( Qgis.Success, 'Finished OK', [] )
        self.changeButtonApply.emit('Add')

    @pyqtSlot(str, bool)
    def onLogin(self, password, hasRegister):
        self.currentProcess.emit('API key')
        self.apiPL.setKey( password, self._responseFinished )
        if not self.response['isOk']:
            self.message.emit( Qgis.Critical, self.response['message'], [] )
            return
        self.message.emit( Qgis.Info, 'Key is valid', [] )
        self.visiblePages.emit( True)
        if hasRegister:
            s = QSettings()
            s.setValue( self.localSetting.format('key'), password )

    @pyqtSlot(str)
    def onKey(self, optionKey):
        self.currentProcess.emit('API key')
        if optionKey == 'Copy clipboard':
            self.clipboard.setText( self.apiPL.validKey )
            self.message.emit( Qgis.Info, 'Copy key to clipboard', [] )

        elif optionKey == 'Clean register':
            s = QSettings()
            s.setValue( self.localSetting.format('key'), None )
            self.message.emit( Qgis.Info, 'Cleaned key register', [] )

    @pyqtSlot()
    def onCancel(self):
        self.killProcess.emit()

    @staticmethod
    def getHtmlTreeMetadata(value, html):
        if isinstance( value, dict ):
            html += "<ul>"
            for key, val in sorted( value.items() ):
                if not isinstance( val, dict ):
                    html += "<li>{key}: {value}</li> ".format(key=key, value=val)
                else:
                    html += "<li>{key}</li> ".format(key=key)
                html = API_PlanetLabs.getHtmlTreeMetadata( val, html )
            html += "</ul>"
            return html
        return html


class PopulateFeaturesCatalog(QObject):
    def __init__(self, layer, apiPL, requestBulkFeatures):
        super().__init__()
        self.provider = layer.dataProvider()
        self.apiPL = apiPL
        self.requestBulkFeatures = requestBulkFeatures
        self.response = None

    def _responseFinished(self, response):
        self.response = response

    def populate(self, params):
        """
        Populate layer from params['features']

        :params: { 'features', '_next'}
        """
        for item in params['features']:
            meta_json = item['properties']
            f =  { }
            f['item_type'] = item['item_type']
            f['item_id'] = item['item_id']
            f['date'] = item['date']
            f['meta_json'] = json.dumps( meta_json )
            f['meta_jsize'] = len( f['meta_json'] )
            atts = [ f[k] for k in self.apiPL.fields ]
            feat = QgsFeature()
            feat.setAttributes( atts )
            geom = item['geometry']
            if not geom is None:
                feat.setGeometry( geom )
            self.provider.addFeature( feat )
            del item

        del params['features']
        self.requestBulkFeatures.emit()
        self.apiPL.getUrlScenesUrl( params['_next'], self._responseFinished )
        if not self.response['isOk']:
            return
        if len( self.response['features'] ) == 0:
            return
        params = { 'features': self.response['features'], '_next': self.response['_links']['_next'] }
        self.populate( params)
