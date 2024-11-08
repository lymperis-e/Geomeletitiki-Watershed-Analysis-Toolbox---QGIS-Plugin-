from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
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
    Qgis,
)

from qgis.core import QgsFields, QgsField

try:
    from qgis import processing
except:
    import processing
from PyQt5.QtCore import QVariant
from collections import defaultdict
from datetime import datetime
import os, sys, inspect
import csv

currentPath = os.path.dirname(__file__)
basePath = os.path.dirname(currentPath)


class geomelCN(QgsProcessingAlgorithm):
    """
    Calculate a watershed's CN
    """

    OUTPUT = "Watershed_CN"
    watershed_land_cover_output = "W_Corine"
    watershed_soil_output = "W_LandUseSCS"
    Pour_Point_Name = "Pour_Point_Name"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return geomelCN()

    def name(self):
        return "geomelCN"

    def displayName(self):
        return self.tr("Geomeletitiki CN Calculator")

    def group(self):
        return self.tr("Geomeletitiki Help Scripts")

    def groupId(self):
        return "geomel_hydro"

    def shortHelpString(self):
        return self.tr("Geomeletitiki CN Calculator")

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "Watershed",
                self.tr("Watershed"),
                types=[QgsProcessing.TypeVectorAnyGeometry],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "SOIL_LAYER",
                self.tr("Soil Map"),
                types=[QgsProcessing.TypeVectorAnyGeometry],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "LAND_COVER_LAYER",
                self.tr("Corine Land Cover"),
                types=[QgsProcessing.TypeVectorAnyGeometry],
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.Pour_Point_Name, self.tr("Pour Point Name"), optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                "Conditions",
                "Conditions",
                options=["Unfavorable", "Mean", "Favorable"],
                allowMultiple=False,
                defaultValue=["Mean"],
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Watershed with CN"))
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.watershed_land_cover_output, self.tr("Watershed with Corine Classes")
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.watershed_soil_output, self.tr("Watershed with SCS Classes")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        pp_name = self.parameterAsString(parameters, self.Pour_Point_Name, context)
        # Open the log file
        path_absolute = QgsProject.instance().readPath("./")
        path = f"/CN_Calculation_Log_{pp_name}_{datetime.now()}"
        path = path.replace(":", "_")
        path = path[:-7]
        path = path_absolute + path + ".txt"

        log = open(path, "w", encoding="utf-8")
        log.write("Κλάση Κάλυψης Γης κατά Corine  /  % κάλυψη της λεκάνης \n")
        log.write(
            "-------------------------------------------------------------------------\n"
        )

        # 1. Crop Soil&Corine to extent
        # watershed_layer = self.parameterAsSource(parameters, "Watershed", context)
        # soil_layer = self.parameterAsSource(parameters, "SOIL_LAYER", context)
        # land_cover_layer = self.parameterAsSource(parameters, "LAND_COVER_LAYER", context)

        # 2. Clip Corine and Soil layers to the exact shape of the watershed
        # Soil = processing.run('gdal:clipvectorbypolygon',
        #                            {'INPUT' : soil_path,
        #                             'MASK' : self.parameterAsVectorLayer(parameters,'Watershed',context),
        #                             'OPTIONS' : '',
        #                             'OUTPUT' : parameters['W_LandUseSCS'] },
        #                            is_child_algorithm=True,
        #                            context=context,
        #                            feedback=feedback)
        # if feedback.isCanceled():
        #     return {}
        alg_params = {
            # "INPUT": "pagingEnabled='true' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:2100' typename='geonode:edafmap_1997_7' url='http://mapsportal.ypen.gr/geoserver/ows' version='auto'",
            "INPUT": self.parameterAsVectorLayer(parameters, "SOIL_LAYER", context),
            "OVERLAY": self.parameterAsVectorLayer(parameters, "Watershed", context),
            "OUTPUT": parameters["W_LandUseSCS"],
        }
        soil_layer = processing.run(
            "native:clip",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Corine = processing.run('gdal:clipvectorbypolygon',
        #                            {'INPUT' :  corine_path,
        #                             'MASK' : self.parameterAsVectorLayer(parameters,'Watershed',context),
        #                             'OPTIONS' : '',
        #                             'OUTPUT' : parameters['W_Corine'] },
        #                            is_child_algorithm=True,
        #                            context=context,
        #                            feedback=feedback)

        # Clip
        alg_params = {
            # "INPUT": "pagingEnabled='true' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:2100' typename='geonode:gr_clc2018' url='http://mapsportal.ypen.gr/geoserver/ows' version='auto'",
            "INPUT": self.parameterAsVectorLayer(parameters, "LAND_COVER_LAYER", context),
            "OVERLAY": self.parameterAsVectorLayer(parameters, "Watershed", context),
            "OUTPUT": parameters["W_Corine"],
        }
        land_cover_layer = processing.run(
            "native:clip",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        if feedback.isCanceled():
            return {}

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "Union",
                self.tr("Watershed"),
                types=[QgsProcessing.TypeVectorAnyGeometry],
            )
        )

        Union = processing.run(
            "sagang:polygonunion",
            {
                "A": land_cover_layer["OUTPUT"],
                "B": soil_layer["OUTPUT"],
                "RESULT": "TEMPORARY_OUTPUT",
                "SPLIT": True,
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback,
        )

        # 4. Calculate CN
        # Put intersections in a layer and add CN field
        cn_labels = QgsVectorLayer(Union["RESULT"], "", "ogr")

        out_fields = QgsFields()

        # 2. Then, I defined the fields
        out_fields.append(QgsField("Basin Percentage", QVariant.Double))
        out_fields.append(QgsField("Corine_Code", QVariant.Double))
        out_fields.append(QgsField("CORINE Descr", QVariant.String))
        out_fields.append(QgsField("Geo_Code", QVariant.String))
        out_fields.append(QgsField("LandUse_Code(1_7)", QVariant.Int))
        out_fields.append(QgsField("Hydro_Code(ABCD)", QVariant.String))
        out_fields.append(QgsField("CN", QVariant.Int))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            cn_labels.wkbType(),
            cn_labels.crs(),
        )

        geo_to_abcd_dict = {
            "Y": "A",
            "F": "A",
            "R": "B",
            "C": "C",
            "T": "D",
            "P": "C",
            "X": "A",
            "Z": "B",
            "N": "B",
            "A": "D",
            "K": "A",
            "H": "A",
            "J": "C",
            "V": "A",
            "W": "C",
            "L": "C",
            "S": "B",
            "E": "D",
            "B": "A",
            "M": "B",
        }

        corine_to_1_7_dict = {
            "111": ["Συνεχής αστικός ιστός", 6],
            "112": ["Ασυνεχής αστικός ιστός", 6],
            "121": ["Βιομηχανικές ή εμπορικές ζώνες", 5],
            "122": ["Οδικά & σιδηροδρομικά δίκτυα", 7],
            "123": ["Ζώνες λιμένων", 7],
            "124": ["Αεροδρόμια", 7],
            "131": ["Χώροι εξορύξεως ορυκτών", 6],
            "132": ["Χώροι απορρίψεως απορριμμάτων", 6],
            "133": ["Χώροι οικοδόμησης", 6],
            "141": ["Περιοχές αστικού πρασίνου", 4],
            "142": ["Εγκαταστάσεις αθλητισμού και αναψυχής", 4],
            "211": ["Μη αρδευόμενη αρόσιμη γη", 1],
            "212": ["Μόνιμα αρδευόμενη γη", 1],
            "213": ["Ορυζώνες", 1],
            "221": ["Αμπελώνες", 1],
            "222": ["Οπωροφόρα δένδρα και φυτείες με σαρκώδεις καρπούς", 1],
            "223": ["Ελαιώνες", 1],
            "231": ["Λιβάδια", 2],
            "241": ["Ετήσιες καλλιέργειες που συνδέονται με μόνιμες καλλιέργειες", 1],
            "242": ["Σύνθετες Καλλιέργειες", 1],
            "243": [
                "Γη που χρησιμοποιείται κυρίως για γεωργία με σημαντικά τμήματα φυσικής βλάστησης",
                1,
            ],
            "244": ["Γεωργο-δασικές Περιοχές", 1],
            "311": ["Δάσος πλατυφύλλων", 3],
            "312": ["Δάσος κωνοφόρων", 3],
            "313": ["Μικτό δάσος", 3],
            "321": ["Φυσικοί  βοσκότοποι", 2],
            "322": ["Θάμνοι και χερσότοποι", 2],
            "323": ["Σκληροφυλλική βλάστηση", 2],
            "324": ["Μεταβατικές δασώδεις θαμνώδεις εκτάσεις", 3],
            "331": ["Παραλίες, αμμόλοφοι, αμμουδιές", 3],
            "332": ["Απογυμνωμένοι βράχοι", 7],
            "333": ["Εκτάσεις με αραιή βλάστηση", 2],
            "334": ["Αποτεφρωμένες εκτάσεις", 6],
            "335": ["Παγετώνες και αέναο χιόνι", 7],
            "411": ["Βάλτοι στην ενδοχώρα", 7],
            "412": ["Τυρφώνες", 7],
            "421": ["Παραθαλάσσιοι βάλτοι", 7],
            "422": ["Αλυκές", 7],
            "423": ["Ζώνες που καλύπτονται από παλιρροιακά ύδατα", 7],
            "511": ["Υδατορρεύματα", 7],
            "512": ["Επιφάνειες στάσιμου ύδατος", 7],
            "521": ["Παράκτιες λιμνοθάλασσες", 7],
            "522": ["Εκβολές ποταμών", 7],
            "523": ["Θάλασσες και ωκεανοί", 7],
        }

        # Choose conditions

        # Retrieve the value mappings
        params_path = os.path.join(basePath, "parameters")

        conditions_index = self.parameterAsEnum(parameters, "Conditions", context)
        geo_corine_to_cn_dict = {}

        # Unfavorable
        if conditions_index == 0:
            conditions = "Δυσμενείς"
            with open(os.path.join(params_path, "unfavorable.csv"), "r",encoding="utf-8") as cond_file:
                reader = csv.reader(cond_file)
                geo_corine_to_cn_dict = {rows[0]: float(rows[1]) for rows in reader}

        elif conditions_index == 1:
            conditions = "Μέσες"
            with open(os.path.join(params_path, "mean.csv"), "r", encoding="utf-8") as cond_file:
                reader = csv.reader(cond_file)
                geo_corine_to_cn_dict = {rows[0]: float(rows[1]) for rows in reader}

        # Favorable Conditions
        else:
            conditions = "Ευμενείς"
            with open(os.path.join(params_path, "favorable.csv"), "r", encoding="utf-8") as cond_file:
                reader = csv.reader(cond_file)
                geo_corine_to_cn_dict = {rows[0]: float(rows[1]) for rows in reader}

        basin_area = None
        for f in self.parameterAsVectorLayer(
            parameters, "Watershed", context
        ).getFeatures():
            basin_area = f.geometry().area()

        corine_perc = defaultdict()

        cn_perc = defaultdict()

        for feat in cn_labels.getFeatures():
            try:
                cn = None
                geo = feat["MY_EPIKR1"]
                cor = feat["Code_18"]

                # Convert corine code to 1-7
                cor_1_7 = corine_to_1_7_dict[cor][1]
                corine_description = corine_to_1_7_dict[cor][0]

                # Convert soil/geology code to ABCD
                geo_abcd = geo_to_abcd_dict[geo]

                # Combine them
                geo_corine = str(cor_1_7) + geo_abcd

                # Convert to CN
                cn = geo_corine_to_cn_dict[geo_corine]

                perc = (feat.geometry().area() / basin_area) * 100
                perc = "%.3f" % round(perc, 5)

                # Update the Corine and CN dicts (for logging)
                if corine_description in corine_perc:
                    corine_perc[corine_description] += float(perc)
                else:
                    corine_perc[corine_description] = float(perc)

                if cn in cn_perc:
                    cn_perc[cn] += float(perc)
                else:
                    cn_perc[cn] = float(perc)

                out_feat = QgsFeature(out_fields)
                out_feat.setGeometry(feat.geometry())
                out_feat["Basin Percentage"] = perc
                out_feat["Corine_Code"] = float(cor)
                out_feat["CORINE Descr"] = corine_description
                out_feat["Geo_Code"] = geo
                out_feat["LandUse_Code(1_7)"] = cor_1_7
                out_feat["Hydro_Code(ABCD)"] = geo_abcd
                out_feat["CN"] = cn
                sink.addFeature(out_feat, QgsFeatureSink.FastInsert)
            except Exception:
                continue

        for key, value in corine_perc.items():
            log.write(str(key) + ": " + str(value) + "\n")

        # Write the CN log part
        log.write("\n\n\n")
        log.write("\n\n\n")
        log.write("Αριθμός Καμπύλης CN  /  % κάλυψη της λεκάνης \n")
        log.write("-----Συνθήκες: {}-----------\n".format(conditions))
        log.write(
            "-------------------------------------------------------------------------\n"
        )

        sum_cn_numerator = 0 # Αριθμητής
        sum_cn_denominator = 0 # Παρονομαστής
        for key, value in cn_perc.items():
            # Write a log entry for each CN and its %cover of the basin
            log.write(str(key) + ": " + str(value) + "\n")

            sum_cn_numerator += key * value
            sum_cn_denominator += value

        log.write("\n\n")
        sum_cn = sum_cn_numerator / sum_cn_denominator
        log.write("Συνισταμένη Τιμή CN (χωρικά σταθμισμένη): " + str(sum_cn))

        # Calculate and log urban cover
        log.write(
            "-------------------------------------------------------------------------\n"
        )
        log.write("Αστική Κάλυψη (κωδικοί Corine: 111-124, 141,142) \n")
        log.write("\n\n\n")

        urban_total = 0.000
        for key, value in corine_perc.items():
            if (
                key == "Συνεχής αστικός ιστός"
                or key == "Ασυνεχής αστικός ιστός"
                or key == "Βιομηχανικές ή εμπορικές ζώνες"
                or key == "Οδικά & σιδηροδρομικά δίκτυα"
                or key == "Ζώνες λιμένων"
                or key == "Αεροδρόμια"
                or key == "Περιοχές αστικού πρασίνου"
                or key == "Εγκαταστάσεις αθλητισμού και αναψυχής"
            ):
                log.write(str(key) + ": " + str(value) + "\n")
                urban_total += value
        log.write("Αστική Κάλυψη (%): " + str(urban_total))
        log.write("\n")
        log.write("Αστική Κάλυψη (0-1): " + str(urban_total / 100))

        log.close()
        # Calculate Total CN value

        # Return the results
        return {self.OUTPUT: dest_id}
