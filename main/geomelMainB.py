import os
try:
    from qgis import processing
except:
    import processing
from qgis.core import QgsProject, QgsVectorLayer, QgsProcessingParameterNumber, QgsProcessingAlgorithm, QgsProcessingFeatureSourceDefinition, QgsFeatureRequest, QgsVectorLayer, QgsProcessingParameterVectorDestination, QgsProcessingParameterRasterLayer, QgsProcessingParameterVectorLayer, QgsVectorDataProvider, QgsField, QgsRasterLayer, QgsRasterBandStats
from PyQt5.QtCore import QVariant, QCoreApplication
from datetime import datetime
import math
import ast


class geomelMainB(QgsProcessingAlgorithm):
    """
    Basin hydrological analysis tool
    INPUTS: 
             1. DEM
             2. Channel Initiation Threshold 
    Outputs: 
             1. Filled DEM  (Wang&Liu methodology)
             2. Flow Directions (Raster)
             3. Watershed (Raster)
             4. Watershed (Vector)
             5. Channel Network (Vector)
             6. CN-labeled Watershed (Vector)
    
    Channel Initiation Threshold: the minimum number of cells (raster pixels) that drain through a particular cell A, in order for A to be labeled as part of a Channel. The default value is 40,000 and was specified to produce an adequately dense Channel Network on a 10Km x 8Km DEM
    
    
    -------------------------------------------------------------
    
    
    
    
    
    
    
    Developed by E. Lymperis
    2021, Geomeletitiki S.A.
    """

    Filled_DEM = 'Filled_DEM'
    Pour_Point = 'Pour_Point'
    Channel_Net = 'Channel_Net'
    Watershed_Basin = 'Watershed_Basin'
    Contour_Interval = 'Contour_Interval'
    SCS = 'SCS'
    Corine = 'Corine'

    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return geomelMainB()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'geomelMainB'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('2. Geomeletitiki Complete Watershed Analysis Module - Basin CN')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Geomeletitiki Hydrology Analysis')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'geomel_hydro_main'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('\n\n\n\n\nDeveloped by E. Lymperis\n2021, Geomeletitiki S.A.')

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.Filled_DEM,
                self.tr('Filled_DEM')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.Pour_Point,
                self.tr('Pour_Point')
            )
        )
       

        self.addParameter(
            QgsProcessingParameterNumber(
                self.Contour_Interval,
                self.tr('Contour Interval (in meters)'),
                defaultValue=50
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.Watershed_Basin,
                self.tr('Watershed Basin')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.SCS,
                self.tr('SCS Cover')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.Corine,
                self.tr('Corine Cover')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'Contour_Lines',
                self.tr('Clipped Contour Lines')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.Channel_Net,
                self.tr('Clipped Channel Network')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'CN_Layer',
                self.tr('CN Labels (Vector)')
            )
        )
        


    
    def processAlgorithm(self, parameters, context, feedback):
       
        Filled_DEM = self.parameterAsRasterLayer(parameters,'Filled_DEM', context)
        Pour_Point = self.parameterAsVectorLayer(parameters,'Pour_Point', context)
        SCS = self.parameterAsOutputLayer(parameters,'SCS', context)
        Corine = self.parameterAsOutputLayer(parameters,'Corine', context)
        Watershed_Basin = self.parameterAsOutputLayer(parameters, 'Watershed_Basin', context)
        Channel_Net = self.parameterAsOutputLayer(parameters, 'Channel_Net', context)
        Contour_Interval = self.parameterAsInt(parameters, 'Contour_Interval', context)

       
    
        Catchment_Area = None
    
        # Specify the Pour Point from the points layer
        pour_point = None
        for f in Pour_Point.getFeatures():
            pour_point = f
    
    
    
    
    
        # 2. Run UpSlopeArea
        x = pour_point.geometry().asPoint().x()
        y = pour_point.geometry().asPoint().y()
    
        Upslope_Area = processing.run('saga:upslopearea',
                                   {'AREA' : 'TEMPORARY_OUTPUT',
                                    'CONVERGE' : 1.1,
                                    'ELEVATION' : Filled_DEM,
                                    'METHOD' : 0,
                                    'SINKROUTE' : None,
                                    'TARGET' : None,
                                    'TARGET_PT_X' : x,
                                    'TARGET_PT_Y' : y },
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)['AREA']
        if feedback.isCanceled():
            return {}
    
    
    
    
        # 3. Run Polygonize
        Initial_Watershed = processing.run('gdal:polygonize',
                                   {'BAND' : 1,
                                    'EIGHT_CONNECTEDNESS' : False,
                                    'EXTRA' : '',
                                    'FIELD' : 'DN',
                                    'INPUT' : Upslope_Area,
                                    'OUTPUT' : 'TEMPORARY_OUTPUT' } ,
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)['OUTPUT']
        if feedback.isCanceled():
            return {}
    

        # 4. Fix any invalid geometries in the vectorized watershed
        Watershed = processing.run('native:fixgeometries',
                                   {'INPUT' : Initial_Watershed,
                                    'OUTPUT' : 'TEMPORARY_OUTPUT' } ,
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)['OUTPUT']
        if feedback.isCanceled():
            return {}

    
    
    
        # 5. Filter the watershed layer, keep only the needed watershed
        Filter_Res = processing.run('geomel_watershed:geomelWAttributes',
                                   {'Watershed':  Watershed,
                                   'Filtered_Watershed': Watershed_Basin,
                                   'pour_point': str(x) + ',' + str(y),
                                   'Area_Perimeter': 'TEMPORARY_OUTPUT'} ,
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)
        if feedback.isCanceled():
            return {}
    
    
        Filtered_Watershed = Filter_Res['Filtered_Watershed']
        area_per = ast.literal_eval(Filter_Res['Area_Perimeter'])
        area = area_per[0]
        perimeter = area_per[1]
    
    
    
    
    
        # 6. Clip DEM
        Clipped_DEM = processing.run('gdal:cliprasterbymasklayer',
                                       { 'ALPHA_BAND' : False,
                                        'CROP_TO_CUTLINE' : True,
                                        'DATA_TYPE' : 0,
                                        'EXTRA' : '',
                                        'INPUT' : Filled_DEM,
                                        'KEEP_RESOLUTION' : False,
                                        'MASK' : Filtered_Watershed,
                                        'MULTITHREADING' : False, 'NODATA' : None, 'OPTIONS' : '', 'OUTPUT' : 'TEMPORARY_OUTPUT', 'SET_RESOLUTION' : False, 'SOURCE_CRS' : None, 'TARGET_CRS' : None, 'X_RESOLUTION' : None, 'Y_RESOLUTION' : None },
                                       is_child_algorithm=True,
                                       context=context,
                                       feedback=feedback)['OUTPUT']
        if feedback.isCanceled():
            return {}


        
    
        # 7. Calculate Contours
        Contours = processing.run('gdal:contour',
                                   {'BAND' : 1,
                                    'CREATE_3D' : False,
                                    'EXTRA' : '',
                                    'FIELD_NAME' : 'ELEV',
                                    'IGNORE_NODATA' : False,
                                    'INPUT' : Clipped_DEM,
                                    'INTERVAL' : Contour_Interval,
                                    'NODATA' : None,
                                    'OFFSET' : 0,
                                    'OUTPUT' : parameters['Contour_Lines']},
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)['OUTPUT']
        if feedback.isCanceled():
            return {}




        # 8. Clip the Channel Network (if it is available)
        Channels_Initial = None
        candidates = QgsProject.instance().mapLayersByName('Channel Network')

        if len(candidates) > 0:
            for layer in candidates:
                if isinstance(layer, QgsVectorLayer):
                    Channels_Initial = layer
                    break
                else:
                    continue
            Channels = processing.run('gdal:clipvectorbypolygon',
                                       { 'INPUT' : Channels_Initial,
                                        'MASK' : Filtered_Watershed,
                                        'OPTIONS' : '',
                                        'OUTPUT' : Channel_Net},
                                       is_child_algorithm=True,
                                       context=context,
                                       feedback=feedback)['OUTPUT']
            if feedback.isCanceled():
                return {}
        else:
            Channels = None
        




    
        # 7. Watershed Stats
        watershed_stats = None
        Stats = processing.run('geomel_watershed:geomelWatershedStats',
                                       {'Clipped_DEM': Clipped_DEM ,
                                       'Area': area,
                                       'Perimeter':perimeter,
                                       'Watershed_Stats': watershed_stats},
                                       is_child_algorithm=True,
                                       context=context,
                                       feedback=feedback)['Watershed_Stats']
        if feedback.isCanceled():
            return {}
    
    
    
    
    
    
    
        # 8. CN Calculation
        
        CN_Vector = processing.run('geomel_watershed:geomelCN',
                                   {'Watershed_CN':parameters['CN_Layer'],
                                    'W_Corine' : Corine,
                                    'W_LandUseSCS' : SCS,
                                    'Watershed' : Filtered_Watershed },
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)['Watershed_CN']
    
    
    
        if feedback.isCanceled():
            return {}
    
        
        return {
            "CN_Layer":CN_Vector,
            "Contour_Lines": Contours,
            "Channel_Net": Channels,
            "Watershed_Basin":Filtered_Watershed
        }
