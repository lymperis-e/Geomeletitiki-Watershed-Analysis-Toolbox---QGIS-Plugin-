# -*- coding: utf-8 -*-

"""
/***************************************************************************
 geomelBasinAnalysis
                                 A QGIS plugin
 Complete watershed analysis toolbox.

                              -------------------
        begin                : 2021-02-16
        copyright            : (C) 2021 by Lymperis Efstathios / Geomeletitiki S.A.
        email                : geo.elymperis@gmail.com
 ***************************************************************************/

"""

__author__ = 'Lymperis Efstathios / Geomeletitiki S.A.'
__date__ = '2021-02-16'
__copyright__ = '(C) 2021 by Lymperis Efstathios / Geomeletitiki S.A.'

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .geomelWatershed_provider import geomelBasinAnalysisProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
import processing


class geomelBasinAnalysisPlugin(object):

    def __init__(self, iface):
        self.iface = iface
        self.settingsDialog = None
        self.PPointDialog = None
        self.provider = geomelBasinAnalysisProvider()

    def initGui(self):
        
        #Button 1
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon_1.png")
        self.geomel1 = QAction(icon, "1. Channel Network Analysis", self.iface.mainWindow())
        self.geomel1.triggered.connect(self.geomel1Dialog)
        self.geomel1.setCheckable(False)
        self.iface.addToolBarIcon(self.geomel1)

        #Add Pour Point Button
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon_target.png")
        self.openPPoint = QAction(icon, "Add a Pour Point", self.iface.mainWindow())
        self.openPPoint.triggered.connect(self.showPourPointDialog)
        self.openPPoint.setCheckable(False)
        self.iface.addToolBarIcon(self.openPPoint)


        #Button 2
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon_2.png")
        self.geomel2 = QAction(icon, "2. Watershed Basin CN Analysis", self.iface.mainWindow())
        self.geomel2.triggered.connect(self.geomel2Dialog)
        self.geomel2.setCheckable(False)
        self.iface.addToolBarIcon(self.geomel2)


        #Settings Dialog
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon_gear.png")
        self.openSettings = QAction(icon, "Select data folder (Geomeletitiki W.A.)", self.iface.mainWindow())
        self.openSettings.triggered.connect(self.showSettingsDialog)
        self.openSettings.setCheckable(False)
        self.iface.addToolBarIcon(self.openSettings)

        QgsApplication.processingRegistry().addProvider(self.provider)


    def geomel1Dialog(self):
        processing.execAlgorithmDialog('geomel_watershed:geomelMainA', {})

    def geomel2Dialog(self):
        processing.execAlgorithmDialog('geomel_watershed:geomelMainB', {})

    def showSettingsDialog(self):
        if not self.settingsDialog:
            from .Data_Settings_Dialog import DataSettingsDialog
            self.settingsDialog = DataSettingsDialog(self.iface)
        self.settingsDialog.show()


    def showPourPointDialog(self):
        if not self.PPointDialog:
            from .Add_PPoint_Dialog import AddPPointDialog
            self.PPointDialog = AddPPointDialog(self.iface)
        self.PPointDialog.show()




    def unload(self):
        try:
            self.iface.removeToolBarIcon(self.geomel1)
            self.iface.removeToolBarIcon(self.geomel2)
            self.iface.removeToolBarIcon(self.openSettings)
            self.iface.removeToolBarIcon(self.openPPoint)
            QgsApplication.processingRegistry().removeProvider(self.provider)
        except:
            pass 
    
