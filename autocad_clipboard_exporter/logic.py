# Selected QGIS features -> AutoLISP script on the clipboard.
# Paste the result into the AutoCAD command line (not the drawing area).
#
# Why LISP instead of plain commands: AutoCAD drops empty lines from a command-line
# paste, so a script can't press a bare Enter (needed to end PLINE / -LAYER) and
# gets out of sync. entmake needs no Enter at all, ignores OSNAP/UCS/dynamic input,
# auto-creates missing layers and doesn't change the current layer.
# Requires AutoLISP: full AutoCAD, or AutoCAD LT 2024+.
#
# Script layout:
# - (command "_.UNDO" "_BE") ... (command "_.UNDO" "_E") -> a single U undoes it
# - three small helpers: qgis:lay (new layer + true color), qgis:pl (LWPOLYLINE), qgis:pt (POINT)
# - one helper call per part; vertex lists span several lines (the LISP reader continues)
# - qgis:n counts successful entmakes; at the end: ZOOM to the pasted extent + summary line

import re

from qgis.PyQt.QtCore import QCoreApplication, QSettings, Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsWkbTypes, QgsCoordinateTransform,
    QgsSingleSymbolRenderer, QgsGeometry, QgsRectangle, Qgis,
    QgsLineSymbolLayer, QgsSimpleFillSymbolLayer,
)

SETTINGS_SCOPE = "plugins/AutoCADClipboardExporter"
SETTINGS_KEY_DECIMALS = "decimals"
DEFAULT_DECIMALS = 3

TITLE = "AutoCAD Clipboard Exporter"

VERTICES_PER_LINE = 8

# characters AutoCAD forbids in layer names (also keeps the LISP string literal safe)
_BAD_LAYER_CHARS = re.compile(r'[<>/\\":;?*|,=`\x00-\x1f]+')

_LISP_HEADER = [
    '(command "_.UNDO" "_BE")',
    '(setq qgis:n 0)',
    # new layers only (existing layer colors in the drawing are left alone);
    # inside (command) the "" Enter is reliable, unlike in a pasted command script
    '(defun qgis:lay (n rgb) (if (not (tblsearch "LAYER" n)) (progn (command "_.-LAYER" "_N" n "")'
    ' (if rgb (command "_.-LAYER" "_C" "_T" rgb n "")))) (princ))',
    '(defun qgis:pl (n c pts) (if (entmake (append (list \'(0 . "LWPOLYLINE") \'(100 . "AcDbEntity") (cons 8 n)'
    ' \'(100 . "AcDbPolyline") (cons 90 (length pts)) (cons 70 c)) (mapcar \'(lambda (p) (cons 10 p)) pts)))'
    ' (setq qgis:n (1+ qgis:n))) (princ))',
    '(defun qgis:pt (n p) (if (entmake (list \'(0 . "POINT") (cons 8 n) (cons 10 p))) (setq qgis:n (1+ qgis:n))) (princ))',
]


def tr(text):
    return QCoreApplication.translate("AutoCADClipboardExporter", text)


def _decimals() -> int:
    return QSettings().value(f"{SETTINGS_SCOPE}/{SETTINGS_KEY_DECIMALS}", DEFAULT_DECIMALS, type=int)


def _acad_layer_name(name: str) -> str:
    clean = _BAD_LAYER_CHARS.sub("_", name).strip(" _")
    return clean[:255] or "QGIS"


def _fmt(v: float, dec: int) -> str:
    """LISP real: always has a decimal point (integers would be rejected by entmake)."""
    s = f"{v:.{max(dec, 1)}f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return "0.0" if s == "-0.0" else s


def _xy(p, dec: int) -> str:
    return f"({_fmt(p.x(), dec)} {_fmt(p.y(), dec)})"


def _symbol_outline_color(symbol):
    """Color of what AutoCAD will get: the outline for polygons, the symbol color otherwise."""
    if symbol.type() == Qgis.SymbolType.Fill:
        for sl in symbol.symbolLayers():
            if not sl.enabled():
                continue
            if isinstance(sl, QgsLineSymbolLayer):  # e.g. "Outline: Simple line"
                return sl.color()
            if isinstance(sl, QgsSimpleFillSymbolLayer):
                if sl.strokeStyle() != Qt.PenStyle.NoPen and sl.strokeColor().alpha() > 0:
                    return sl.strokeColor()
    return symbol.color()


def _visible_rgb(c):
    """'r,g,b' for mid-tone colors; None (-> AutoCAD color 7) for colors that are too light
    or too dark: 7 shows black on a white and white on a black background."""
    luma = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
    if luma < 60 or luma > 195:
        return None
    return f"{c.red()},{c.green()},{c.blue()}"


def _layer_line(layer: QgsVectorLayer, name: str) -> str:
    rgb = None
    renderer = layer.renderer()
    if isinstance(renderer, QgsSingleSymbolRenderer) and renderer.symbol():
        rgb = _visible_rgb(_symbol_outline_color(renderer.symbol()))
    arg = f'"{rgb}"' if rgb else "nil"
    return f'(qgis:lay "{name}" {arg})'


def _pline_lines(points, closed: bool, lname: str, dec: int) -> list:
    if closed and len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 2:
        return []
    flag = 1 if closed and len(points) > 2 else 0
    out = [f'(qgis:pl "{lname}" {flag} \'(']
    for i in range(0, len(points), VERTICES_PER_LINE):
        out.append(" ".join(_xy(p, dec) for p in points[i:i + VERTICES_PER_LINE]))
    out.append("))")
    return out


def _geometry_lines(geom: QgsGeometry, lname: str, dec: int) -> list:
    if geom is None or geom.isEmpty():
        return []
    if QgsWkbTypes.isCurvedType(geom.wkbType()):
        geom = QgsGeometry(geom)
        geom.convertToStraightSegment()

    gtype = geom.type()
    multi = geom.isMultipart()
    out = []

    if gtype == Qgis.GeometryType.Point:
        pts = geom.asMultiPoint() if multi else [geom.asPoint()]
        for p in pts:
            out.append(f'(qgis:pt "{lname}" \'({_fmt(p.x(), dec)} {_fmt(p.y(), dec)} 0.0))')

    elif gtype == Qgis.GeometryType.Line:
        lines = geom.asMultiPolyline() if multi else [geom.asPolyline()]
        for line in lines:
            closed = len(line) > 3 and line[0] == line[-1]
            out += _pline_lines(line, closed, lname, dec)

    elif gtype == Qgis.GeometryType.Polygon:
        polys = geom.asMultiPolygon() if multi else [geom.asPolygon()]
        for poly in polys:
            for ring in poly:  # outer ring + holes, each as closed polyline
                out += _pline_lines(ring, True, lname, dec)

    return out


def _target_layers(iface) -> list:
    layers = [l for l in iface.layerTreeView().selectedLayers() if isinstance(l, QgsVectorLayer)]
    active = iface.activeLayer()
    if not layers and isinstance(active, QgsVectorLayer):
        layers = [active]
    return [l for l in layers if l.selectedFeatureCount() > 0]


def build_script(layers, dest_crs, dec: int):
    ctx = QgsProject.instance().transformContext()
    lines = list(_LISP_HEADER)
    n_feats = n_ents = 0
    extent = QgsRectangle()
    extent.setNull()

    for layer in layers:
        xform = None
        if dest_crs.isValid() and layer.crs().isValid() and layer.crs() != dest_crs:
            xform = QgsCoordinateTransform(layer.crs(), dest_crs, ctx)
        lname = _acad_layer_name(layer.name())

        layer_lines = []
        for f in layer.getSelectedFeatures():
            g = f.geometry()
            if g is None or g.isEmpty():
                continue
            g = QgsGeometry(g)
            if xform:
                g.transform(xform)
            ents = _geometry_lines(g, lname, dec)
            if ents:
                layer_lines += ents
                extent.combineExtentWith(g.boundingBox())
                n_feats += 1
                n_ents += sum(1 for s in ents if s.startswith("(qgis:p"))

        if layer_lines:
            lines += [_layer_line(layer, lname)] + layer_lines

    if not extent.isNull():
        # 5% margin, at least 10 drawing units (single point selection)
        pad = max(extent.width(), extent.height()) * 0.05 + 10
        lo = f"(trans '({_fmt(extent.xMinimum() - pad, dec)} {_fmt(extent.yMinimum() - pad, dec)} 0.0) 0 1)"
        hi = f"(trans '({_fmt(extent.xMaximum() + pad, dec)} {_fmt(extent.yMaximum() + pad, dec)} 0.0) 0 1)"
        lines.append(f'(command "_.ZOOM" "_W" {lo} {hi})')
    lines += [
        '(command "_.UNDO" "_E")',
        f'(princ (strcat "\\nQGIS: " (itoa qgis:n) "/{n_ents} objektum létrehozva."))',
        '(princ)',
    ]
    return "\n".join(lines) + "\n", n_feats, n_ents


def copy_selection_for_autocad(iface):
    mb = iface.messageBar()
    layers = _target_layers(iface)
    if not layers:
        mb.pushWarning(tr(TITLE), tr("Előbb jelölj ki elemeket (az aktív rétegen, vagy a Rétegek panelen kijelölt rétegeken)."))
        return

    dest_crs = QgsProject.instance().crs()
    text, n_feats, n_ents = build_script(layers, dest_crs, _decimals())
    if n_feats == 0:
        mb.pushWarning(tr(TITLE), tr("A kijelölt elemeknek nincs használható geometriája."))
        return

    QApplication.clipboard().setText(text)
    mb.pushMessage(
        tr(TITLE),
        tr(f"{n_feats} elem ({n_ents} AutoCAD objektum, {dest_crs.authid() or 'projekt KRR'}) a vágólapon. "
           f"AutoCAD-ben kattints a parancssorba (NE a rajzterületre), majd nyomj Ctrl+V-t. "
           f"Visszavonás egy lépésben: U."),
        Qgis.MessageLevel.Success, 20
    )
