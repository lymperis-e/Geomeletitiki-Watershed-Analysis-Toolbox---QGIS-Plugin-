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

pluginPath = os.path.dirname(__file__)
sys.path.append(os.path.join(pluginPath, "processing", "core"))
sys.path.append(os.path.join(pluginPath, "processing", "submodules"))

from qgis.core import QgsProcessingProvider


# Main algs
from step_1 import WATStep1
from step_2 import WATStep2
from longest_flow_path import LongestFlowPath
from idf_curves import IdfCurves


from watershed_cn import WatershedCN
from watershed_statistics import WatershedStatistics
from watershed_attributes import WatershedAttributes
from watershed_stats_standalone import WatershedStatisticsStandalone


from elongation_ratio import ElongationRatio
from count_feats import FeatureCounter
from nearby_meteo_stations import NearbyMeteoStations
from inverse_dist_gage_weighting import InverseDistGageWeighting


from qgis.PyQt.QtGui import QIcon


class WATProcessingProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(WATStep1())
        self.addAlgorithm(WATStep2())
        self.addAlgorithm(WatershedCN())
        self.addAlgorithm(WatershedStatistics())
        self.addAlgorithm(WatershedAttributes())
        self.addAlgorithm(WatershedStatisticsStandalone())
        self.addAlgorithm(LongestFlowPath())
        self.addAlgorithm(ElongationRatio())
        self.addAlgorithm(FeatureCounter())
        self.addAlgorithm(NearbyMeteoStations())
        self.addAlgorithm(InverseDistGageWeighting())
        self.addAlgorithm(IdfCurves())

    def id(self):
        return "gwat"

    def name(self):
        return self.tr("GWAT - Geomeletitiki Watershed Analysis Toolbox ")

    def icon(self):
        return QIcon(os.path.join(pluginPath, "assets", "icons", "icon.png"))

    def longName(self):
        return self.name()
