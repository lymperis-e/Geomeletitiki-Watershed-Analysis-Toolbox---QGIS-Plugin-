from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsFeature,
)
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant

try:
    import processing
except:
    from qgis import processing


class Rename_Output(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "INPUT",
                "INPUT",
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT",
                "Longest_Flow_Path",
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue=None,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        outFields = QgsFields()
        outFields.append(QgsField("Network Cost", QVariant.Double, len=20, prec=5))
        outFields.append(QgsField("Stream Length (m)", QVariant.Double, len=20, prec=5))

        source = self.parameterAsVectorLayer(parameters, "INPUT", context)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            "OUTPUT",
            context,
            outFields,
            source.wkbType(),
            source.sourceCrs(),
        )
        features = source.getFeatures()
        for _, feature in enumerate(features):

            out_feat = QgsFeature(outFields)
            out_feat.setGeometry(feature.geometry())
            out_feat["Network Cost"] = feature["cost"]
            out_feat["Stream Length (m)"] = out_feat.geometry().length()
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

        results = {"OUTPUT": dest_id}
        return results

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)

    def name(self):
        return "rename_output"

    def createInstance(self):
        return Rename_Output()

    def displayName(self):
        return self.tr("Rename Layer")

    def group(self):
        return self.tr("submodules")

    def groupId(self):
        return "submodules"

    def shortHelpString(self):
        return self.tr("Rename Layer")
