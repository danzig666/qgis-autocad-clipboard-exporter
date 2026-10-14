import os

from qgis.PyQt.QtWidgets import QAction, QInputDialog
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, QSettings

from .logic import (
    copy_selection_for_autocad, SETTINGS_SCOPE, SETTINGS_KEY_DECIMALS, DEFAULT_DECIMALS, TITLE,
)

MENU = "&AutoCAD Clipboard Exporter"


class AutoCADClipboardExporter:

    def __init__(self, iface_):
        self.iface = iface_
        self._actions = []

    def tr(self, text):
        return QCoreApplication.translate("AutoCADClipboardExporter", text)

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        self.act_copy = QAction(QIcon(icon_path),
                                self.tr("Copy Selection for AutoCAD"), self.iface.mainWindow())
        self.act_copy.setObjectName("AutoCADClipboardExporterCopy")
        self.act_copy.triggered.connect(lambda: copy_selection_for_autocad(self.iface))
        self.iface.addToolBarIcon(self.act_copy)
        self.iface.addPluginToMenu(self.tr(MENU), self.act_copy)
        self._actions.append(self.act_copy)

        self.act_dec = QAction(self.tr("Set Coordinate Decimals…"), self.iface.mainWindow())
        self.act_dec.triggered.connect(self._set_decimals)
        self.iface.addPluginToMenu(self.tr(MENU), self.act_dec)
        self._actions.append(self.act_dec)

    def unload(self):
        for a in self._actions:
            try:
                self.iface.removePluginMenu(self.tr(MENU), a)
                self.iface.removeToolBarIcon(a)
            except Exception:
                pass

    def _set_decimals(self):
        key = f"{SETTINGS_SCOPE}/{SETTINGS_KEY_DECIMALS}"
        cur = QSettings().value(key, DEFAULT_DECIMALS, type=int)
        val, ok = QInputDialog.getInt(self.iface.mainWindow(), self.tr(TITLE),
                                      self.tr("Decimal places for coordinates:"), cur, 0, 8)
        if ok:
            QSettings().setValue(key, val)
