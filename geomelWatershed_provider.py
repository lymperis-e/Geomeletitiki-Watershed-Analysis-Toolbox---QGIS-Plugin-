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
pluginPath = os.path.dirname(__file__)
sys.path.append(os.path.join(pluginPath, "main"))
sys.path.append(os.path.join(pluginPath, "sub"))

from qgis.core import QgsProcessingProvider
from geomelMainA import geomelMainA
from geomelMainB import geomelMainB
from geomelCN import geomelCN
from geomelWatershedStats import geomelWatershedStats
from geomelWAttributes import geomelWAttributes

from qgis.PyQt.QtGui import QIcon




class geomelBasinAnalysisProvider(QgsProcessingProvider):
    
   

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(geomelMainA())
        self.addAlgorithm(geomelMainB())
        self.addAlgorithm(geomelCN())
        self.addAlgorithm(geomelWatershedStats())
        self.addAlgorithm(geomelWAttributes())

    def id(self):
        return 'geomel_watershed'

    def name(self):
        return self.tr('Geomeletitiki Watershed Analysis Toolbox')

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "icon.png"))


    def longName(self):
        return self.name()
