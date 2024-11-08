from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,QgsFeatureSink,
                       QgsField,
                       QgsFields, QgsExpressionContext, QgsExpressionContextUtils,
                       QgsExpression, QgsProcessingParameterNumber,
                       QgsFeature)
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant

try:
    import processing
except:
    from qgis import processing


class geomelIDGW(QgsProcessingAlgorithm):
    
    

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource('INPUT', 'INPUT', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('ReturnPeriod', 'Return Period in Years (T)', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=50))
        self.addParameter(QgsProcessingParameterNumber('RainfallDuration', 'Rainfall Duration in Hours (d)', type=QgsProcessingParameterNumber.Double, minValue=0.1, defaultValue=1.0))
        self.addParameter(QgsProcessingParameterFeatureSink('OUTPUT','Nearest Stations (IDGW)', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        outFields = QgsFields()
        outFields.append(QgsField("ΥΔ",QVariant.String,len=10))
        outFields.append(QgsField("ΚΩΔΙΚΟΣ",QVariant.String,len=5))
        outFields.append(QgsField("ΟΝΟΜΑ",QVariant.String,len=50))
        outFields.append(QgsField("Χ",QVariant.Double,len=25,prec=7))
        outFields.append(QgsField("Y",QVariant.Double,len=25,prec=7))
        outFields.append(QgsField("Z",QVariant.Double,len=25,prec=7))


        outFields.append(QgsField("κ",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("λ",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("ψ",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("θ",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("η",QVariant.Double,len=10,prec=4))
        

        outFields.append(QgsField("α(Τ)",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("Απόσταση (Km)",QVariant.Double,len=25,prec=7))
        outFields.append(QgsField("1/d2",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("Wi",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("i (mm/hr)",QVariant.Double,len=10,prec=4))
        outFields.append(QgsField("Σταθμισμένη i (mm/hr)",QVariant.Double,len=10,prec=4))

        

        
        source = self.parameterAsVectorLayer(parameters,'INPUT',context)
        (sink, dest_id) = self.parameterAsSink(parameters, 'OUTPUT', context,outFields,source.wkbType(),source.sourceCrs())
        features = source.getFeatures()
        

        context = QgsExpressionContext()
        context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(source))

        for current, feature in enumerate(features):
            out_feat = QgsFeature(outFields)
            out_feat.setGeometry(feature.geometry())
         
          
            k = feature['κ']
            l = feature["λ΄"]
            psi = feature["ψ΄"]
            theta = feature['θ']
            eta = feature['η']
            D = feature['Distance']/1000
            


            T = parameters['ReturnPeriod']   
            d_v = parameters['RainfallDuration'] 

            a_T = l*((T**k)-psi)
            print(a_T)
            reverse_d_sq = 1/(D**2)

            
            context.setFeature(feature)

            total_distance = (QgsExpression('sum(1/((\"Distance\"/1000)*(\"Distance\"/1000)))').evaluate(context))
            
            print(total_distance)
            weight = reverse_d_sq/total_distance

            i = a_T/((1+(d_v/theta))**eta)

            S_i = weight*i

            ###########

            out_feat['ΥΔ'] = feature['ΥΔ']
            out_feat['ΚΩΔΙΚΟΣ'] = feature['ΚΩΔΙΚΟΣ']
            out_feat['ΟΝΟΜΑ'] = feature['ΟΝΟΜΑ']

            out_feat['Χ'] = feature['Χ']
            out_feat['Y'] = feature['Υ']
            out_feat['Z'] = feature['Ζ']

            out_feat["κ"] =  feature["κ"]
            out_feat["λ"] = feature["λ΄"]
            out_feat["ψ"] = feature["ψ΄"]
            out_feat["θ"] =  feature["θ"]
            out_feat["η"] =  feature["η"]

            out_feat["α(Τ)"] = a_T
            out_feat["Απόσταση (Km)"] = D
            out_feat["1/d2"] = reverse_d_sq
            out_feat["Wi"] = weight
            out_feat["i (mm/hr)"] = i
            out_feat["Σταθμισμένη i (mm/hr)"] = S_i



            print(S_i)

            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

        results={'OUTPUT': dest_id}
        return results
    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)
    
    def name(self):
        return 'geomelIDGW'

    def createInstance(self):
        return geomelIDGW()

    def displayName(self):
        return self.tr('IDF 2: Inverse Distance Gage Weighting for IDF Curves')

    def group(self):
        return self.tr('Geomeletitiki Help Scripts')

    def groupId(self):
        return 'geomel_hydro'

    def shortHelpString(self):
        return self.tr('Using the meteo stations parameters, calculate precipitation intensity via Inverse Distance Gage Weighting')
