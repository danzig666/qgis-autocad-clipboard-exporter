from .autocad_clipboard_exporter import AutoCADClipboardExporter

def classFactory(iface):  # QGIS calls this
    return AutoCADClipboardExporter(iface)
