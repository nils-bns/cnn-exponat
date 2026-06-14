# Widgets - Technische Referenz

Dieses Dokument beschreibt alle bestehenden Widgets im `view/widgets/`-Package. Es dokumentiert den Ist-Zustand: Aufbau, Attribute, Signals, Datenfluss und Zusammenspiel der einzelnen Komponenten.

---

## Inhaltsverzeichnis

1. [Package-Struktur](#package-struktur)
2. [BaseOverlayWidget](#baseoverlaywidget)
3. [CameraDisplayWidget](#cameradisplaywidget)
4. [LayerButton](#layerbutton)
5. [ArchLayerButton](#archlayerbutton)
6. [LayerButtonBar](#layerbuttonbar)
7. [InfoPanel](#infopanel)
8. [AboutWidget](#aboutwidget)
9. [OutputRankingWidget](#outputrankingwidget)
10. [GradCAMWidget](#gradcamwidget)
11. [TitleTextWidget](#titletextwidget)
12. [GradCAMSubtitleWidget](#gradcamsubtitlewidget)
13. [Seiteneffekte](#seiteneffekte)

---

## Package-Struktur

```
widgets/
    __init__.py                 # Re-Export aller Widgets
    base_overlay.py             # Basisklasse fuer transparente Overlays
    camera_display.py           # Kamera-Display (Visitor + Admin)
    layer_button.py             # Einzelner Layer-Button (checkable, Pulse)
    layer_button_bar.py         # Horizontale Button-Leiste
    info_panel.py               # Info-Panel fuer Layer-Beschreibungen
    about_widget.py             # About-Slideshow (3 Seiten, Swipe)
    output_ranking_widget.py    # Top-3-Predictions als Balkendiagramm
    gradcam_widget.py           # GradCAM-Visualisierung mit Kreis-Maskierung
    title_text_widget.py        # Bilingualer Titel-Text (Visitor Mode)
    gradcam_subtitle_widget.py  # Bilingualer GradCAM-Untertitel (Visitor Mode)
    helpers/
        __init__.py             # Re-Export: ArchLayerButton
        arch_layer_button.py    # LayerButton mit QPainter-Rendering
```

Alle Widgets sind ueber `view.widgets` importierbar:

```python
from view.widgets import (
    BaseOverlayWidget, CameraDisplayWidget, LayerButton,
    LayerButtonBar, InfoPanel, AboutWidget,
    OutputRankingWidget, GradCAMWidget, TitleTextWidget,
    GradCAMSubtitleWidget,
)
from view.widgets.helpers import ArchLayerButton
```

---

## BaseOverlayWidget

**Datei:** `base_overlay.py`
**Basisklasse:** `QWidget`
**Verwendung:** Basisklasse fuer alle transparenten Overlay-Widgets im Visitor Mode.

### Zweck

Stellt gemeinsame Funktionalitaet fuer Widgets bereit, die als semi-transparente Overlays ueber dem Kamera-Feed schweben. Setzt den transparenten Hintergrund und bietet Fade-Animationen.

### Konstruktor

| Parameter | Typ               | Beschreibung                  |
|-----------|--------------------|-------------------------------|
| `parent`  | `QWidget \| None` | Parent-Widget (optional)      |

### Attribute

| Attribut            | Typ                          | Beschreibung                             |
|---------------------|------------------------------|------------------------------------------|
| `_opacity_effect`   | `QGraphicsOpacityEffect`     | Opacity-Effekt fuer Fade-Animationen      |
| `_fade_animation`   | `QPropertyAnimation \| None` | Aktive Fade-Animation (oder None)        |

### Konfiguration im Konstruktor

- `WA_TranslucentBackground` wird gesetzt (transparenter Widget-Hintergrund)
- `WA_TransparentForMouseEvents` wird auf `False` gesetzt (Mouse-Events werden gefangen, nicht durchgelassen)
- `QGraphicsOpacityEffect` mit Opacity 1.0 wird als Graphics-Effect registriert

### Methoden

| Methode                                 | Beschreibung                                                    |
|-----------------------------------------|-----------------------------------------------------------------|
| `fade_in(duration=300)`                 | Fade-In-Animation (Opacity 0.0 nach 1.0)                       |
| `fade_out(duration=300)`                | Fade-Out-Animation (Opacity 1.0 nach 0.0)                      |
| `set_transparent_for_mouse(transparent)`| Steuert ob Mouse-Events durchgelassen oder gefangen werden      |
| `update_language(language)`             | Stub-Methode, von Subklassen ueberschrieben fuer Sprachwechsel |

### Fade-Animation Details

`_animate_opacity()` stoppt eine laufende Animation, erstellt eine neue `QPropertyAnimation` auf die `opacity`-Property des `QGraphicsOpacityEffect` und startet sie. Die Easing-Kurve ist `InOutQuad`. Bei Abschluss wird das Signal `fade_finished` emittiert.

### Signals

| Signal           | Parameter | Beschreibung                         |
|------------------|-----------|--------------------------------------|
| `fade_finished`  | --        | Emittiert nach Abschluss einer Fade-Animation |

### Subklassen

`LayerButtonBar`, `InfoPanel`, `AboutWidget`, `OutputRankingWidget`, `GradCAMWidget`, `TitleTextWidget` erben von `BaseOverlayWidget`.

---

## CameraDisplayWidget

**Datei:** `camera_display.py`
**Basisklasse:** `QLabel`
**Verwendung:** Kamera-Feed-Anzeige in Visitor Mode und Admin Mode.

### Zweck

Zeigt NumPy-RGB-Arrays als Pixmaps an. Wird von beiden Modi verwendet -- im Visitor Mode als Fullscreen-Display, im Admin Mode als Live-Vorschau.

### Konstruktor

| Parameter | Typ               | Beschreibung                  |
|-----------|--------------------|-------------------------------|
| `parent`  | `QWidget \| None` | Parent-Widget (optional)      |

### Konfiguration im Konstruktor

- Alignment auf `AlignCenter`
- ObjectName auf `"camera-display"` (fuer QSS-Selektor `QLabel#camera-display` in `base.qss`)
- Platzhalter-Text: "Warte auf Kamera-Feed..."

### Slots

| Slot                            | Parameter      | Beschreibung                                   |
|---------------------------------|----------------|-------------------------------------------------|
| `update_frame(np.ndarray)`      | `np.ndarray`   | Konvertiert RGB-Array zu Pixmap und zeigt es an |

### Datenfluss

```
CameraThread.frame_ready(np.ndarray)
    |
    +--> CameraDisplayWidget.update_frame(frame)
            |
            +--> numpy_to_qpixmap(frame, self.size())
            |       +--> QImage aus NumPy-Daten erstellen
            |       +--> QPixmap aus QImage erstellen
            |       +--> Skalierung auf Label-Groesse (Aspect-Ratio erhalten)
            |       +--> Zentriertes Cropping auf exakte Groesse
            |
            +--> self.setPixmap(pixmap)
```

Die Konvertierung delegiert an `view.utils.frame_converter.numpy_to_qpixmap()`. Die Zielgroesse ist immer die aktuelle Widget-Groesse (`self.size()`), sodass das Bild bei Fensteraenderungen automatisch mitskaliert.

### Fehlerbehandlung

Falls die Konvertierung fehlschlaegt, wird der Text "Fehler bei Frame-Anzeige" gesetzt und ein Error geloggt.

---

## LayerButton

**Datei:** `layer_button.py`
**Basisklasse:** `QPushButton`
**Verwendung:** Einzelner Button fuer Layer-Navigation. Wird von `ArchLayerButton` erweitert.

### Zweck

Touch-optimierter Button fuer die Layer-Auswahl. Checkable (Radio-Button-Verhalten innerhalb der `LayerButtonBar`). Bietet eine Pulse-Animation fuer visuelles Feedback.

### Konstruktor

| Parameter      | Typ            | Beschreibung                               |
|----------------|----------------|--------------------------------------------|
| `layer_name`   | `str`          | Interner Layer-Name (z.B. `"layer1"`)       |
| `display_text` | `str \| None`  | Angezeigter Text (Fallback: layer_name.upper()) |
| `parent`       | `QWidget`      | Parent-Widget                              |

### Konfiguration im Konstruktor

- Mindestgroesse aus `BUTTON_DIMS` (150x80 px)
- `setCheckable(True)` fuer Radio-Button-Verhalten
- Font: Consolas, Groesse aus `FONT_SIZES.large` (18pt), Bold
- ObjectName: `"layer-button"` (fuer QSS-Selektor in `base.qss`)
- `clicked`-Signal mit `_on_clicked()` verbunden

### Attribute

| Attribut              | Typ                                  | Beschreibung                              |
|-----------------------|--------------------------------------|-------------------------------------------|
| `_layer_name`         | `str`                                | Interner Layer-Name                       |
| `_base_size`          | `QSize \| None`                      | Erfasste Basisgroesse fuer Pulse-Animation|
| `_pulse_scale_value`  | `float`                              | Aktueller Skalierungsfaktor (1.0 = normal)|
| `_pulse_animation`    | `QSequentialAnimationGroup \| None`  | Laufende Pulse-Animation                  |

### Signals

| Signal                  | Parameter | Beschreibung                              |
|-------------------------|-----------|-------------------------------------------|
| `layer_selected(str)`   | `str`     | Emittiert bei Klick mit dem Layer-Namen   |

### Methoden

| Methode               | Beschreibung                                                    |
|-----------------------|-----------------------------------------------------------------|
| `set_active(active)`  | Setzt checked-Status                                            |
| `capture_base_size()` | Erfasst aktuelle Groesse als Basis fuer Pulse (nach Layout-Finalisierung) |
| `start_pulse()`       | Startet periodische Groessenaenderung (10%, 2s Zyklus, endlos)  |
| `stop_pulse()`        | Stoppt Animation und stellt Basisgroesse wieder her             |

### Pulse-Animation

Die Pulse-Animation ist eine `QSequentialAnimationGroup` aus zwei `QPropertyAnimation`-Objekten auf die Custom-Property `pulse_scale`:

1. Grow: 1.0 nach 1.1 in 1000ms (InOutSine)
2. Shrink: 1.1 nach 1.0 in 1000ms (InOutSine)
3. Loop-Count: -1 (endlos)

Der Setter `_set_pulse_scale()` berechnet die neue Groesse relativ zur `_base_size` und ruft `setFixedSize()` auf. Voraussetzung: `capture_base_size()` muss vorher aufgerufen worden sein.

### Properties

| Property      | Typ     | Beschreibung                              |
|---------------|---------|-------------------------------------------|
| `layer_name`  | `str`   | Read-only, gibt internen Layer-Namen zurueck |
| `pulse_scale` | `float` | Read/Write, steuert Skalierungsfaktor     |

---

## ArchLayerButton

**Datei:** `widgets/helpers/arch_layer_button.py`
**Basisklasse:** `LayerButton`
**Verwendung:** Button mit CNN-Architektur-Visualisierung. Wird von der `LayerButtonBar` anstelle des Basis-`LayerButton` verwendet.

### Zweck

Zeichnet eine stilisierte CNN-Architektur mit Knoten und Verbindungslinien im Cyberpunk-Stil. Das komplette Rendering erfolgt per `QPainter` in `paintEvent()`. QSS-Styling des Basis-`LayerButton` wird vollstaendig ueberschrieben.

### Konstruktor

| Parameter      | Typ    | Beschreibung                              |
|----------------|--------|-------------------------------------------|
| `layer_name`   | `str`  | Interner Layer-Name                       |
| `display_text` | `str`  | Angezeigter Text                          |
| `num_nodes`    | `int`  | Anzahl der Knoten fuer diesen Layer        |
| `parent`       | --     | Parent-Widget (optional)                   |

### Zusaetzliche Attribute

| Attribut      | Typ    | Beschreibung                                |
|---------------|--------|----------------------------------------------|
| `_num_nodes`  | `int`  | Anzahl der dargestellten Knoten              |
| `_hovered`    | `bool` | Hover-Status (Klassen-Variable, Default False) |

### Rendering (paintEvent)

Das Rendering erfolgt in mehreren Schichten:

1. **Hintergrund-Gradient:** Vertikaler Gradient (oben dunkel, unten dunkler). Farben zustandsabhaengig:
   - Default: `CYBERPUNK_BG_TOP` / `CYBERPUNK_BG_BOT`
   - Hover: `ARCH_LAYER_BG_HOVER_TOP` / `ARCH_LAYER_BG_HOVER_BOT`
   - Checked: `ARCH_LAYER_BG_CHECKED_TOP` / `ARCH_LAYER_BG_CHECKED_BOT`

2. **Border:** Abgerundetes Rechteck mit zustandsabhaengiger Farbe und Alpha:
   - Default/Hover: Cyan-basiert, Alpha 80 (Default) bzw. 180 (Hover)
   - Checked: Magenta-basiert, Alpha 180

3. **Scan-Lines:** Horizontale Linien alle `scan_line_step` Pixel (4px). Farbe: Weiss mit Alpha 8. Rein dekorativ.

4. **Knoten:** Vertikale Spalte am linken Rand (X-Position: `node_x` = 22px). Die Knoten werden vertikal zentriert mit `node_spacing_preferred` (12px) Abstand. Bei vielen Knoten wird der Abstand reduziert, um in die Button-Hoehe zu passen.

5. **Verbindungslinien:** Von jedem Knoten zum rechten Rand. Die Zielanzahl ist `max(3, num_nodes // 2)`. Farbe: Akzentfarbe mit Alpha 35.

6. **Glow-Effekte:** Radialer Gradient hinter jedem Knoten (Radius: `node_radius * 4`). Akzentfarbe mit Alpha 50 im Zentrum, transparent am Rand.

7. **Knoten-Zeichnung:** Kreise mit Outline (Akzentfarbe, Alpha 220) und Fuellung (Akzentfarbe, Alpha 60).

8. **Label:** Text rechts unten. Font: Consolas, 10pt, Bold. Farbe: Akzentfarbe.

### Zustandsfarben

| Zustand   | Akzentfarbe     | Hintergrund                        |
|-----------|------------------|------------------------------------|
| Default   | Cyan (#00f0ff)   | Dunkel (#0a0e1a / #050810)        |
| Hover     | Bright Cyan (#33ffff) | Etwas heller (#0f1a2e / #060d1a) |
| Checked   | Magenta (#ff00aa)| Violett-getönt (#1a0a2e / #0d0520)|

### Hover-Tracking

`QPushButton` hat kein eingebautes `_hovered`-Flag. `ArchLayerButton` implementiert `enterEvent()` und `leaveEvent()`, die `_hovered` setzen und `update()` aufrufen (triggert Neuzeichnung).

### Zeichen-Konstanten

Alle Werte stammen aus `ARCH_LAYER_BTN_DIMS` in `dimensions.py`:

| Konstante               | Wert  | Beschreibung                        |
|--------------------------|-------|--------------------------------------|
| `node_radius`            | 4     | Radius der Knoten-Kreise            |
| `node_x`                 | 22    | X-Position der Knoten-Spalte        |
| `node_spacing_preferred` | 12    | Bevorzugter Abstand zwischen Knoten |
| `margin_vertical`        | 10    | Vertikaler Rand oben/unten          |
| `scan_line_step`         | 4     | Abstand zwischen Scan-Lines         |
| `border_radius`          | 8     | Abrundung des Hintergrund-Rechtecks |
| `label_font_size`        | 10    | Font-Groesse des Labels             |
| `label_font_family`      | "Consolas" | Font-Familie des Labels        |

---

## LayerButtonBar

**Datei:** `layer_button_bar.py`
**Basisklasse:** `BaseOverlayWidget`
**Verwendung:** Horizontale Button-Leiste fuer Layer-Navigation im Visitor Mode.

### Zweck

Erstellt eine Reihe von `ArchLayerButton`-Instanzen, verwaltet den aktiven Button (Radio-Button-Verhalten) und orchestriert die Pulse-Animation auf dem jeweils naechsten Button.

### Konstruktor

| Parameter        | Typ                          | Beschreibung                                         |
|------------------|------------------------------|------------------------------------------------------|
| `layer_names`    | `list[str]`                  | Liste der Layer-Namen (z.B. `["conv1", "layer1", ...]`) |
| `button_labels`  | `dict[str, dict[str, str]]`  | Bilinguale Labels: `{"de": {"conv1": "Conv 1", ...}, "en": {...}}` |
| `parent`         | `QWidget`                    | Parent-Widget (optional)                             |

### Attribute

| Attribut           | Typ                         | Beschreibung                                      |
|--------------------|-----------------------------|---------------------------------------------------|
| `_buttons`         | `dict[str, LayerButton]`    | Mapping Layer-Name zu Button-Instanz               |
| `_all_labels`      | `dict[str, dict[str, str]]` | Bilinguale Labels (gespeichert fuer Sprachwechsel) |
| `_layer_order`     | `list[str]`                 | Reihenfolge der Layer (fuer Pulse-Berechnung)      |
| `_pulsing_button`  | `LayerButton \| None`       | Aktuell pulsierender Button                        |
| `_pulse_ready`     | `bool`                      | Pulse-System initialisiert?                        |
| `_pending_active`  | `str \| None`               | Gepufferter Layer falls Pulse noch nicht bereit    |

### Signals

| Signal                | Parameter | Beschreibung                              |
|-----------------------|-----------|-------------------------------------------|
| `layer_selected(str)` | `str`     | Emittiert bei Button-Klick mit Layer-Name |
| `layout_ready`        | --        | Emittiert nach Pulse-System-Initialisierung (Container-Resize abgeschlossen) |

### Knoten-Anzahl pro Layer

Die Anzahl der Knoten fuer die Architektur-Visualisierung ist als Klassen-Variable `DEFAULT_NODE_COUNTS` hinterlegt:

| Layer    | Knoten |
|----------|--------|
| `conv1`  | 12     |
| `layer1` | 8      |
| `layer2` | 6      |
| `layer3` | 4      |
| `layer4` | 1      |

### Container-Wrapping

Jeder `ArchLayerButton` ist in einen `QWidget`-Container eingebettet. Der Container hat eine feste Groesse, die der maximalen Pulse-Groesse entspricht (110% der Basisgroesse + 6px Puffer). Dadurch veraendert die Pulse-Animation die aeussere Layout-Geometrie nicht -- der Button pulsiert innerhalb seines Containers.

### Pulse-System

Die Initialisierung des Pulse-Systems ist per `QTimer.singleShot(0, _init_pulse_system)` verzoegert. Der Grund: Zum Zeitpunkt des Konstruktors hat Qt die Layout-Groessen noch nicht finalisiert. `button.size()` wuerde falsche Werte liefern.

Ablauf von `_init_pulse_system()`:
1. `capture_base_size()` auf jedem Button aufrufen
2. Container-Groesse auf `base * 1.1 + 6` setzen
3. `_pulse_ready = True` setzen
4. `layout_ready` emittieren (Parent repositioniert Overlays)
5. Falls ein `_pending_active` existiert: Pulse starten

### Pulse-Orchestrierung

`_start_pulse_on_next(active_layer)`:
1. Aktuellen Pulse stoppen (falls vorhanden)
2. Index des aktiven Layers in `_layer_order` finden
3. Naechsten Index berechnen (Wrap-Around via Modulo)
4. `start_pulse()` auf dem naechsten Button aufrufen

Das bedeutet: Der Button, der als naechstes vom Besucher angeklickt werden soll, pulsiert als visuelle Anleitung.

### Methoden

| Methode                      | Beschreibung                                                    |
|------------------------------|-----------------------------------------------------------------|
| `set_active_layer(layer)`    | Setzt checked-Status, startet Pulse auf naechstem Button       |
| `get_active_layer()`         | Gibt Namen des aktuell aktiven Layers zurueck (oder None)      |
| `update_language(language)`  | Aktualisiert Button-Texte aus `_all_labels[language]`          |

### Datenfluss

```
User klickt ArchLayerButton
    |
    +--> ArchLayerButton.clicked (QPushButton-Signal)
    |
    +--> LayerButtonBar._on_button_clicked(layer_name)
            |
            +--> set_active_layer(layer_name)
            |       +--> Alle Buttons: setChecked(name == layer_name)
            |       +--> _start_pulse_on_next(layer_name)
            |               +--> Stoppe aktuellen Pulse
            |               +--> Starte Pulse auf naechstem Button
            |
            +--> layer_selected.emit(layer_name)
                    |
                    +--> VisitorModeWidget._on_layer_selected(layer_name)
```

---

## InfoPanel

**Datei:** `info_panel.py`
**Basisklasse:** `BaseOverlayWidget`
**Verwendung:** Overlay-Panel fuer Layer-Beschreibungstexte im Visitor Mode.

### Zweck

Zeigt HTML-formatierten Text mit semi-transparentem Cyberpunk-Hintergrund. Wird bei Layer-Wechsel und Sprachwechsel mit neuem Inhalt befuellt.

### Konstruktor

| Parameter | Typ               | Beschreibung                  |
|-----------|--------------------|-------------------------------|
| `parent`  | `QWidget \| None` | Parent-Widget (optional)      |

### Attribute

| Attribut     | Typ         | Beschreibung                    |
|--------------|-------------|---------------------------------|
| `_text_edit` | `QTextEdit` | Read-only Text-Display          |

### Konfiguration im Konstruktor

- `QTextEdit` mit `setReadOnly(True)`
- ObjectName `"info-panel"` auf dem QTextEdit (fuer QSS)
- Document-Stylesheet: `body { font-family }` aus `FONT_SIZES.font_family` + `h2 { color }` aus `ARCH_LAYER_MAGENTA` (QTextEdit erbt font-family nicht aus QSS)
- Vertikale Scrollbar: bei Bedarf. Horizontale Scrollbar: nie.
- Layout-Padding aus `INFO_PANEL_DIMS.layout_padding` (6px), damit der in `paintEvent` gezeichnete Rand sichtbar bleibt

### Methoden

| Methode                 | Beschreibung                                    |
|-------------------------|-------------------------------------------------|
| `set_content(html)`     | Setzt HTML-formatierten Inhalt                  |
| `set_plain_text(text)`  | Setzt Plain-Text (ohne HTML)                    |
| `clear()`               | Leert den Inhalt                                |

### Custom Painting (paintEvent)

Der Hintergrund wird manuell gezeichnet:

1. **Gradient:** Vertikaler `QLinearGradient` von `CYBERPUNK_BG_TOP` (mit Alpha `INFO_PANEL_BG_OPACITY`) nach `CYBERPUNK_BG_BOT` (mit Alpha `INFO_PANEL_BG_OPACITY`).
2. **Border:** `CYBERPUNK_CYAN` mit Alpha `OVERLAY_BORDER_ALPHA` (80). Breite aus `INFO_PANEL_DIMS.border_width` (1.5px).
3. **Form:** Abgerundetes Rechteck mit `border_radius` 8px. 1px Inset (damit die Border-Linie innerhalb des Widgets bleibt).

### Datenfluss

```
VisitorModeWidget._on_layer_selected(layer_name)
    |
    +--> _update_layer_info(layer_name)
            |
            +--> LAYER_DESCRIPTIONS[_language][layer_name]
            |       +--> HTML-String aus media/content/info_panel_content.py
            |
            +--> InfoPanel.set_content(html)
                    |
                    +--> _text_edit.setHtml(html)
```

### Visibility-Steuerung

Das InfoPanel wird ausgeblendet, solange das AboutWidget geoeffnet ist:

```
AboutWidget.expanded_changed(True)
    |
    +--> VisitorModeWidget._on_about_expanded_changed(True)
            |
            +--> InfoPanel.setVisible(False)
```

---

## AboutWidget

**Datei:** `about_widget.py`
**Basisklasse:** `BaseOverlayWidget`
**Verwendung:** Aufklappbare Info-Slideshow im Visitor Mode.

### Zweck

Zeigt ein Info-Icon, das auf Klick einen Content-Bereich mit 3-Seiten-Slideshow oeffnet. Die Seiten enthalten HTML-Inhalte mit eingebetteten Logo-Bildern. Navigation ueber Pfeil-Buttons oder horizontale Swipe-Geste.

### Konstruktor

| Parameter | Typ               | Beschreibung                  |
|-----------|--------------------|-------------------------------|
| `parent`  | `QWidget \| None` | Parent-Widget (optional)      |

### Attribute

| Attribut              | Typ                    | Beschreibung                                |
|-----------------------|------------------------|----------------------------------------------|
| `_is_expanded`        | `bool`                 | Aufgeklappt oder zugeklappt                  |
| `_icon_button`        | `QPushButton`          | Info-Icon-Button                             |
| `_content_container`  | `QWidget`              | Container fuer Content (initial unsichtbar)  |
| `_page_stack`         | `QStackedWidget`       | 3-Seiten-Slideshow                           |
| `_page_indicator`     | `QLabel`               | Seitenindikator ("1/3", "2/3", "3/3")       |
| `_prev_button`        | `QPushButton`          | Vorherige-Seite-Button ("<")                 |
| `_next_button`        | `QPushButton`          | Naechste-Seite-Button (">")                  |
| `_all_pages`          | `dict[str, list[str]]` | Bilinguale Seiteninhalt-Referenz             |
| `_swipe_start_x`      | `float \| None`        | Start-X-Position fuer Swipe-Erkennung       |

### Konfiguration im Konstruktor

- Feste Breite: `ABOUT_DIMS.content_width` (300px)
- Icon: `info_icon.png`, Groesse aus `ABOUT_DIMS.icon_size` (36px), ObjectName `"about-icon-button"`
- Content-Container: Feste Hoehe `ABOUT_DIMS.content_height` (400px), ObjectName `"about-content-container"`, initial unsichtbar
- 3 `QTextEdit`-Seiten (read-only) in einem `QStackedWidget`, befuellt aus `PAGE_CONTENTS["de"]`, jeweils mit Document-Stylesheet fuer `font-family` aus `FONT_SIZES.font_family`
- Logo-Bilder (`logo0.jpg`, `logo1.jpg`) als `QTextDocument`-Ressourcen registriert
- Navigationspfeile als Overlays auf dem Content-Container (30x40px)
- Swipe-EventFilter auf dem `_page_stack` installiert

### Signals

| Signal                     | Parameter | Beschreibung                               |
|----------------------------|-----------|---------------------------------------------|
| `expanded_changed(bool)`   | `bool`    | True bei Expand, False bei Collapse         |

### Seitennavigation

- **Pfeile:** `_go_next()` und `_go_previous()` verwenden Modulo-Arithmetik fuer endlosen Wrap-Around (3 -> 1, 1 -> 3)
- **Swipe:** Horizontale Wischgeste auf dem Page-Stack. Start-Position bei `MouseButtonPress`, Auswertung bei `MouseButtonRelease`. Schwellenwert: 50px (`_SWIPE_THRESHOLD`). Links-Swipe = naechste Seite, Rechts-Swipe = vorherige Seite.
- **Seitenindikator:** Wird nach jedem Seitenwechsel aktualisiert (z.B. "2/3")

### Expand/Collapse

**Expand (`_expand()`):**
1. `_is_expanded = True`
2. Content-Container sichtbar machen
3. Navigationspfeile positionieren
4. `adjustSize()` aufrufen
5. Application-Level `eventFilter` installieren (fuer Click-Outside-to-Close)
6. `expanded_changed.emit(True)`

**Collapse (`_collapse()`):**
1. `_is_expanded = False`
2. Content-Container unsichtbar machen
3. Page-Stack auf Seite 0 zuruecksetzen
4. Seitenindikator aktualisieren
5. `adjustSize()` aufrufen
6. Application-Level `eventFilter` entfernen
7. `expanded_changed.emit(False)`

### Click-Outside-to-Close

Der `eventFilter()` wird auf Application-Level installiert und faengt alle `MouseButtonPress`-Events ab. Wenn der Klick ausserhalb des AboutWidget-Bereichs liegt (`self.rect().contains(local_pos)` ist False), wird `_collapse()` aufgerufen.

### Logo-Bilder

Die Bilder `logo0.jpg` und `logo1.jpg` aus `media/img/` werden als `QTextDocument.ResourceType.ImageResource` auf allen Seiten-Dokumenten registriert. Dadurch koennen sie im HTML ueber `<img src="logo0.jpg">` referenziert werden, ohne einen Dateipfad anzugeben.

### Datenfluss (Sprachwechsel)

```
VisitorModeWidget._on_language_toggled()
    |
    +--> AboutWidget.update_language("en")
            |
            +--> pages = _all_pages["en"]
            +--> Fuer jede Seite im Page-Stack:
                    page_widget.setHtml(pages[i])
```

---

## OutputRankingWidget

**Datei:** `output_ranking_widget.py`
**Basisklasse:** `BaseOverlayWidget`
**Verwendung:** Anzeige der Top-3-Klassifikationsergebnisse im Visitor Mode.

### Zweck

Zeigt Klassenname, proportionalen Balken und Prozentzahl fuer die drei wahrscheinlichsten ImageNet-Klassen. Das Widget ist initial unsichtbar und wird erst eingeblendet wenn die Top-1-Prediction einen Mindestwert ueberschreitet.

### Konstruktor

| Parameter | Typ               | Beschreibung                  |
|-----------|--------------------|-------------------------------|
| `parent`  | `QWidget \| None` | Parent-Widget (optional)      |

### Konstanten

| Konstante         | Wert | Beschreibung                                           |
|-------------------|------|--------------------------------------------------------|
| `MIN_CONFIDENCE`  | 0.1  | Minimale Top-1-Konfidenz fuer Widget-Sichtbarkeit (10%) |

### Attribute

| Attribut           | Typ              | Beschreibung                        |
|--------------------|------------------|-------------------------------------|
| `_name_labels`     | `list[QLabel]`   | 3 Labels fuer Klassennamen          |
| `_bar_widgets`     | `list[QWidget]`  | 3 Balken-Widgets (dynamische Breite)|
| `_percent_labels`  | `list[QLabel]`   | 3 Labels fuer Prozentzahlen         |
| `_title_label`     | `QLabel`         | Widget-Titel                        |
| `_language`        | `str`            | Aktuelle Sprache ("de" oder "en")   |

### Konfiguration im Konstruktor

- Feste Groesse: `OUTPUT_RANKING_DIMS.width` x `height` (250x120px)
- Initial unsichtbar (`setVisible(False)`)
- Layout: Titel + 3-Spalten-Grid (Name | Balken | Prozent)
- Name-Labels: Feste Breite 130px, ObjectName `"overlay-text"`, Farbe Cyan
- Percent-Labels: Feste Breite 40px, rechtsbuendig
- Balken: Feste Hoehe `bar_height` (16px), initiale Breite 0

### Slots

| Slot                                       | Parameter                    | Beschreibung                  |
|--------------------------------------------|------------------------------|-------------------------------|
| `update_predictions(list[tuple[str,float]])`| Liste von (Name, Wahrscheinlichkeit) | Aktualisiert Anzeige |

### Datenfluss

```
CameraThread.predictions_ready(predictions)
    |
    +--> OutputRankingWidget.update_predictions(predictions)
            |
            +--> Pruefe predictions[0][1] >= MIN_CONFIDENCE
            |       +--> Falls nein: setVisible(False), return
            |       +--> Falls ja: setVisible(True)
            |
            +--> Fuer jede der 3 Zeilen (i = 0, 1, 2):
                    |
                    +--> name, probability = predictions[i]
                    +--> percent = int(probability * 100)
                    |
                    +--> (DE) display_name = IMAGENET_DE.get(name, name)
                    +--> (EN) display_name = name
                    |
                    +--> _name_labels[i].setText(display_name)
                    +--> _percent_labels[i].setText(f"{percent}%")
                    |
                    +--> bar_width = int(probability * bar_max_width)
                    +--> _bar_widgets[i].setFixedWidth(max(bar_width, 2))
                    |
                    +--> color = _get_bar_color(probability)
                    +--> _bar_widgets[i].setStyleSheet(
                            f"background-color: {color}; border-radius: 2px;"
                         )
```

### Balkenfarbe

`_get_bar_color(probability)` interpoliert linear zwischen zwei RGB-Werten:

- `OUTPUT_RANKING_BAR_DARK` = (0, 150, 180) -- gedaempftes Cyan
- `OUTPUT_RANKING_BAR_BRIGHT` = (0, 240, 255) -- helles Cyan

Formel pro Kanal: `dark + (bright - dark) * probability`

Ergebnis als Hex-String (z.B. `"#00c8e0"`).

### Custom Painting (paintEvent)

Identisch zum InfoPanel:
1. Vertikaler Gradient-Hintergrund (`CYBERPUNK_BG_TOP` / `CYBERPUNK_BG_BOT`)
2. Glow-Border (`CYBERPUNK_CYAN` mit Alpha `OVERLAY_BORDER_ALPHA`)
3. Abgerundetes Rechteck mit `border_radius` 8px

Der Unterschied zum InfoPanel: Kein Alpha auf den Hintergrundfarben (volle Deckkraft).

### Sprachwechsel

`update_language(language)`:
- Setzt `_language` (wird bei naechstem `update_predictions` fuer Klassennamen verwendet)
- Aktualisiert `_title_label` aus `WIDGET_TITLE[language]`

---

## GradCAMWidget

**Datei:** `gradcam_widget.py`
**Basisklasse:** `BaseOverlayWidget`
**Verwendung:** GradCAM-Visualisierung im Visitor Mode (nur fuer bestimmte Layer sichtbar).

### Zweck

Zeigt GradCAM-Heatmaps als kreisfoermig maskiertes Bild mit einem dekorativen Glow-Kreis-Hintergrund. Das Widget ist nur fuer die letzten beiden CNN-Layer (layer3, layer4) sichtbar.

### Konstruktor

| Parameter        | Typ          | Beschreibung                                       |
|------------------|--------------|-----------------------------------------------------|
| `visible_layers` | `list[str]`  | Layer bei denen das Widget sichtbar ist (z.B. `["layer3", "layer4"]`) |
| `parent`         | `QWidget \| None` | Parent-Widget (optional)                       |

### Attribute

| Attribut          | Typ           | Beschreibung                                |
|-------------------|---------------|----------------------------------------------|
| `_visible_layers` | `list[str]`   | Layer bei denen das Widget sichtbar ist      |
| `_display_label`  | `QLabel`      | Label fuer das GradCAM-Bild                  |
| `_bg_pixmap`      | `QPixmap`     | Hintergrundbild (Glow-Kreis aus gradcam.png) |
| `_title_label`    | `QLabel`      | Widget-Titel (aktuell unsichtbar)            |

### Konfiguration im Konstruktor

- Feste Groesse: `GRADCAM_DIMS.width` x `height` (360x360px, quadratisch)
- Initial unsichtbar (`setVisible(False)`)
- Hintergrundbild `gradcam.png` aus `media/img/` geladen
- Padding: `GRADCAM_DIMS.padding` (50px) -- Platz fuer den Glow-Rand um das Bild
- Titel-Label: Aus `WIDGET_TITLE`, initial unsichtbar (`setVisible(False)`)

### Methoden

| Methode                          | Beschreibung                                             |
|----------------------------------|----------------------------------------------------------|
| `set_current_layer(layer_name)`  | Setzt Visibility basierend auf `_visible_layers`         |
| `update_frame(np.ndarray)`       | Empfaengt GradCAM-Frame, maskiert und zeigt an           |
| `update_language(language)`      | Aktualisiert Titel (aktuell nicht sichtbar)              |

### Kreisfoermige Maskierung (update_frame)

```
GradCAM-Frame (np.ndarray)
    |
    +--> numpy_to_qpixmap(frame, label_size)  --> pixmap
    |
    +--> Kreismaskierung:
    |       +--> Neues transparentes QPixmap (gleiche Groesse)
    |       +--> QPainter oeffnen
    |       +--> QPainterPath mit Ellipse erstellen (zentriert)
    |       +--> Ellipse als Clip-Path setzen
    |       +--> Urspruengliches Pixmap zeichnen (nur innerhalb der Ellipse)
    |       +--> QPainter schliessen
    |
    +--> _display_label.setPixmap(masked)
```

Der Durchmesser des Kreises ist `min(pixmap.width(), pixmap.height())`. Die Ellipse wird zentriert auf dem Pixmap positioniert.

### Custom Painting (paintEvent)

Zeichnet das Hintergrundbild (`gradcam.png`) zentriert und skaliert auf die Widget-Groesse. Falls das Bild nicht ladbar war (`_bg_pixmap.isNull()`), wird nichts gezeichnet.

Die Skalierung erfolgt mit `KeepAspectRatio` und `SmoothTransformation`. Das skalierte Bild wird zentriert positioniert.

### Datenfluss

```
CameraThread (nur wenn target_layer in gradcam_layers)
    |
    +--> (alle 0.5s) facade.compute_gradcam(target_layer)
    |       +--> ModelService: Forward + Backward Pass
    |       +--> Heatmap + Kamerabild-Overlay
    |       +--> RGB NumPy Array
    |
    +--> gradcam_ready.emit(overlay)
            |
            +--> GradCAMWidget.update_frame(overlay)
                    +--> Konvertierung + Kreis-Maskierung
                    +--> Anzeige im Label
```

### Visibility-Steuerung

```
VisitorModeWidget._on_layer_selected(layer_name)
    |
    +--> GradCAMWidget.set_current_layer(layer_name)
            |
            +--> should_show = layer_name in _visible_layers
            +--> setVisible(should_show)
```

---

## TitleTextWidget

**Datei:** `title_text_widget.py`
**Basisklasse:** `BaseOverlayWidget`
**Verwendung:** Bilingualer Titel-Text im Visitor Mode.

### Zweck

Zeigt einen kurzen einzeiligen Text oben mittig im Visitor Mode an (z.B. "Wie sieht KI mich?"). Das Widget ist rein dekorativ, immer sichtbar und leitet Mouse-Events durch. Das Styling erfolgt vollstaendig ueber QSS (Selektor: `QLabel#title-text` in `base.qss`).

### Konstruktor

| Parameter | Typ               | Beschreibung                  |
|-----------|--------------------|-------------------------------|
| `parent`  | `QWidget \| None` | Parent-Widget (optional)      |

### Attribute

| Attribut    | Typ      | Beschreibung                          |
|-------------|----------|---------------------------------------|
| `_label`    | `QLabel` | Text-Label mit ObjectName "title-text"|
| `_language` | `str`    | Aktuelle Sprache ("de" oder "en")     |

### Konfiguration im Konstruktor

- `QLabel` mit `AlignCenter`-Ausrichtung
- ObjectName `"title-text"` auf dem QLabel (fuer QSS-Selektor `QLabel#title-text` in `base.qss`)
- `WA_TransparentForMouseEvents` auf `True` gesetzt (dekoratives Widget, Klicks durchlassen)
- Layout: `QVBoxLayout` mit ContentsMargins 0
- Initialer Text aus `TITLE_TEXT["de"]`

### Methoden

| Methode                       | Beschreibung                                            |
|-------------------------------|---------------------------------------------------------|
| `update_language(language)`   | Aktualisiert den angezeigten Text fuer die neue Sprache |

### Datenfluss

```
VisitorModeWidget._on_language_toggled()
    |
    +--> TitleTextWidget.update_language("en")
            |
            +--> _language = "en"
            +--> _update_text()
                    |
                    +--> TITLE_TEXT["en"]  -->  "How AI sees me?"
                    +--> _label.setText(text)
```

### QSS-Styling

Das Styling wird ueber den QSS-Selektor `QLabel#title-text` in `base.qss` gesteuert:

| Eigenschaft   | Wert                                    |
|---------------|-----------------------------------------|
| `color`       | `ARCH_LAYER_MAGENTA` (#ff00aa)          |
| `font-family` | Consolas (via `{font_family}` Platzhalter) |
| `font-size`   | 18px (via `TITLE_TEXT_DIMS.font_size`)  |
| `font-weight` | bold                                    |
| `background`  | transparent                             |

### Positionierung

Die Positionierung erfolgt in `VisitorModeWidget._position_overlays()`:

| Eigenschaft | Berechnung                                |
|-------------|-------------------------------------------|
| Breite      | `self.width() // 2` (halbe Fensterbreite) |
| Hoehe       | 40px (fest)                               |
| X-Position  | `(self.width() - title_width) // 2` (zentriert) |
| Y-Position  | `TITLE_TEXT_DIMS.margin_top` (30px)       |

### Content-Datei

**Datei:** `view/media/content/title_text_content.py`

| Konstante    | Typ              | Inhalt                                                |
|--------------|------------------|-------------------------------------------------------|
| `TITLE_TEXT` | `dict[str, str]` | `{"de": "Wie sieht KI mich?", "en": "How AI sees me?"}` |

---

## GradCAMSubtitleWidget

**Datei:** `gradcam_subtitle_widget.py`
**Basisklasse:** `BaseOverlayWidget`
**Verwendung:** Bilingualer Untertitel-Text unterhalb des GradCAM-Kreises im Visitor Mode.

### Zweck

Funktional identisch zum TitleTextWidget, jedoch nur sichtbar wenn das GradCAMWidget eingeblendet ist (letzte zwei Layer). Zeigt einen erklaerenden Text zum GradCAM-Kreis an.

### Konstruktor

| Parameter        | Typ          | Beschreibung                                       |
|------------------|--------------|-----------------------------------------------------|
| `visible_layers` | `list[str]`  | Layer bei denen das Widget sichtbar ist (wie GradCAMWidget) |
| `parent`         | `QWidget \| None` | Parent-Widget (optional)                       |

### Attribute

| Attribut          | Typ           | Beschreibung                                |
|-------------------|---------------|----------------------------------------------|
| `_label`          | `QLabel`      | Text-Label mit ObjectName "gradcam-subtitle-text" |
| `_language`       | `str`         | Aktuelle Sprache ("de" oder "en")            |
| `_visible_layers` | `list[str]`   | Layer bei denen das Widget sichtbar ist      |

### Konfiguration im Konstruktor

- `QLabel` mit `AlignCenter`-Ausrichtung
- ObjectName `"gradcam-subtitle-text"` auf dem QLabel (fuer QSS-Selektor in `base.qss`)
- `WA_TransparentForMouseEvents` auf `True` gesetzt (dekoratives Widget)
- Initial unsichtbar (`setVisible(False)`)
- Layout: `QVBoxLayout` mit ContentsMargins 0

### Methoden

| Methode                          | Beschreibung                                             |
|----------------------------------|----------------------------------------------------------|
| `set_current_layer(layer_name)`  | Setzt Visibility basierend auf `_visible_layers`         |
| `update_language(language)`      | Aktualisiert den angezeigten Text fuer die neue Sprache  |

### Visibility-Steuerung

Identisch zum GradCAMWidget:

```
VisitorModeWidget._on_layer_selected(layer_name)
    |
    +--> GradCAMSubtitleWidget.set_current_layer(layer_name)
            |
            +--> should_show = layer_name in _visible_layers
            +--> setVisible(should_show)
```

### QSS-Styling

Ueber den QSS-Selektor `QLabel#gradcam-subtitle-text` in `base.qss`:

| Eigenschaft   | Wert                                    |
|---------------|-----------------------------------------|
| `color`       | `ARCH_LAYER_MAGENTA` (#ff00aa)          |
| `font-family` | Consolas (via `{font_family}` Platzhalter) |
| `font-size`   | 20px (via `GRADCAM_SUBTITLE_DIMS.font_size`) |
| `font-weight` | bold                                    |
| `background`  | transparent                             |

### Positionierung

Die Positionierung erfolgt in `VisitorModeWidget._position_overlays()`:

| Eigenschaft | Berechnung                                          |
|-------------|------------------------------------------------------|
| Breite      | `self.width() // 3` (drittel Fensterbreite)          |
| Hoehe       | 40px (fest)                                          |
| X-Position  | `GRADCAM_SUBTITLE_DIMS.margin_left` (30px)           |
| Y-Position  | `GRADCAM_SUBTITLE_DIMS.margin_top` (650px)           |

### Content-Datei

**Datei:** `view/media/content/gradcam_subtitle_content.py`

| Konstante              | Typ              | Inhalt                                                                  |
|------------------------|------------------|-------------------------------------------------------------------------|
| `GRADCAM_SUBTITLE_TEXT`| `dict[str, str]` | `{"de": "Was fokussiert die KI?", "en": "What does the AI focus on?"}` |

---

## Seiteneffekte

### Widgets ohne externe Seiteneffekte

Alle Widgets in diesem Package veraendern keinen globalen Zustand ausserhalb ihrer eigenen UI-Elemente:

| Widget                 | Veraendert nur                                          |
|------------------------|---------------------------------------------------------|
| `CameraDisplayWidget`  | Eigenes QPixmap                                         |
| `InfoPanel`            | Eigenen QTextEdit-Inhalt                                |
| `LayerButton`          | Eigenen checked-Status und Groesse (Pulse)              |
| `ArchLayerButton`      | Eigenes Rendering und Hover-Status                      |
| `LayerButtonBar`       | Eigene Button-States und Pulse-Orchestrierung           |
| `OutputRankingWidget`  | Eigene Labels, Balken-Breiten und Sichtbarkeit          |
| `GradCAMWidget`        | Eigenes Bild und Sichtbarkeit                           |
| `TitleTextWidget`      | Eigenen Label-Text                                      |
| `GradCAMSubtitleWidget`| Eigenen Label-Text und Sichtbarkeit                     |

### Widgets mit Application-Level-Seiteneffekten

| Widget         | Seiteneffekt                                                     |
|----------------|------------------------------------------------------------------|
| `AboutWidget`  | Installiert/entfernt Application-Level `eventFilter` bei Expand/Collapse |

Der EventFilter wird bei `_expand()` auf `QApplication.instance()` installiert und bei `_collapse()` entfernt. Waehrend der EventFilter aktiv ist, werden alle `MouseButtonPress`-Events abgefangen und auf Click-Outside geprueft. Die Events werden nicht konsumiert (Rueckgabe `False`), sodass andere Widgets weiterhin funktionieren. Ausnahme: Swipe-Events auf dem Page-Stack werden konsumiert (Rueckgabe `True`).

### Keine Facade-Zugriffe

Kein Widget in `view/widgets/` hat einen direkten Zugriff auf die `ApplicationFacade`. Daten werden ausschliesslich ueber Signals und Slots zugestellt. Die Modi-Widgets (`VisitorModeWidget`, `AdminModeWidget`) halten die Facade-Referenz und orchestrieren den Datenfluss.
