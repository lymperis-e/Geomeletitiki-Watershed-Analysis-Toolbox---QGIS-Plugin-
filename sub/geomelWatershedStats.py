from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingOutputNumber,
                       QgsProcessingParameterRasterLayer,QgsProcessingParameterNumber,
                       QgsVectorLayer,QgsRasterLayer,QgsRasterBandStats,
                       QgsVectorDataProvider, QgsProcessingFeatureSourceDefinition, QgsFeatureRequest,QgsProcessingOutputString,
                       QgsFeature, QgsFeatureSink, QgsFeatureRequest, QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink)
from qgis.core import QgsFields, QgsField, QgsProject
from qgis import processing
from PyQt5.QtCore import QVariant
from collections import defaultdict
import math
import os
from datetime import datetime


class geomelWatershedStats(QgsProcessingAlgorithm):
    """
    Calculate a watershed's stats
    """
    INPUT = 'Clipped_DEM'
    OUTPUT = 'Watershed_Stats'
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)
    def createInstance(self):
        # Must return a new copy of your algorithm.
        return geomelWatershedStats()
    def name(self):
        return 'geomelWatershedStats'
    def displayName(self):
        return self.tr('Geomeletitiki Watershed Stats')
    def group(self):
        return self.tr('Geomeletitiki Help Scripts')
    def groupId(self):
        return 'geomel_hydro'
    def shortHelpString(self):
        return self.tr('Geomeletitiki CN Calculator')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Clipped DEM')
            )
        )
        
        param_area = QgsProcessingParameterNumber('Area', self.tr('Area'), type=QgsProcessingParameterNumber.Double, optional=True)
        param_area.setMetadata( {'widget_wrapper':{ 'decimals': 4 }})
        self.addParameter(param_area)
        
        param_perimeter = QgsProcessingParameterNumber('Perimeter', self.tr('Perimeter'), type=QgsProcessingParameterNumber.Double, optional=True)
        param_area.setMetadata( {'widget_wrapper':{ 'decimals': 4 }})
        self.addParameter(param_perimeter)

        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT,
                self.tr('Watershed stats')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        # Open the log file
        path_absolute = QgsProject.instance().readPath("./")
        path = "/Basin_Stats_Log_{}".format(datetime.now())
        path = path.replace(":", "_")
        path = path[:-7]
        path = path_absolute + path +".txt"

        log = open(path, "w")
        

        basin = self.parameterAsRasterLayer(parameters, self.INPUT ,context)
        area = self.parameterAsDouble(parameters, 'Area', context)
        perimeter = self.parameterAsDouble(parameters, 'Perimeter', context)

        basin_provider=basin.dataProvider()
        stats = basin_provider.bandStatistics(1, QgsRasterBandStats.All)
        min = stats.minimumValue
        max = stats.maximumValue
        mean = stats.mean
        klisi = (max-min)/area
        RC = (4*3.1415*area)/(perimeter**2)
        CC = (0.282*perimeter)/math.sqrt(area)


        output = defaultdict()

        output['min'] = min
        output['max'] = max
        output['mean'] = mean
        output['klisi'] = klisi
        output['RC'] = RC
        output['CC'] = CC


        log.write("Ελάχιστο Υψόμετρο: " + str(min)+"m"+"\n")
        log.write("Μέγιστο Υψόμετρο: " + str(max)+"m"+"\n")
        log.write("Μέσο Υψόμετρο: " + str(mean)+ "m"+"\n")
        log.write("Περίμετρος: " + str(perimeter) +"Km" +"\n")
        log.write("Μέση Κλίση Υδρολογικής Λεκάνης: " + str(klisi) +"\n" )
        log.write("Δείκτης Κυκλικότητα (Rc): "+ str(RC)+ "\n")
        log.write("Δείκτης Συμπαγούς (Cc): "+ str(CC)+ "\n")

        del basin_provider
        del basin
      
        # Return the results
        return {
            self.OUTPUT: '{' + str(output).split('{')[1].split('}')[0]
        }