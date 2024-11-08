"""
Model exported as python.
Name : geomelMainA
Group : geomel_hydro_main
With QGIS : 33411
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterVectorDestination
import processing


class Geomelmaina(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('dem', 'DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('channel_initiation_threshold', 'Channel_Initiation_Threshold', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=40000))
        self.addParameter(QgsProcessingParameterRasterDestination('Channel_network_raster', 'Channel_Network_Raster', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('Channel_network_vector', 'Channel_Network_Vector', type=QgsProcessing.TypeVectorLine, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Filled_dem', 'Filled_DEM', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Flow_direction', 'Flow_Direction', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # Fill sinks (wang & liu)
        alg_params = {
            'ELEV': parameters['dem'],
            'MINSLOPE': 0.01,
            'WSHED': 'TEMPORARY_OUTPUT',
            'FDIR': parameters['Flow_direction'],
            'FILLED': parameters['Filled_dem'],
            'WSHED': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FillSinksWangLiu'] = processing.run('sagang:fillsinkswangliu', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Filled_dem'] = outputs['FillSinksWangLiu']['FILLED']
        results['Flow_direction'] = outputs['FillSinksWangLiu']['FDIR']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Catchment area
        alg_params = {
            'ACCU_LEFT': 'TEMPORARY_OUTPUT',
            'ACCU_MATERIAL': None,
            'ACCU_RIGHT': 'TEMPORARY_OUTPUT',
            'ACCU_TARGET': outputs['FillSinksWangLiu']['FILLED'],
            'ACCU_TOTAL': 'TEMPORARY_OUTPUT',
            'CONVERGENCE': 1.1,
            'ELEVATION': outputs['FillSinksWangLiu']['FILLED'],
            'FLOW': 'TEMPORARY_OUTPUT',
            'FLOW_LENGTH': 'TEMPORARY_OUTPUT',
            'FLOW_UNIT': 1,  # [1] cell area
            'LINEAR_DIR': None,
            'LINEAR_DO': False,
            'LINEAR_MIN': 500,
            'LINEAR_VAL': None,
            'METHOD': 0,  # [0] Deterministic 8
            'MFD_CONTOUR': False,
            'NO_NEGATIVES': True,
            'SINKROUTE': None,
            'STEP': 1,
            'VAL_INPUT': None,
            'VAL_MEAN': 'TEMPORARY_OUTPUT',
            'WEIGHTS': None,
            'WEIGHT_LOSS': 'TEMPORARY_OUTPUT',
            'FLOW': QgsProcessing.TEMPORARY_OUTPUT,
            'VAL_MEAN': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CatchmentArea'] = processing.run('sagang:catchmentarea', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Channel network
        alg_params = {
            'DIV_CELLS': 5,
            'DIV_GRID': None,
            'ELEVATION': outputs['FillSinksWangLiu']['FILLED'],
            'INIT_GRID': outputs['CatchmentArea']['FLOW'],
            'INIT_METHOD': 2,  # [2] Greater than
            'INIT_VALUE': parameters['channel_initiation_threshold'],
            'MINLEN': 1,
            'SINKROUTE': None,
            'TRACE_WEIGHT': None,
            'CHNLNTWRK': parameters['Channel_network_raster'],
            'CHNLROUTE': QgsProcessing.TEMPORARY_OUTPUT,
            'SHAPES': parameters['Channel_network_vector']
        }
        outputs['ChannelNetwork'] = processing.run('sagang:channelnetwork', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Channel_network_raster'] = outputs['ChannelNetwork']['CHNLNTWRK']
        results['Channel_network_vector'] = outputs['ChannelNetwork']['SHAPES']
        return results

    def name(self):
        return 'geomelMainA'

    def displayName(self):
        return 'geomelMainA'

    def group(self):
        return 'geomel_hydro_main'

    def groupId(self):
        return ''

    def createInstance(self):
        return Geomelmaina()
