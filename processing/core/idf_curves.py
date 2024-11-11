from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
import processing
from qgis.PyQt.QtCore import QCoreApplication


class IdfCurves(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Basin",
                "Basin",
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "NumberofStations",
                "Number of Stations",
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                defaultValue=4,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "ReturnPeriodTinyears",
                "Return Period (T, in years)",
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                defaultValue=50,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "RainfallDurationdinhours",
                "Rainfall Duration (d, in hours)",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.1,
                defaultValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "NearestStationsWithIdgw",
                "Nearest Stations with IDGW",
                type=QgsProcessing.TypeVectorPoint,
                createByDefault=True,
                defaultValue=None,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feedback = QgsProcessingMultiStepFeedback(2, feedback)
        results = {}
        outputs = {}

        # IDGW 1: Locate Nearest Meteo Stations
        alg_params = {
            "Basin": parameters["Basin"],
            "Number_of_Stations": parameters["NumberofStations"],
            "NearestStations": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["Idgw1LocateNearestMeteoStations"] = processing.run(
            "gwat:nearby_meteo_stations",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # IDGW 2: Inverse Distance Gage Weighting
        alg_params = {
            "INPUT": outputs["Idgw1LocateNearestMeteoStations"]["NearestStations"],
            "RainfallDuration": parameters["RainfallDurationdinhours"],
            "ReturnPeriod": parameters["ReturnPeriodTinyears"],
            "OUTPUT": parameters["NearestStationsWithIdgw"],
        }
        outputs["Idgw2InverseDistanceGageWeighting"] = processing.run(
            "gwat:inverse_dist_gauge_weighting",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["NearestStationsWithIdgw"] = outputs[
            "Idgw2InverseDistanceGageWeighting"
        ]["OUTPUT"]
        return results

    def name(self):
        return "idf_curves"

    def displayName(self):
        return "4. IDF Curves via Inverse Distance Gauge Weighting Full"

    def group(self):
        return "core"

    def groupId(self):
        return "core"

    def createInstance(self):
        return IdfCurves()

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr(
            "Using the dataset of the Greek Meteo stations network, this algorithm calculates the input parameters for IDF Curve creation,  for the stations nearest to the basin \n\n\n\n\nDeveloped by E. Lymperis\n2021, Geomeletitiki S.A."
        )

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)
