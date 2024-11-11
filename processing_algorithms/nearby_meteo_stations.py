from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression, QgsProcessingParameterNumber

try:
    from qgis import processing
except:
    import processing
import os

currentPath = os.path.dirname(__file__)
basePath = os.path.dirname(currentPath)

from geomelwatershed.utils.settings import meteo_stations_path


class NearbyMeteoStations(QgsProcessingAlgorithm):

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return NearbyMeteoStations()

    def name(self):
        return "nearby_meteo_stations"

    def displayName(self):
        return self.tr("IDF 1: Locate Nearest Meteo Stations")

    def group(self):
        return self.tr("Geomeletitiki Help Scripts")

    def groupId(self):
        return "geomel_hydro"

    def shortHelpString(self):
        return self.tr(
            "Locate the 4 meteo stations nearest to the centroid of the basin"
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Basin",
                "Basin",
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        # self.addParameter(QgsProcessingParameterVectorLayer('Stations', 'Stations', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(
            QgsProcessingParameterNumber(
                "Number_of_Stations",
                "Number of Stations ",
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                defaultValue=4,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "NearestStations",
                "Nearest Stations",
                optional=True,
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=None,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        meteo_path = meteo_stations_path()

        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}

        # Centroids
        alg_params = {
            "ALL_PARTS": False,
            "INPUT": parameters["Basin"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["Centroids"] = processing.run(
            "native:centroids",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Add Index to the Basin
        alg_params = {
            "FIELD_NAME": "Fid",
            "GROUP_FIELDS": [""],
            "INPUT": outputs["Centroids"]["OUTPUT"],
            "SORT_ASCENDING": True,
            "SORT_EXPRESSION": "",
            "SORT_NULLS_FIRST": False,
            "START": 0,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["AddAutoincrementalField"] = processing.run(
            "native:addautoincrementalfield",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Distance matrix
        alg_params = {
            "INPUT": outputs["AddAutoincrementalField"]["OUTPUT"],
            "INPUT_FIELD": QgsExpression("'Fid'").evaluate(),
            "MATRIX_TYPE": 0,
            "NEAREST_POINTS": parameters["Number_of_Stations"],
            "TARGET": meteo_path,
            "TARGET_FIELD": QgsExpression("'fid'").evaluate(),
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["DistanceMatrix"] = processing.run(
            "qgis:distancematrix",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Extract by location
        alg_params = {
            "INPUT": meteo_path,
            "INTERSECT": outputs["DistanceMatrix"]["OUTPUT"],
            "PREDICATE": [0],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ExtractByLocation"] = processing.run(
            "native:extractbylocation",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Join attributes by location
        alg_params = {
            "DISCARD_NONMATCHING": False,
            "INPUT": outputs["ExtractByLocation"]["OUTPUT"],
            "JOIN": outputs["DistanceMatrix"]["OUTPUT"],
            "JOIN_FIELDS": [""],
            "METHOD": 1,
            "PREDICATE": [0],
            "PREFIX": "",
            "OUTPUT": parameters["NearestStations"],
        }

        outputs["JoinAttributesByLocation"] = processing.run(
            "native:joinattributesbylocation",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["NearestStations"] = outputs["JoinAttributesByLocation"]["OUTPUT"]

        return results
