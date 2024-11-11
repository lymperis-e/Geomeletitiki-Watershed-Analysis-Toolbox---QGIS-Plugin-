import os
import math
from collections import defaultdict
from datetime import datetime

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsRasterBandStats,
    QgsProcessingOutputString,
    QgsProcessingAlgorithm,
)
from gwat.utils.files import get_plugin_output_dir, get_or_create_path


class WatershedStatistics(QgsProcessingAlgorithm):
    """
    Calculate a watershed's stats
    """

    INPUT = "Clipped_DEM"
    OUTPUT = "Watershed_Stats"
    Pour_Point_Name = "Pour_Point_Name"

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return WatershedStatistics()

    def name(self):
        return "watershed_statistics"

    def displayName(self):
        return self.tr("Watershed Statιstics")

    def group(self):
        return self.tr("submodules")

    def groupId(self):
        return "submodules"

    def shortHelpString(self):
        return self.tr("Watershed Curve Numbers")

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT, self.tr("Clipped DEM"))
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.Pour_Point_Name, self.tr("Pour Point Name"), optional=True
            )
        )

        param_area = QgsProcessingParameterNumber(
            "Area",
            self.tr("Area"),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
        )
        param_area.setMetadata({"widget_wrapper": {"decimals": 4}})
        self.addParameter(param_area)

        param_perimeter = QgsProcessingParameterNumber(
            "Perimeter",
            self.tr("Perimeter"),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
        )
        param_area.setMetadata({"widget_wrapper": {"decimals": 4}})
        self.addParameter(param_perimeter)

        self.addOutput(
            QgsProcessingOutputString(self.OUTPUT, self.tr("Watershed stats"))
        )

    def processAlgorithm(self, parameters, context, feedback):

        pp_name = self.parameterAsString(parameters, self.Pour_Point_Name, context)

        # Check if the point name contains the crs etc... And throw them away
        pp_name = pp_name.split("?")[0]
        print(f"Pour Point: {pp_name}")

        logs_dir = get_or_create_path(os.path.join(get_plugin_output_dir(), "step_2"))

        path = f"/basin_statistics_{pp_name}_{datetime.now()}"

        if "?" in path:
            path = path.split("?")[0]

        print(f"Path: {path}")

        path = path.replace(":", "_")
        path = path[:-7]
        path = logs_dir + path + ".txt"

        with open(path, "w", encoding="utf-8") as log:

            basin = self.parameterAsRasterLayer(parameters, self.INPUT, context)
            area = self.parameterAsDouble(parameters, "Area", context)
            perimeter = self.parameterAsDouble(parameters, "Perimeter", context)

            basin_provider = basin.dataProvider()
            stats = basin_provider.bandStatistics(1, QgsRasterBandStats.All)
            min_elev = stats.minimumValue
            max_elev = stats.maximumValue
            mean = stats.mean
            klisi = (max_elev - min_elev) * 0.001 / math.sqrt(area)
            circularity_ratio = (4 * 3.1415 * area) / (perimeter**2)
            compactness_coefficient = (0.282 * perimeter) / math.sqrt(area)

            output = defaultdict()

            output["min"] = min_elev
            output["max"] = max_elev
            output["mean"] = mean
            output["klisi"] = klisi
            output["RC"] = circularity_ratio
            output["CC"] = compactness_coefficient

            log.write("Ελάχιστο Υψόμετρο: " + str(min_elev) + "m" + "\n")
            log.write("Μέγιστο Υψόμετρο: " + str(max_elev) + "m" + "\n")
            log.write("Μέσο Υψόμετρο: " + str(mean) + "m" + "\n")
            log.write("Περίμετρος: " + str(perimeter) + "Km" + "\n")
            log.write("Εμβαδό: " + str(area) + "Km2" + "\n")
            log.write("Μέση Κλίση Υδρολογικής Λεκάνης: " + str(klisi) + "\n")
            log.write("Δείκτης Κυκλικότητας (Rc): " + str(circularity_ratio) + "\n")
            log.write("Δείκτης Συμπαγούς (Cc): " + str(compactness_coefficient) + "\n")

            del basin_provider
            del basin

        # Return the results
        return {self.OUTPUT: "{" + str(output).split("{")[1].split("}")[0]}
