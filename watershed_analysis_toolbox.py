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

__author__ = "Lymperis Efstathios / Geomeletitiki S.A."
__date__ = "2021-02-16"
__copyright__ = "(C) 2021 by Lymperis Efstathios / Geomeletitiki S.A."

__revision__ = "$Format:%H$"

import os
import sys
import inspect

from qgis.core import QgsApplication

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
import processing

from .processing_provider import WATProcessingProvider
from .utils.wfs import add_wfs_layers


class WatershedAnalysisToolbox(object):

    def __init__(self, iface):
        self.iface = iface
        self.settingsDialog = None
        self.PPointDialog = None
        self.provider = WATProcessingProvider()

    def initGui(self):

        # Button 1
        icon = QIcon(os.path.dirname(__file__) + "/assets/icons/icon_1.png")
        self.step1 = QAction(
            icon, "1. Filled DEM & Channel Network", self.iface.mainWindow()
        )
        self.step1.triggered.connect(self.openStep1)
        self.step1.setCheckable(False)
        self.iface.addToolBarIcon(self.step1)

        # Add Pour Point Button
        icon = QIcon(os.path.dirname(__file__) + "/assets/icons/icon_target.png")
        self.openPPoint = QAction(
            icon, "Add a Discharge Point", self.iface.mainWindow()
        )
        self.openPPoint.triggered.connect(self.openPourPointDialog)
        self.openPPoint.setCheckable(False)
        self.iface.addToolBarIcon(self.openPPoint)

        # Button 2
        icon = QIcon(os.path.dirname(__file__) + "/assets/icons/icon_2.png")
        self.step2 = QAction(
            icon,
            "2. Watershed, Contours, Land Cover & Curve Number",
            self.iface.mainWindow(),
        )
        self.step2.triggered.connect(self.openStep2)
        self.step2.setCheckable(False)
        self.iface.addToolBarIcon(self.step2)

        # Button 3: Longest Flow Path
        icon = QIcon(os.path.dirname(__file__) + "/assets/icons/icon_3.png")
        self.step3 = QAction(icon, "3. Longest Flow Path", self.iface.mainWindow())
        self.step3.triggered.connect(self.openStep3)
        self.step3.setCheckable(False)
        self.iface.addToolBarIcon(self.step3)

        # Button 4: Inverse Distance Gauge Weighting
        icon = QIcon(os.path.dirname(__file__) + "/assets/icons/icon_4.png")
        self.step4 = QAction(
            icon,
            "4. IDF Curves via Inverse Distance Gauge Weighting Full",
            self.iface.mainWindow(),
        )
        self.step4.triggered.connect(self.openStep4)
        self.step4.setCheckable(False)
        self.iface.addToolBarIcon(self.step4)

        # Settings Dialog
        icon = QIcon(os.path.dirname(__file__) + "/assets/icons/icon_gear.png")
        # self.openSettings = QAction(
        #     icon, "Select data folder (Geomeletitiki W.A.)", self.iface.mainWindow()
        # )
        # self.openSettings.triggered.connect(self.showSettingsDialog)
        # self.openSettings.setCheckable(False)
        # self.iface.addToolBarIcon(self.openSettings)

        QgsApplication.processingRegistry().addProvider(self.provider)

    def openStep1(self):
        processing.execAlgorithmDialog("gwat:step_1", {})

    def openStep2(self):
        # Add Corine & SCS layers
        land_cover_layer, soil_layer = add_wfs_layers(self.iface)
        if land_cover_layer and soil_layer:
            processing.execAlgorithmDialog(
                "gwat:step_2",
                {"SOIL_LAYER": soil_layer, "LAND_COVER_LAYER": land_cover_layer},
            )

    def openStep3(self):
        processing.execAlgorithmDialog("gwat:longest_flow_path", {})

    def openStep4(self):
        processing.execAlgorithmDialog("gwat:idf_curves", {})

    # def showSettingsDialog(self):
    #     if not self.settingsDialog:
    #         from .dialogs.Data_Settings_Dialog import DataSettingsDialog

    #         self.settingsDialog = DataSettingsDialog(self.iface)
    #     self.settingsDialog.show()

    def openPourPointDialog(self):
        if not self.PPointDialog:
            from .ui.pour_point_dialog import AddPourPointDialog

            self.PPointDialog = AddPourPointDialog(self.iface)
        self.PPointDialog.show()

    def unload(self):
        try:
            self.iface.removeToolBarIcon(self.step1)
            self.iface.removeToolBarIcon(self.step2)
            self.iface.removeToolBarIcon(self.step3)
            self.iface.removeToolBarIcon(self.step4)
            # self.iface.removeToolBarIcon(self.openSettings)
            self.iface.removeToolBarIcon(self.openPPoint)
            QgsApplication.processingRegistry().removeProvider(self.provider)
        except Exception:
            pass
