"""
Model exported as python.
Name : geomelMainB
Group : 
With QGIS : 33411
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsExpression
from qgis.core import QgsProject

import processing
import os
import ast


class Geomelmainb(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        basePath = QgsProject.instance().readPath("./")

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                "filled_dem", "Filled DEM", defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "discharge_point",
                "Discharge Point (MUST be in same, PROJECTED(m) CRS as DEM",
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "channel_network",
                "Channel Network",
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                # help="The channel network to be used for the analysis",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "BasinRaw",
                "Discharge Point Basin (raw)",
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                # help="The raw watershed of the discharge point (needed because GDAL cant handle tmp files)",
                defaultValue=os.path.join(basePath, "basin_raw.gpkg"),
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "UpslopeBasin",
                "Discharge Point Upslope Basin",
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=os.path.join(basePath, "upslope_basin.gpkg"),
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                "BasinDEM",
                "Basin DEM",
                createByDefault=True,
                defaultValue=os.path.join(basePath, "basin_dem.tif"),
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                "BasinContours",
                "Basin Contours",
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue=os.path.join(basePath, "basin_contours.gpkg"),
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "BasinChannelNetwork",
                "Basin Channel Network",
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=os.path.join(basePath, "basin_channel_network.gpkg"),
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "Basincn",
                "Basin CN (Polygons)",
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=os.path.join(basePath, "basin_cn.gpkg"),
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                "Basincorine",
                "Basin Corine Classes (Polygons)",
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=os.path.join(basePath, "basin_corine.gpkg"),
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                "Basinscs",
                "Basin SCS Classes (Polygons)",
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=os.path.join(basePath, "basin_scs.gpkg"),
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "SOIL_LAYER",
                "Soil Map",
                types=[QgsProcessing.TypeVectorAnyGeometry],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "LAND_COVER_LAYER",
                "Corine Land Cover",
                types=[QgsProcessing.TypeVectorAnyGeometry],
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        Pour_Point = self.parameterAsVectorLayer(parameters, "discharge_point", context)

        # Specify the Pour Point from the points layer
        pour_point = None
        for f in Pour_Point.getFeatures():
            pour_point = f

        # Get its name
        pour_point_name = (os.path.basename(Pour_Point.source()).split("|")[0]).split(
            "."
        )[0]

        x = pour_point.geometry().asPoint().x()
        y = pour_point.geometry().asPoint().y()

        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(8, model_feedback)
        results = {}
        outputs = {}

        # Upslope area
        alg_params = {
            "CONVERGE": 1.1,
            "ELEVATION": parameters["filled_dem"],
            "METHOD": 0,  # [0] Deterministic 8
            "MFD_CONTOUR": False,
            "SINKROUTE": None,
            "TARGET": None,
            "TARGET_PT_X": x,
            "TARGET_PT_Y": y,
            "AREA": "TEMPORARY_OUTPUT",  # parameters["DischargePointBasin"],
        }
        outputs["UpslopeArea"] = processing.run(
            "sagang:upslopearea",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["UpslopeArea"] = outputs["UpslopeArea"]["AREA"]

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Polygonize (raster to vector)
        alg_params = {
            "BAND": 1,
            "EIGHT_CONNECTEDNESS": False,
            "EXTRA": "",
            "FIELD": "DN",
            "INPUT": outputs["UpslopeArea"]["AREA"],
            "OUTPUT": parameters["BasinRaw"],
        }
        outputs["BasinRaw"] = processing.run(
            "gdal:polygonize",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Fix geometries
        alg_params = {
            "INPUT": outputs["BasinRaw"]["OUTPUT"],
            "METHOD": 1,  # Structure
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["FixGeometries"] = processing.run(
            "native:fixgeometries",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Dissolve
        alg_params = {
            "FIELD": ["DN"],
            "INPUT": outputs["FixGeometries"]["OUTPUT"],
            "SEPARATE_DISJOINT": False,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["Dissolve"] = processing.run(
            "native:dissolve",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # 5. Filter the watershed layer, keep only the needed watershed & attrs
        alg_params = {
            "Watershed": outputs["Dissolve"]["OUTPUT"],
            "pour_point": str(x) + "," + str(y),
            "Filtered_Watershed": parameters["UpslopeBasin"],
            "Area_Perimeter": "TEMPORARY_OUTPUT",
        }
        outputs["GeomeletitikiWatershedAttributes"] = processing.run(
            "geomel_watershed:geomelWAttributes",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["UpslopeBasin"] = outputs["GeomeletitikiWatershedAttributes"][
            "Filtered_Watershed"
        ]

        area_per = ast.literal_eval(
            outputs["GeomeletitikiWatershedAttributes"]["Area_Perimeter"]
        )
        area = area_per[0]
        perimeter = area_per[1]

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Clip the DEM to the watershed
        alg_params = {
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "DATA_TYPE": 0,  # Use Input Layer Data Type
            "EXTRA": "",
            "INPUT": parameters["filled_dem"],
            "KEEP_RESOLUTION": False,
            "MASK": outputs["GeomeletitikiWatershedAttributes"]["Filtered_Watershed"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "TARGET_EXTENT": None,
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["BasinDEM"] = processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["BasinDEM"] = outputs["BasinDEM"]["OUTPUT"]

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Contour lines
        alg_params = {
            "GRID": outputs["BasinDEM"]["OUTPUT"],
            "LINE_PARTS": True,
            "POLY_PARTS": False,
            "SCALE": 1,
            "VERTEX": 0,  # [0] x, y
            "ZMAX": 1000,
            "ZMIN": 0,
            "ZSTEP": 100,
            "CONTOUR": parameters["BasinContours"],
        }
        outputs["ContourLines"] = processing.run(
            "sagang:contourlines",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["BasinContours"] = outputs["ContourLines"]["CONTOUR"]

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            "INPUT": parameters["channel_network"],
            "OVERLAY": outputs["GeomeletitikiWatershedAttributes"][
                "Filtered_Watershed"
            ],
            "OUTPUT": parameters["BasinChannelNetwork"],
        }
        outputs["Clip"] = processing.run(
            "native:clip",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["BasinChannelNetwork"] = outputs["Clip"]["OUTPUT"]

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Geomeletitiki Watershed Stats
        alg_params = {
            "Area": area,
            "Clipped_DEM": outputs["BasinDEM"]["OUTPUT"],
            "Perimeter": perimeter,
            "Pour_Point_Name": os.path.basename(Pour_Point.source()).split(".")[
                0
            ],  # pour_point_name,
        }
        outputs["GeomeletitikiWatershedStats"] = processing.run(
            "geomel_watershed:geomelWatershedStats",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Geomeletitiki CN Calculator
        alg_params = {
            "Conditions": 1,  # Mean
            "Pour_Point_Name": os.path.basename(Pour_Point.source()).split(".")[
                0
            ],
            "Watershed": outputs["GeomeletitikiWatershedAttributes"][
                "Filtered_Watershed"
            ],
            "W_Corine": parameters["Basincorine"],
            "W_LandUseSCS": parameters["Basinscs"],
            "Watershed_CN": parameters["Basincn"],
            "SOIL_LAYER": parameters["SOIL_LAYER"],
            "LAND_COVER_LAYER": parameters["LAND_COVER_LAYER"],
        }
        outputs["GeomeletitikiCnCalculator"] = processing.run(
            "geomel_watershed:geomelCN",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["Basincn"] = outputs["GeomeletitikiCnCalculator"]["Watershed_CN"]
        results["Basincorine"] = outputs["GeomeletitikiCnCalculator"]["W_Corine"]
        results["Basinscs"] = outputs["GeomeletitikiCnCalculator"]["W_LandUseSCS"]

        return results

    def name(self):
        return "geomelMainB"

    def displayName(self):
        return "geomelMainB"

    def group(self):
        return 'Geomeletitiki Hydrology Analysis'

    def groupId(self):
        return 'geomel_hydro_main'

    def createInstance(self):
        return Geomelmainb()
