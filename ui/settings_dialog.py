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


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "settings_dialog.ui")
)

corine_settings_location = os.path.join(
    os.path.dirname(__file__), "sets", "settings_corine.txt"
)
scs_settings_location = os.path.join(
    os.path.dirname(__file__), "sets", "settings_scs.txt"
)


def tr(string):
    return QCoreApplication.translate("Processing", string)


class WATSettingsDialog(QDialog, FORM_CLASS):
    def __init__(self, iface):
        """Initialize the data settings dialog window."""
        super(WATSettingsDialog, self).__init__(iface.mainWindow())
        self.setupUi(self)
        self.iface = iface

    def showEvent(self, event):
        """The dialog is being shown. We need to initialize it."""
        corine_path = open(corine_settings_location, "r")
        scs_path = open(scs_settings_location, "r")
        self.corine_dialog.setFilePath(corine_path.read())
        self.scs_dialog.setFilePath(scs_path.read())
        corine_path.close()
        scs_path.close()
        self.openConditionsSettings.clicked.connect(self.openConditionsFolder)
        super(WATSettingsDialog, self).showEvent(event)

    def accept(self):
        """Called when the OK button has been pressed."""

        new_corine_path = open(corine_settings_location, "w")
        new_corine_path.write(self.corine_dialog.filePath())
        new_corine_path.close()

        new_scs_path = open(scs_settings_location, "w")
        new_scs_path.write(self.scs_dialog.filePath())
        new_scs_path.close()
        self.close()

    def openConditionsFolder(self):
        try:
            import os

            path = os.path.join(os.path.dirname(__file__), "parameters")
            os.startfile(path)
        except Exception:
            import webbrowser

            webbrowser.open("file:///" + path)
