from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsField,
    QgsPointXY,
    QgsFeature,
    QgsProcessingParameterPoint,
    QgsProcessingOutputString,
    QgsFeatureSink,
    QgsFeatureRequest,
    QgsFields,
    QgsField,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
)


class WatershedAttributes(QgsProcessingAlgorithm):
    INPUT = "Watershed"
    OUTPUT = "Filtered_Watershed"
    AreaPer = "Area_Perimeter"

    def __init__(self):
        super().__init__()

    def name(self):
        return "watershed_attributes"

    def tr(self, text):
        return QCoreApplication.translate("watershed_attributes", text)

    def displayName(self):
        return self.tr("Watershed Attributes")

    def group(self):
        return self.tr("submodules")

    def groupId(self):
        return "submodules"

    def shortHelpString(self):
        return self.tr(
            "Watershed Attributes: delete the [EPSG:2100] part of the point definition"
        )

    def createInstance(self):
        return type(self)()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorAnyGeometry],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer"),
                QgsProcessing.TypeVectorAnyGeometry,
            )
        )
        self.addParameter(
            QgsProcessingParameterPoint("pour_point", self.tr("pour_point"))
        )
        self.addOutput(
            QgsProcessingOutputString(self.AreaPer, self.tr("Area_Perimeter"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        # Define output features
        outFields = QgsFields()
        outFields.append(QgsField("Area (sq. Km)", QVariant.Double))
        outFields.append(QgsField("Perimeter (Km)", QVariant.Double))
        # Get the features from the source layer for filtering
        source = self.parameterAsSource(parameters, self.INPUT, context)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            outFields,
            source.wkbType(),
            source.sourceCrs(),
        )
        # Get the pourpoint as a point
        p = parameters["pour_point"].split(",")
        pourpoint = QgsPointXY(float(p[0]), float(p[1]))
        # Filter
        area = None
        perimeter = None
        area_per = None
        features = source.getFeatures(QgsFeatureRequest())
        for feat in features:
            area = (feat.geometry().area()) / 1000000
            perimeter = (feat.geometry().length()) / 1000
            out_feat = QgsFeature(outFields)
            out_feat.setGeometry(feat.geometry())
            if feat.geometry().contains(pourpoint):
                area = (feat.geometry().area()) / 1000000
                perimeter = (feat.geometry().length()) / 1000
                area_per = "[{}, {}]".format(area, perimeter)
                out_feat["Area (sq. Km)"] = area
                out_feat["Perimeter (Km)"] = perimeter
                sink.addFeature(out_feat, QgsFeatureSink.FastInsert)
            else:
                None

        return {self.OUTPUT: dest_id, self.AreaPer: area_per}
