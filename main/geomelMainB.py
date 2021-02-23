import os
try:
    from qgis import processing
except:
    import processing
from qgis.core import QgsProject, QgsProcessingAlgorithm, QgsVectorLayer, QgsProcessingParameterVectorDestination, QgsProcessingParameterRasterLayer, QgsProcessingParameterVectorLayer, QgsVectorDataProvider, QgsField, QgsRasterLayer, QgsRasterBandStats
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
            QgsProcessingParameterVectorDestination(
                'SCS',
                self.tr('SCS Cover')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'Cor',
                self.tr('Corine Cover')
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

        # Open the log file
        path_absolute = QgsProject.instance().readPath("./")
        path = "/Hydro_Log_{}".format(datetime.now())
        path = path.replace(":", "_")
        path = path[:-7]
        path = path_absolute + path +".txt"
        
    
        log = open(path, "a")
        log.write("--------------------------Complete Watershed Analysis Log-------------------------------\n")
        log.write("\n")
        log.write("\n")
        log.write("Ημερομηνία/Ώρα: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"\n")
        log.write("\n")
        
    
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
        Watershed = processing.run('gdal:polygonize',
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
    
    
    
    
    
        # 4. Filter the watershed layer, keep only the needed watershed
        Filter_Res = processing.run('geomel_watershed:geomelWAttributes',
                                   {'Watershed': Watershed,
                                   'Filtered_Watershed': 'TEMPORARY_OUTPUT',
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
    
    
    
    
    
    
    
        # 4. Clip DEM
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
    
        # 5. Watershed Stats
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
    
    
    
    
    
    
    
        # 6. CN Calculation
        
        CN_Vector = processing.run('geomel_watershed:geomelCN',
                                   {'Watershed_CN':parameters['CN_Layer'],
                                    'W_Corine' : parameters['Cor'],
                                    'W_LandUseSCS' : parameters['SCS'],
                                    'Watershed' : Filtered_Watershed },
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)['Watershed_CN']
    
    
    
        if feedback.isCanceled():
            return {}
    
        
        log.close()
    
        
        return {
            "Watershed":Filtered_Watershed,
            "CN_Layer":CN_Vector,
            "Filtered_Watershed":Filtered_Watershed
            
        }
