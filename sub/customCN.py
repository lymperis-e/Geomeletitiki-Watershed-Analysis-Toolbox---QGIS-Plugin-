from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterString,
                       QgsVectorLayer,
                       QgsProject,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterEnum,
                       QgsMessageLog,
                       Qgis)
                       
from qgis.core import QgsFields, QgsField
try:
    from qgis import processing
except:
    import processing
from PyQt5.QtCore import QVariant
from collections import defaultdict
from datetime import datetime
import os,sys,inspect

currentPath = os.path.dirname(__file__)
basePath = os.path.dirname(currentPath)


class customCN(QgsProcessingAlgorithm):
    """
    Calculate a watershed's CN
    """
    OUTPUT = 'Watershed_CN'
    Corine = 'W_Corine'
    Soil = 'W_LandUseSCS'
    Pour_Point_Name = 'Pour_Point_Name'


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return customCN()

    def name(self):
        return 'customCN'

    def displayName(self):
        return self.tr("E. Koutsimari's CN Calculator")

    def group(self):
        return self.tr('Geomeletitiki Help Scripts')

    def groupId(self):
        return 'geomel_hydro'

    def shortHelpString(self):
        return self.tr("E. Koutsimari's CN Calculator: Calculates the Curve Number of a watershed based on Corine and SCS data")

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'Watershed',
                self.tr('Watershed'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.Pour_Point_Name,
                self.tr('Pour Point Name'),
                optional=True
            )
        )

        self.addParameter(QgsProcessingParameterEnum('Conditions', 'Conditions', options=['Unfavorable', 'Mean', 'Favorable'], allowMultiple=False, defaultValue=['Mean']))

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Watershed with CN')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.Corine,
                self.tr('Watershed with Corine Classes')
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.Soil,
                self.tr('Watershed with SCS Classes')
            )
        )
        

    def processAlgorithm(self, parameters, context, feedback):


        # Read Corine and SCS data path from settings
        settings_path = os.path.join(basePath, 'sets')
        corine_settings = open(os.path.join(settings_path, 'settings_corine.txt'), 'r')
        scs_settings = open(os.path.join(settings_path, 'settings_scs.txt'), 'r')

        try:
            try:
                soil_path = os.path.join(scs_settings.read(), "SOIL.gpkg")
                corine_path = os.path.join(corine_settings.read(), "corine_2018.gpkg")
            except:
                soil_path = os.path.join(scs_settings.read(), "HSG_pineios.shp")
                corine_path = os.path.join(corine_settings.read(), "corine_2018.shp")
        except:
            QgsMessageLog.logMessage("Could not locate the Soil/Landuse data! Please make sure you have downloaded the datasets (https://drive.google.com/drive/folders/1uwq5Fixi8lvyIi0cdFhbjfmaBQsONNnK) and properly set up your settings, via the gear button on the plugin toolbar!", level=Qgis.Critical)
        
        corine_settings.close()
        scs_settings.close() 




        pp_name = self.parameterAsString(parameters, self.Pour_Point_Name ,context)
        # Open the log file
        path_absolute = QgsProject.instance().readPath("./")
        path = "/CN_Calculation_Log_{}_{}".format(pp_name, datetime.now())
        path = path.replace(":", "_")
        path = path[:-7]
        path = path_absolute + path +".txt"


        log = open(path, "w")
        log.write("Κλάση Κάλυψης Γης κατά Corine  /  % κάλυψη της λεκάνης \n")
        log.write("-------------------------------------------------------------------------\n")

        # 1. Crop Soil&Corine to extent
        Watershed = self.parameterAsSource(parameters,'Watershed',context)
        
        # 2. Clip Corine and Soil layers to the exact shape of the watershed
        Soil = processing.run('gdal:clipvectorbypolygon',
                                   {'INPUT' : soil_path,
                                    'MASK' : self.parameterAsVectorLayer(parameters,'Watershed',context),
                                    'OPTIONS' : '',
                                    'OUTPUT' : parameters['W_LandUseSCS'] },
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)
        if feedback.isCanceled():
            return {}


        Corine = processing.run('gdal:clipvectorbypolygon',
                                   {'INPUT' :  corine_path,
                                    'MASK' : self.parameterAsVectorLayer(parameters,'Watershed',context),
                                    'OPTIONS' : '',
                                    'OUTPUT' : parameters['W_Corine'] },
                                   is_child_algorithm=True,
                                   context=context,
                                   feedback=feedback)
        if feedback.isCanceled():
            return {}

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'Union',
                self.tr('Watershed'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )

   
        Union = processing.run('saga:polygonunion',
                            {'A' : Corine['OUTPUT'],
                            'B' : Soil['OUTPUT'],
                            'RESULT' : 'TEMPORARY_OUTPUT',
                            'SPLIT' : True },
                               is_child_algorithm=True,
                               context=context,
                               feedback=feedback)

        # 4. Calculate CN 
        #Put intersections in a layer and add CN field
        CN_labels =  QgsVectorLayer(Union['RESULT'], '', 'ogr')

        outFields = QgsFields()

        # 2. Then, I defined the fields
        outFields.append(QgsField("Basin Percentage",QVariant.Double))
        outFields.append(QgsField("Corine_Code",QVariant.Double))
        outFields.append(QgsField("CORINE Descr",QVariant.String))
        #outFields.append(QgsField("Geo_Code",QVariant.String))
        outFields.append(QgsField("LandUse_Code(1_7)",QVariant.Int))
        outFields.append(QgsField("Hydro_Code(ABCD)",QVariant.String))
        outFields.append(QgsField("CN",QVariant.Int))

        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, outFields, CN_labels.wkbType(), CN_labels.crs())


        corine_to_1_7_dict = {
            "111":["Συνεχής αστικός ιστός",6],
            "112":["Ασυνεχής αστικός ιστός",6],
            "121":["Βιομηχανικές ή εμπορικές ζώνες",5],
            "122":["Οδικά & σιδηροδρομικά δίκτυα",7],
            "123":["Ζώνες λιμένων",7],
            "124":["Αεροδρόμια",7],
            "131":["Χώροι εξορύξεως ορυκτών",6],
            "132":["Χώροι απορρίψεως απορριμμάτων",6],
            "133":["Χώροι οικοδόμησης",6],
            "141":["Περιοχές αστικού πρασίνου", 4],
            "142":["Εγκαταστάσεις αθλητισμού και αναψυχής",4],
            "211":["Μη αρδευόμνη αρόσιμη γη",1],
            "212":["Μόνιμα αρδευόμενη γη",1],
            "213":["Ορυζώνες",1],
            "221":["Αμπελώνες",1],
            "222":["Οπωροφόρα δένδρα και φυτείες με σαρκώδεις καρπούς",1],
            "223":["Ελαιώνες",1],
            "231":["Λιβάδια",2],
            "241":["Ετήσιες καλλιέργειες που συνδέονται με μόνιμες καλλιέργειες",1],
            "242":["Σύνθετες Καλλιέργειες",1],
            "243":["Γη που χρησιμοποιείται κυρίως για γεωργία με σημαντικά τμήματα φυσικής βλάστησης",1],
            "244":["Γεωργο-δασικές Περιοχές", 1],
            "311":["Δάσος πλατυφύλλων",3],
            "312":["Δάσος κωνοφόρων",3],
            "313":["Μικτό δάσος",3],
            "321":["Φυσικοί  βοσκότοποι",2],
            "322":["Θάμνοι και χερσότοποι",2],
            "323":["Σκληροφυλλική βλάστηση",2],
            "324":["Μεταβατικές δασώδεις θαμνώδεις εκτάσεις",3],
            "331":["Παραλίες, αμμόλοφοι, αμμουδιές",3],
            "332":["Απογυμνωμένοι βράχοι",7],
            "333":["Εκτάσεις με αραιή βλάστηση",2],
            "334":["Αποτεφρωμένες εκτάσεις",6],
            "335":["Παγετώνες και αέναο χιόνι", 7],
            "411":["Βάλτοι στην ενδοχώρα",7],
            "412":["Τυρφώνες", 7],
            "421":["Παραθαλάσσιοι βάλτοι",7],
            "422":["Αλυκές",7],
            "423":["Ζώνες που καλύπτονται από παλιρροιακά ύδατα", 7],
            "511":["Υδατορρεύματα",7],
            "512":["Επιφάνειες στάσιμου ύδατος",7],
            "521":["Παράκτιες λιμνοθάλασσες",7],
            "522":["Εκβολές ποταμών",7],
            "523":["Θάλασσες και ωκεανοί",7]
        }

       
        # Choose conditions
        conditions_index = self.parameterAsEnum(parameters,'Conditions',context)
        # Unfavorable
        if conditions_index == 0 :
            geo_corine_to_CN_dict = {
                "1A":72,
                "1B":81,
                "1C":88,
                "1D":91,
                "2A":68,
                "2B":79,
                "2C":86,
                "2D":89,
                "3A":45,
                "3B":66,
                "3C":77,
                "3D":83,
                "4A":49,
                "4B":69,
                "4C":79,
                "4D":84,
                "5A":89,
                "5B":92,
                "5C":94,
                "5D":95,
                "6A":77,
                "6B":85,
                "6C":90,
                "6D":92,
                "7A":98,
                "7B":98,
                "7C":98,
                "7D":98
            }
        elif conditions_index == 1:
            geo_corine_to_CN_dict = {
                "1A":67,
                "1B":76,
                "1C":83,
                "1D":86,
                "2A":49,
                "2B":68.5,
                "2C":78.5,
                "2D":83.5,
                "3A":35,
                "3B":60.5,
                "3C":73.5,
                "3D":80,
                "4A":44,
                "4B":65,
                "4C":76.5,
                "4D":82,
                "5A":85,
                "5B":90,
                "5C":92.5,
                "5D":94,
                "6A":64,
                "6B":76.5,
                "6C":84.5,
                "6D":88,
                "7A":85,
                "7B":90,
                "7C":92.5,
                "7D":93.5
            }
        #Favorable Conditions
        else:
            geo_corine_to_CN_dict = {
                "1A":62,
                "1B":71,
                "1C":78,
                "1D":81,
                "2A":30,
                "2B":58,
                "2C":71,
                "2D":78,
                "3A":25,
                "3B":55,
                "3C":70,
                "3D":77,
                "4A":39,
                "4B":61,
                "4C":74,
                "4D":80,
                "5A":81,
                "5B":88,
                "5C":91,
                "5D":93,
                "6A":51,
                "6B":68,
                "6C":79,
                "6D":84,
                "7A":72,
                "7B":82,
                "7C":87,
                "7D":89
            }


        basin_area=None
        for f in self.parameterAsVectorLayer(parameters,'Watershed',context).getFeatures():
            basin_area = f.geometry().area()

        corine_perc = defaultdict()

        CN_perc = defaultdict()

        for feat in CN_labels.getFeatures():
            try:
                CN = None
                geo_abcd = feat["Hydro_Code"]
                cor = feat["Code_18"]
                
                # Convert corine code to 1-7
                cor_1_7 = corine_to_1_7_dict[cor][1]
                corine_description = corine_to_1_7_dict[cor][0]



                #Combine them
                geo_corine = str(cor_1_7) + geo_abcd

                #Convert to CN
                CN = geo_corine_to_CN_dict[geo_corine]
                
                perc = (feat.geometry().area()/basin_area)*100
                perc = '%.3f' % round(perc, 5)
                
                #Update the Corine and CN dicts (for logging)
                if corine_description in corine_perc:
                    corine_perc[corine_description] += float(perc)
                else:
                    corine_perc[corine_description] = float(perc)
                    

                if CN in CN_perc:
                    CN_perc[CN] += float(perc)
                else:
                    CN_perc[CN] = float(perc)
                


                out_feat = QgsFeature(outFields)
                out_feat.setGeometry(feat.geometry())
                out_feat['Basin Percentage'] = perc
                out_feat['Corine_Code'] = float(cor)
                out_feat['CORINE Descr'] = corine_description
                #out_feat['Geo_Code'] = geo
                out_feat['LandUse_Code(1_7)'] = cor_1_7
                out_feat['Hydro_Code(ABCD)']= geo_abcd
                out_feat['CN'] = CN
                sink.addFeature(out_feat, QgsFeatureSink.FastInsert)
            except:
                continue

        

        for key, value in corine_perc.items():
            log.write(str(key) + ": " + str(value)+"\n")
        


        # Write the CN log part
        log.write("\n\n\n")
        log.write("\n\n\n")
        log.write("Αριθμός Καμπύλης CN  /  % κάλυψη της λεκάνης \n")
        log.write("-------------------------------------------------------------------------\n")


        Sum_CN_arithm = 0
        Sum_CN_paronom = 0
        for key, value in CN_perc.items():
            #Write a log entry for each CN and its %cover of the basin
            log.write(str(key) + ": " + str(value)+"\n")

            Sum_CN_arithm += key*value
            Sum_CN_paronom += value
        
        log.write("\n\n")
        Sum_CN = Sum_CN_arithm/Sum_CN_paronom
        log.write("Συνισταμένη Τιμή CN (χωρικά σταθμισμένη): " + str(Sum_CN))

        # Calculate and log urban cover
        log.write("-------------------------------------------------------------------------\n")
        log.write("Αστική Κάλυψη (κωδικοί Corine: 111-124, 141,142) \n")
        log.write("\n\n\n")

        urban_total = 0.000
        for key, value in corine_perc.items():
            if key=="Συνεχής αστικός ιστός" or key=="Ασυνεχής αστικός ιστός" or key=="Βιομηχανικές ή εμπορικές ζώνες" or key=="Οδικά & σιδηροδρομικά δίκτυα" or key=="Ζώνες λιμένων" or key=="Αεροδρόμια" or key=="Περιοχές αστικού πρασίνου" or key=="Εγκαταστάσεις αθλητισμού και αναψυχής":
                log.write(str(key) + ": " + str(value)+"\n")
                urban_total += value
        log.write("Αστική Κάλυψη (%): " + str(urban_total))
        log.write("\n")
        log.write("Αστική Κάλυψη (0-1): " + str(urban_total/100))

        # Calculate Total CN value



        # Return the results
        return {
            self.OUTPUT: dest_id
        }