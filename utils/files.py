import os
from qgis.core import QgsProject


def get_project_root():
    """
    Get the root path of the currently open QGIS project.
    """
    return QgsProject.instance().homePath()

def get_or_create_path(path):
    """
    Get or create a directory at the specified path.
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_plugin_output_dir(dirname="watershed_analysis_outputs"):
    """
    Get or create an output folder for the current project, where the plugin will store its outputs.
    """
    output_folder = os.path.join(get_project_root(), dirname)
    return get_or_create_path(output_folder)