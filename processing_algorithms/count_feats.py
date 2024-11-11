from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFeatureSource


class count_feats(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource("INPUT", "INPUT", defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)
        results = {}
        outputs = {}

        INPUT = self.parameterAsVectorLayer(parameters, "INPUT", context)
        count = 0
        for f in INPUT.getFeatures():
            count += 1
        outputs["count"] = count
        return outputs

    def name(self):
        return "count_feats"

    def displayName(self):
        return "Count Features (no output)"

    def group(self):
        return "Geomeletitiki Help Scripts"

    def groupId(self):
        return "geomel_hydro"

    def createInstance(self):
        return count_feats()
