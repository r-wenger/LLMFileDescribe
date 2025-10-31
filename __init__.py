"""QGIS Plugin Implementation for LLMFileDescribe.

This module registers a simple plugin that adds a toolbar/action entry to QGIS. The
plugin opens a dialogue allowing the user to select a vector (SHP/GPKG) or raster
file, specify the Ollama model to use, et obtenir une description synthétique
via un modèle de langage. See `LLMFileDescribe.py` for the implementation of
the main logic.
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
import os.path

from .LLMFileDescribe import LLMFileDescribeDialog


class LLMFileDescribe:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('LLMFileDescribe', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # Always load the icon from the plugin directory.  We do not use
        # the Qt resource system here, so avoid `:/plugins/...` paths.
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), self.tr('LLM File Describe'), self.iface.mainWindow())
        self.action.setStatusTip(self.tr('Interroger un fichier via LLM'))
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.tr('&LLMFileDescribe'), self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if self.action:
            self.iface.removePluginMenu(self.tr('&LLMFileDescribe'), self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None

    def run(self):
        """Run method that performs all the real work."""
        dialog = LLMFileDescribeDialog(self.iface.mainWindow())
        dialog.exec_()


# QGIS calls classFactory to instantiate the plugin.  This function must
# exist at the package root.  It receives the QGIS interface and returns
# an instance of our plugin class.
def classFactory(iface):
    return LLMFileDescribe(iface)