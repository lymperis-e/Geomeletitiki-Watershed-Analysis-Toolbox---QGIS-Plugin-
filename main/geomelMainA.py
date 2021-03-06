import os
try:
    from qgis import processing
except:
    import processing

from qgis.core import QgsProject, QgsProcessingParameterRasterDestination, QgsProcessingParameterVectorDestination, QgsProcessingParameterNumber, QgsProcessingParameterRasterLayer, QgsProcessingAlgorithm, QgsVectorLayer, QgsVectorDataProvider, QgsField, QgsRasterLayer, QgsRasterBandStats
from PyQt5.QtCore import QVariant
from datetime import datetime
from qgis.PyQt.QtCore import QCoreApplication



class geomelMainA(QgsProcessingAlgorithm):
    """
    Note: Use this module first, if you NEED TO SPECIFY THE POUR POINT and then run module 2. If you already know its exact position you can directly use module 3


    Basin hydrological analysis tool - module 1
    INPUTS: 
             1. DEM
             2. Channel Initiation Threshold 
    Outputs: 
             1. Filled DEM  (Wang&Liu methodology)
             2. Flow Directions (Raster)
             5. Channel Network (Vector)
             6. Channel Network (Raster)
    
    Channel Initiation Threshold: the minimum number of cells (raster pixels) that drain through a particular cell A, in order for A to be labeled as part of a Channel. The default value is 40,000 and was specified to produce an adequately dense Channel Network on a 10Km x 8Km DEM
    
    """

    DEM = 'DEM'
    Channel_Initiation_Threshold = 'Channel_Initiation_Threshold'

    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return geomelMainA()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'geomelMainA'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('1. Geomeletitiki Complete Watershed Analysis Module - Channel Net')

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
                self.DEM,
                self.tr('DEM')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.Channel_Initiation_Threshold,
                self.tr('Channel Initiation Threshold'),
                defaultValue=40000
            )
        )

       
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                'Flow_Direction',
                self.tr('Flow Direction')
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                'Filled_DEM',
                self.tr('Filled DEM')
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                'Channel_Network_Raster',
                self.tr('Channel Network (Raster)')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'Channel_Network_Vector',
                self.tr('Channel Network (Vector)')
            )
        )




    

    def processAlgorithm(self, parameters, context, feedback):
        
        DEM = self.parameterAsRasterLayer(parameters,'DEM', context)
        Pour_Point = self.parameterAsVectorLayer(parameters,'Pour_Point', context)
        
        
    
        Catchment_Area = None
    
    
        # 1. Run Fill(Wang&Liu)
        RES_1 = processing.run('saga:fillsinkswangliu',
                                   {'ELEV' : DEM,
                                    'FDIR' : 'TEMPORARY_OUTPUT',
                                    'FILLED' : 'TEMPORARY_OUTPUT',
                                    'MINSLOPE' : 0.01,
                                    'WSHED' : 'TEMPORARY_OUTPUT',
                                    'FDIR': parameters['Flow_Direction'],
                                    'FILLED': parameters['Filled_DEM']
                                    },
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)
        if feedback.isCanceled():
            return {}
    
    
        #Results 1
        Flow_Direction = RES_1["FDIR"]
        Filled_DEM = RES_1["FILLED"]
        
    
    
    
    
        # 4. Catchment Area
        Catchment_Area = processing.run('saga:catchmentarea',
                                   {'ELEVATION' : Filled_DEM,
                                    'FLOW' : 'TEMPORARY_OUTPUT',
                                    'METHOD' : 0 } ,
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)['FLOW']
        if feedback.isCanceled():
            return {}
    
    
        # 5. Channel Network
        RES_5 = processing.run('saga:channelnetwork',
                                   { 'CHNLNTWRK' : parameters['Channel_Network_Raster'],
                                    'CHNLROUTE' : 'TEMPORARY_OUTPUT',
                                    'DIV_CELLS' : 10, 'DIV_GRID' : None,
                                    'ELEVATION' :  Filled_DEM,
                                    'INIT_GRID' : Catchment_Area,
                                    'INIT_METHOD' : 2,
                                    'INIT_VALUE' : parameters['Channel_Initiation_Threshold'],
                                    'MINLEN' : 1,
                                    'SHAPES' : parameters['Channel_Network_Vector'],
                                    'SINKROUTE' : None,
                                    'TRACE_WEIGHT' : None } ,
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)
        if feedback.isCanceled():
            return {}
        Channel_Network_Vector = RES_5['SHAPES']
        Channel_Network_Raster = RES_5['CHNLNTWRK']
    
        
       
    
        
        return {
            "Flow_Direction":Flow_Direction,
            "Filled_DEM":Filled_DEM,
            "Channel_Network_Raster": Channel_Network_Raster,
            "Channel_Network_Vector":Channel_Network_Vector
        }






