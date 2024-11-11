from collections import defaultdict
import math
import os
from datetime import datetime
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsRasterBandStats,
    QgsProcessingOutputString,
    QgsProcessingAlgorithm,
)
from qgis.core import QgsProject

try:
    from qgis import processing
except:
    import processing


class geomelStatisticsStandalone(QgsProcessingAlgorithm):
    """
    Calculate a watershed's stats
    """

    Filled_DEM = "Filled_DEM"
    Watershed_Basin = "Watershed_Basin"
    OUTPUT = "Watershed_Stats"
    Pour_Point_Name = "Pour_Point_Name"
    Clipped_DEM = "Clipped_DEM"

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return geomelStatisticsStandalone()

    def name(self):
        return "geomelStatisticsStandalone"

    def displayName(self):
        return self.tr("Geomeletitiki Statistics Module (stand-alone)")

    def group(self):
        return self.tr("Geomeletitiki Help Scripts")

    def groupId(self):
        return "geomel_hydro"

    def shortHelpString(self):
        return self.tr("Geomeletitiki Watershed Statistics Calculator")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.Filled_DEM, self.tr("Filled DEM"))
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.Watershed_Basin, self.tr("Watershed Basin")
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.Pour_Point_Name, self.tr("Pour Point Name"), optional=True
            )
        )

        self.addOutput(
            QgsProcessingOutputString(self.OUTPUT, self.tr("Watershed stats"))
        )

    def processAlgorithm(self, parameters, context, feedback):

        pp_name = self.parameterAsString(parameters, self.Pour_Point_Name, context)
        # Open the log file
        path_absolute = QgsProject.instance().readPath("./")
        path = "/Statistics_Log_{}_{}".format(pp_name, datetime.now())
        path = path.replace(":", "_")
        path = path[:-7]
        path = path_absolute + path + ".txt"

        log = open(path, "w")

        Filled_DEM = self.parameterAsRasterLayer(parameters, self.Filled_DEM, context)
        Watershed_Basin = self.parameterAsVectorLayer(
            parameters, self.Watershed_Basin, context
        )

        # 1. Get area and perimeter of the basin, from the vector polygon
        for f in Watershed_Basin.getFeatures():
            WB = f
        area = (f.geometry().area()) / 1000000
        perimeter = (f.geometry().length()) / 1000

        # 1. Clip DEM

        Clipped_DEM = processing.run(
            "gdal:cliprasterbymasklayer",
            {
                "ALPHA_BAND": False,
                "CROP_TO_CUTLINE": True,
                "DATA_TYPE": 0,
                "EXTRA": "",
                "INPUT": Filled_DEM,
                "KEEP_RESOLUTION": False,
                "MASK": Watershed_Basin,
                "MULTITHREADING": False,
                "NODATA": None,
                "OPTIONS": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
                "SET_RESOLUTION": False,
                "SOURCE_CRS": None,
                "TARGET_CRS": None,
                "X_RESOLUTION": None,
                "Y_RESOLUTION": None,
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        if feedback.isCanceled():
            return {}

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.Clipped_DEM, self.tr("Clipped DEM"), defaultValue=Clipped_DEM
            )
        )

        Clipped = self.parameterAsRasterLayer(parameters, "Clipped_DEM", context)

        basin_provider = Clipped.dataProvider()
        stats = basin_provider.bandStatistics(1, QgsRasterBandStats.All)
        min = stats.minimumValue
        max = stats.maximumValue
        mean = stats.mean
        klisi = (max - min) * 0.001 / math.sqrt(area)
        RC = (4 * 3.1415 * area) / (perimeter**2)
        CC = (0.282 * perimeter) / math.sqrt(area)

        output = defaultdict()

        output["min"] = min
        output["max"] = max
        output["mean"] = mean
        output["klisi"] = klisi
        output["RC"] = RC
        output["CC"] = CC

        log.write("Ελάχιστο Υψόμετρο: " + str(min) + "m" + "\n")
        log.write("Μέγιστο Υψόμετρο: " + str(max) + "m" + "\n")
        log.write("Μέσο Υψόμετρο: " + str(mean) + "m" + "\n")
        log.write("Περίμετρος: " + str(perimeter) + "Km" + "\n")
        log.write("Εμβαδό: " + str(area) + "Km2" + "\n")
        log.write("Μέση Κλίση Υδρολογικής Λεκάνης: " + str(klisi) + "\n")
        log.write("Δείκτης Κυκλικότητας (Rc): " + str(RC) + "\n")
        log.write("Δείκτης Συμπαγούς (Cc): " + str(CC) + "\n")

        del basin_provider
        del Clipped_DEM

        # Return the results
        return {self.OUTPUT: "{" + str(output).split("{")[1].split("}")[0]}
