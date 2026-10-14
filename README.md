<p align="center">
  <img src="autocad_clipboard_exporter/icon.png" width="96" alt="AutoCAD Clipboard Exporter icon">
</p>

<h1 align="center">AutoCAD Clipboard Exporter</h1>

<p align="center">
  Copy selected QGIS features and paste them straight into AutoCAD — no DXF export, no file juggling.<br>
  <a href="#magyar">🇭🇺 Magyar leírás lent</a>
</p>

---

## English

### What it does

Select features in QGIS, click **Copy Selection for AutoCAD**, then paste into the AutoCAD command line. The geometry appears in your drawing at its real coordinates.

- **Points** → AutoCAD `POINT`s
- **Lines** → 2D polylines (closed if the line is a ring)
- **Polygons** → closed 2D polylines (outer ring and holes)
- **Multi-part and curved geometries** are supported (curves are segmentized)
- Each QGIS layer becomes an **AutoCAD layer of the same name**
- Coordinates are in the **QGIS project CRS** (e.g. EOV / EPSG:23700), so set the project CRS to match your drawing
- The view **zooms to the pasted objects**, and the command line reports how many objects were created
- The whole paste is **one undo step** — a single `U` removes it

It is the counterpart of **AutoCAD Clipboard Importer**, which goes the other way (AutoCAD → QGIS).

### Requirements

- QGIS 3.34 or newer, including QGIS 4 (Qt6)
- AutoCAD with AutoLISP: full AutoCAD, or **AutoCAD LT 2024 or newer** (older LT versions have no LISP)

### Installation

1. Download `autocad_clipboard_exporter.zip` from the [latest release](https://github.com/danzig666/qgis-autocad-clipboard-exporter/releases/latest).
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**, choose the file, click **Install Plugin**.

### Usage

1. Select features on the active layer — or select several layers in the Layers panel to export the selected features of all of them.
2. Click the toolbar button (or **Plugins → AutoCAD Clipboard Exporter → Copy Selection for AutoCAD**).
3. In AutoCAD, **click into the command line** (not the drawing area!) and press **Ctrl+V**.

> Pasting into the drawing area would insert the clipboard as a text object instead of running it.

Coordinate precision (default: 3 decimals) can be changed under **Plugins → AutoCAD Clipboard Exporter → Set Coordinate Decimals…**

### Layer colors

New AutoCAD layers get the color of the QGIS symbol, chosen so that it stays visible on both white and black AutoCAD backgrounds:

| QGIS symbol | AutoCAD layer color |
|---|---|
| Polygon | outline (stroke) color; fill color if there is no outline |
| Line / point | symbol color |
| Mid-tone color (red, orange, green, blue…) | kept as true color |
| Very dark or very light color (black, white, cream, yellow, navy…) | color 7 — black on white, white on black background |
| Categorized / rule-based / other multi-symbol renderers | color 7 |

Layers that **already exist** in the drawing keep their color — the plugin never recolors your layers.

### How it works

The clipboard receives a short AutoLISP script that creates the objects with `entmake`. This is deliberate: a plain command script (`PLINE`, `-LAYER`, …) needs empty lines as Enter, but AutoCAD drops empty lines from a command-line paste, so such scripts get out of sync. `entmake` needs no Enter, is unaffected by object snaps, the UCS and dynamic input, does not change the current layer, and is much faster.

### Limitations

- 2D only — Z values are dropped
- No attributes, labels, hatches or line types
- Very large selections paste slowly (thousands of features take a while)

---

<a id="magyar"></a>

## Magyar

### Mire jó?

Jelölj ki elemeket QGIS-ben, kattints a **Copy Selection for AutoCAD** gombra, majd illeszd be az AutoCAD parancssorába. A geometria valós koordinátáival kerül a rajzba — nincs DXF export, nincs fájlkezelés.

- **Pontok** → AutoCAD `POINT`
- **Vonalak** → 2D polyline (zárt, ha a vonal gyűrű)
- **Poligonok** → zárt 2D polyline (külső határ és lyukak)
- **Többrészes és íves geometriák** is (az íveket szakaszokra bontja)
- Minden QGIS réteg **azonos nevű AutoCAD réteg** lesz
- A koordináták a **QGIS projekt koordináta-rendszerében** vannak (pl. EOV / EPSG:23700) — a projekt KRR egyezzen a rajzéval
- Beillesztés után a nézet **a beillesztett elemekre zoomol**, és a parancssor kiírja, hány objektum jött létre
- Az egész beillesztés **egy visszavonási lépés** — egyetlen `U` törli

Az **AutoCAD Clipboard Importer** párja, amely fordított irányban működik (AutoCAD → QGIS).

### Követelmények

- QGIS 3.34 vagy újabb, QGIS 4 (Qt6) is
- AutoLISP-et támogató AutoCAD: teljes AutoCAD, vagy **AutoCAD LT 2024 vagy újabb** (a régebbi LT-ben nincs LISP)

### Telepítés

1. Töltsd le az `autocad_clipboard_exporter.zip` fájlt a [legfrissebb kiadásból](https://github.com/danzig666/qgis-autocad-clipboard-exporter/releases/latest).
2. QGIS-ben: **Modulok → Modulok kezelése és telepítése → Telepítés ZIP-ből**, válaszd ki a fájlt, majd **Modul telepítése**.

### Használat

1. Jelölj ki elemeket az aktív rétegen — vagy jelölj ki több réteget a Rétegek panelen, ekkor mindegyik kijelölt elemei mennek.
2. Kattints az eszköztár gombjára (vagy **Modulok → AutoCAD Clipboard Exporter → Copy Selection for AutoCAD**).
3. AutoCAD-ben **kattints a parancssorba** (NE a rajzterületre!), és nyomj **Ctrl+V**-t.

> Ha a rajzterületre illeszted, az AutoCAD szövegobjektumként szúrja be a vágólap tartalmát, ahelyett hogy lefuttatná.

A koordináták pontossága (alapból 3 tizedes) a **Modulok → AutoCAD Clipboard Exporter → Set Coordinate Decimals…** menüben állítható.

### Rétegszínek

Az új AutoCAD rétegek a QGIS szimbólum színét kapják, úgy választva, hogy fehér és fekete AutoCAD háttéren is látható legyen:

| QGIS szimbólum | AutoCAD rétegszín |
|---|---|
| Poligon | körvonal színe; ha nincs körvonal, a kitöltés színe |
| Vonal / pont | a szimbólum színe |
| Közepes tónusú szín (piros, narancs, zöld, kék…) | megmarad (true color) |
| Nagyon sötét vagy nagyon világos szín (fekete, fehér, krém, sárga, sötétkék…) | 7-es szín — fehér háttéren fekete, feketén fehér |
| Kategorizált / szabály alapú / egyéb többszimbólumos megjelenítés | 7-es szín |

A rajzban **már létező** rétegek színe nem változik — a modul soha nem színezi át a meglévő rétegeidet.

### Hogyan működik?

A vágólapra egy rövid AutoLISP szkript kerül, amely `entmake`-kel hozza létre az objektumokat. Ez szándékos: egy sima parancsszkript (`PLINE`, `-LAYER`, …) üres sorokkal nyomna Entert, de az AutoCAD parancssori beillesztéskor eldobja az üres sorokat, így az ilyen szkript elcsúszik. Az `entmake`-nek nem kell Enter, nem zavarja a tárgyraszter, az FKR és a dinamikus bevitel, nem váltja át az aktuális réteget, és sokkal gyorsabb.

### Korlátok

- Csak 2D — a Z értékek elvesznek
- Nincsenek attribútumok, feliratok, sraffozás, vonaltípusok
- Nagyon nagy kijelölés lassan illeszthető be (több ezer elem eltart egy darabig)
