# -*- coding: utf-8 -*-
"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QDialog

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
)


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "pour_point_dialog.ui")
)


def tr(string):
    return QCoreApplication.translate("Processing", string)


class AddPourPointDialog(QDialog, FORM_CLASS):
    def __init__(self, iface):
        """Initialize the data settings dialog window."""
        super(AddPourPointDialog, self).__init__(iface.mainWindow())
        self.setupUi(self)
        self.crs_comboBox.addItem("GGRS87")
        self.crs_comboBox.addItem("WGS84")
        self.iface = iface

    def showEvent(self, event):
        """The dialog is being shown. We need to initialize it."""

        super(AddPourPointDialog, self).showEvent(event)

    def accept(self):
        """Called when the OK button has been pressed."""

        if self.crs_comboBox.currentText() == "GGRS87":
            uri = "point?crs=epsg:2100"
        else:
            uri = "point?crs=epsg:4326"

        ppLayer = QgsVectorLayer(uri, "Pour Point", "memory")
        prov = ppLayer.dataProvider()

        f = QgsFeature()
        f.setGeometry(
            QgsGeometry.fromPointXY(
                QgsPointXY(float(self.x_field.text()), float(self.y_field.text()))
            )
        )
        prov.addFeature(f)
        ppLayer.updateExtents()
        QgsProject.instance().addMapLayer(ppLayer)

        self.close()
