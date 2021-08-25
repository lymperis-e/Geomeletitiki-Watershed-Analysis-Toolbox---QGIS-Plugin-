from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterFeatureSink, QgsProcessingFeatureSourceDefinition

from PyQt5.QtCore import QCoreApplication

try:
    import processing
except:
    from qgis import processing
   
 

class geomelLongestFlowPath(QgsProcessingAlgorithm):


    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('ChannelNetwork', 'Channel Network', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('PourPoint', 'Discharge Point', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('PourPointIDField', 'Pour Point ID Field', type=QgsProcessingParameterField.Numeric, parentLayerParameterName='PourPoint', allowMultiple=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterVectorLayer('WatershedBasin', 'Watershed Basin', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Longest_Stream','Longest_Stream' , type=QgsProcessing.TypeVectorLine, createByDefault=True, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the whole algorithm
        feedback = QgsProcessingMultiStepFeedback(7, model_feedback)
        results = {}
        outputs = {}

        # 1. Select the Channels/Streams that fall within the basin basin
        #    that is being examined
        alg_params = {
            'INPUT': parameters['ChannelNetwork'],
            'INTERSECT': parameters['WatershedBasin'],
            'METHOD': 0,
            'PREDICATE': [0,6]
        }
        outputs['SelectChannelsWithinBasin'] = processing.run('native:selectbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # 2. Extract the first vertex of each line feature representing a
        #    stream channel.
        #    TODO: Rather than extracting all these vertices, calculate only the Springs & Junctions of the network
        alg_params = {
            'INPUT': QgsProcessingFeatureSourceDefinition(parameters['ChannelNetwork'], selectedFeaturesOnly=True, featureLimit=-1),
            'VERTICES': '0',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractFirstVertices'] = processing.run('native:extractspecificvertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # 3. Create spatial index for the previously extracted vertices, to gain performance
        #    benefit when calculating distances
        alg_params = {
            'INPUT': outputs['ExtractFirstVertices']['OUTPUT']
        }
        outputs['CreateSpatialIndex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # 4. Calculate the Distance Matrix between the extracted vertices, some of which correspond to springs,
        #    and the Pour Point, which corresponds to the discharge point
        alg_params = {
            'INPUT': parameters['PourPoint'],
            'INPUT_FIELD': parameters['PourPointIDField'],
            'MATRIX_TYPE': 0,
            'NEAREST_POINTS': 0,
            'TARGET': outputs['CreateSpatialIndex']['OUTPUT'],
            'TARGET_FIELD': 'SegmentID',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DistanceMatrixVerticesToPourPoint'] = processing.run('qgis:distancematrix', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # 5. Using the Distance Matrix, select the 10 vertices that are the farthest from the Discharge Point
        #    These are the most likely to be the farthest springs, and thus the final extents of the longest channels
        alg_params = {
            'EXPRESSION': ' \"Distance\" >= array_get(array_sort(array_agg(\"Distance\"),false),9)',
            'INPUT': outputs['DistanceMatrixVerticesToPourPoint']['OUTPUT'],
            'METHOD': 0
        }
        outputs['Top10FarthestPoints'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}
        
        
        # 6.a Format the layer containing the Pour Point for proper input.Get the first(and only) point feature 
        #     in the pour point layer and concatenate it to its x,y coords
        PP_LAYER = self.parameterAsVectorLayer(parameters,'PourPoint', context)
        pp=PP_LAYER.getFeature(0)
        x=pp.geometry().asPoint().x()
        y=pp.geometry().asPoint().y()

        # 6.b Calculate the network costs between the pourpoint and the 10 farthest points
        #     using the native algorithm--> Shortest path (point to layer), and Travel Distance,
        #     rather than travel time, as cost
        alg_params = {
            'DEFAULT_DIRECTION': 2,
            'DEFAULT_SPEED': 50,
            'DIRECTION_FIELD': '',
            'END_POINTS': QgsProcessingFeatureSourceDefinition(outputs['DistanceMatrixVerticesToPourPoint']['OUTPUT'], selectedFeaturesOnly=True, featureLimit=-1),
            'INPUT': QgsProcessingFeatureSourceDefinition(parameters['ChannelNetwork'], selectedFeaturesOnly=True, featureLimit=-1),
            'SPEED_FIELD': '',
            'START_POINT':'{} [EPSG:2100]'.format(str(x)+','+str(y)), 
            'STRATEGY': 0,
            'TOLERANCE': 0,
            'VALUE_BACKWARD': '',
            'VALUE_BOTH': '',
            'VALUE_FORWARD': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ShortestPathPointToLayer'] = processing.run('native:shortestpathpointtolayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        
        # 7. Select the point with the maximum network cost. Since the cost calc method was 
        #    set to 'Shortest', the max cost corresponds to the maximum distance on the network
        #    and thus the longest hydrological stream
        alg_params = {
            'EXPRESSION': ' \"cost\" >= array_get(array_sort(array_agg(\"cost\"),false),0)',
            'INPUT': outputs['ShortestPathPointToLayer']['OUTPUT'],
            'METHOD': 0
        }
        outputs['Longest_Stream'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # 8. Save the max cost path to a new layer (final output)
        alg_params = {
            'INPUT': outputs['ShortestPathPointToLayer']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Longest_Stream'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        # 9. Rename the layer 
        alg_params = {
            'INPUT': outputs['Longest_Stream']['OUTPUT'],
            'OUTPUT': parameters['Longest_Stream']
        }
        outputs['Longest_Flow_Path'] = processing.run('geomel_watershed:rename_output', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # 10. Pack the dict key/value pair Longest_Stream in the results and return it
        results['Longest_Flow_Path'] = outputs['Longest_Flow_Path']['OUTPUT']
        return results


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)


    def name(self):
        return 'geomelLongestFlowPath'


    def createInstance(self):
        return geomelLongestFlowPath()


    def displayName(self):
        return self.tr('3. Longest Flow Path')


    def group(self):
        return self.tr('Geomeletitiki Hydrology Analysis')


    def groupId(self):
        return 'geomel_hydro_main'


    def shortHelpString(self):
        return self.tr('\n\n Extract the longest flow path. Note that the <b>discharge point</b> should be <b>ON</b> the Channel Network. Ensure this by editing the layer containing the point, and moving it with <b>Snapping</b> enabled.  \n\n\n\n\nDeveloped by E. Lymperis\n2021, Geomeletitiki S.A.')