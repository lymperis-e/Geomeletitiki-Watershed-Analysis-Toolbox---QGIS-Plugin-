from qgis.core import QgsProject, QgsVectorLayer, Qgis
from qgis.gui import Qgis

def add_wfs_layers(iface):
    # Define the URL of the WFS layer
    land_cover_url = "http://mapsportal.ypen.gr/geoserver/ows?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=geonode:gr_clc2018"
    soil_url = "http://mapsportal.ypen.gr/geoserver/ows?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=geonode:edafmap_1997_7"
    
    # Check if layers are already loaded
    land_cover_layer, soil_layer = None, None
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == "CORINE_LC_2018":
            land_cover_layer = layer
        elif layer.name() == "SOIL_MAP_1997":
            soil_layer = layer
    
    if land_cover_layer and soil_layer:
        iface.messageBar().pushMessage(
            "Info", "WFS Layers already loaded", level=Qgis.Info
        )
        return land_cover_layer, soil_layer
    
    # Add the WFS layer to the project
    land_cover_layer = QgsVectorLayer(land_cover_url, "CORINE_LC_2018", "WFS")
    soil_layer = QgsVectorLayer(soil_url, "SOIL_MAP_1997", "WFS")
    
    if land_cover_layer.isValid() and soil_layer.isValid():
        QgsProject.instance().addMapLayer(land_cover_layer)
        QgsProject.instance().addMapLayer(soil_layer)
        iface.messageBar().pushMessage(
            "Success", "WFS Layers added successfully", level=Qgis.Info
        )
    else:
        iface.messageBar().pushMessage(
            "Error", "Failed to load WFS layer", level=Qgis.Critical
        )
        return None, None
    
    return land_cover_layer, soil_layer
        
