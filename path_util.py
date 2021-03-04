import os
import sys
pluginPath = os.path.dirname(__file__)

class utilProvider():
    soil_path = os.path.join(pluginPath, "data", "edafmap_1997_8.shp")
    corine_path = os.path.join(pluginPath, "data", "CLC12_GR.shp")

    def soil_path(self):
        return self.soil_path
    def cor_path(self):
        return self.cor_path