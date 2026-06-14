# View Layer

Dieses Dokument beschreibt Aufbau, Verantwortlichkeiten und Zusammenspiel der Komponenten im `view/`-Package. Es richtet sich an Entwickler, die den Code warten, erweitern oder reviewen. Fuer das Styling-System existiert eine separate Dokumentation unter `view/styles/styling_guide.md`. Fuer den Admin-Modus existiert eine ausfuehrliche Dokumentation unter `view/admin_mode/admin-mode-doc.md`.

---

## Inhaltsverzeichnis

1. [Einordnung in die Gesamtarchitektur](#einordnung-in-die-gesamtarchitektur)
2. [Package-Struktur](#package-struktur)
3. [Oeffentliche API](#oeffentliche-api)
4. [Hauptkomponenten](#hauptkomponenten)
5. [Widgets](#widgets)
6. [Threading-Modell](#threading-modell)
7. [Datenfluss](#datenfluss)
8. [Overlay-Positionierung](#overlay-positionierung)
9. [Mehrsprachigkeit](#mehrsprachigkeit)
10. [Medien und Content](#medien-und-content)
11. [Utilities](#utilities)
12. [Seiteneffekte](#seiteneffekte)
13. [Erweiterung](#erweiterung)

---

## Einordnung in die Gesamtarchitektur

Die Anwendung folgt einer Drei-Schichten-Architektur:

```
View (PyQt6)  -->  Core (Services + Facade)  -->  Storage (JSON-Config)
```

Der View Layer ist die oberste Schicht. Er stellt die grafische Benutzeroberflaeche bereit und kommuniziert ausschliesslich ueber die `ApplicationFacade` mit der Geschaeftslogik. Direkte Zugriffe auf einzelne Core-Services oder den Storage Layer existieren nicht.

Abhaengigkeitsrichtung: View haengt von Core ab. Der Core kennt den View nicht.

---

## Package-Struktur

```
view/
    __init__.py                     # Public API: MainWindow, CameraThread, VisitorModeWidget, AdminModeWidget
    main_window.py                  # Hauptfenster mit Modus-Verwaltung (QStackedWidget)
    visitor_mode.py                 # Besuchermodus (Fullscreen, Touch-optimiert)
    camera_thread.py                # QThread fuer asynchrone Frame-Verarbeitung
    admin_mode/                     # Admin-Modus (Preset-Editor) – siehe admin-mode-doc.md
        __init__.py                 # Re-Export: AdminModeWidget
        admin_mode_widget.py        # Haupt-Widget mit Editor + Live-Vorschau
        channel_manager.py          # Channel-Verwaltung + ChannelSpinBox
        preset_builder.py           # PresetConfig-Erstellung aus UI-State
    widgets/                        # Wiederverwendbare UI-Komponenten – siehe legacy-widgets-doc.md
        __init__.py                 # Re-Export aller Widgets
        base_overlay.py             # Basisklasse fuer transparente Overlays
        camera_display.py           # Kamera-Display (Visitor + Admin)
        layer_button.py             # Einzelner Layer-Button (checkable, Pulse-Animation)
        layer_button_bar.py         # Horizontale Button-Leiste fuer Layer-Auswahl
        info_panel.py               # Info-Panel fuer Layer-Beschreibungen
        about_widget.py             # About-Slideshow (3-Seiten, Swipe)
        output_ranking_widget.py    # Top-3-Predictions als Balkendiagramm
        gradcam_widget.py           # GradCAM-Visualisierung mit Kreis-Maskierung
        title_text_widget.py        # Bilingualer Titel-Text (Visitor Mode)
        gradcam_subtitle_widget.py  # Bilingualer GradCAM-Untertitel (Visitor Mode)
        helpers/                    # Spezialisierte Widget-Varianten
            __init__.py             # Re-Export: ArchLayerButton
            arch_layer_button.py    # LayerButton mit QPainter-Architektur-Visualisierung
    media/                          # Statische Medien und Inhalte
        content/                    # Bilinguale Texte (DE/EN) als Python-Dicts
            main_window_content.py
            layer_button_bar_content.py
            info_panel_content.py
            about_widget_content.py
            output_ranking_content.py
            gradcam_widget_content.py
            title_text_content.py
            gradcam_subtitle_content.py
            imagenet_translations.py    # 1000 EN->DE Mappings fuer ImageNet-Klassen
        icon/                       # Icons (info_icon.png, lang_flag.png, cursor.png, cursor_clicked.png)
        img/                        # Bilder (Logos, Hintergruende, GradCAM-Glow)
    styles/                         # Zentrales Styling – siehe styling_guide.md
        __init__.py                 # Re-Export: StyleManager + alle Farben/Dimensionen
        colors.py                   # Farbdefinitionen (Hex-Strings, RGB-Tupel, RGBA-Helpers)
        dimensions.py               # Dimensionen als frozen Dataclasses
        base.qss                    # QSS-Template mit Platzhaltern
        style_manager.py            # Platzhalter-Ersetzung und Caching
    utils/                          # Hilfsfunktionen
        __init__.py                 # Re-Export: numpy_to_qpixmap
        frame_converter.py          # NumPy-Array zu QPixmap Konvertierung
```

---

## Oeffentliche API

Das `view/__init__.py` exportiert vier Klassen:

| Klasse              | Modul              | Beschreibung                          |
|---------------------|--------------------|---------------------------------------|
| `MainWindow`        | `main_window.py`   | Hauptfenster mit Modus-Verwaltung     |
| `CameraThread`      | `camera_thread.py` | QThread fuer Frame-Verarbeitung       |
| `VisitorModeWidget` | `visitor_mode.py`  | Fullscreen-UI fuer Museumsbesucher    |
| `AdminModeWidget`   | `admin_mode/`      | Preset-Editor mit Live-Vorschau       |

Der View Layer wird in `main.py` instanziiert. Dort werden auch die `ApplicationFacade` per Dependency Injection erzeugt und das globale Stylesheet geladen.

---

## Hauptkomponenten

### MainWindow

**Datei:** `main_window.py`

Das `MainWindow` ist eine `QMainWindow`-Subklasse und der zentrale Container der Anwendung. Es verwaltet den Wechsel zwischen Visitor Mode und Admin Mode ueber ein `QStackedWidget`.

**Konstruktor-Parameter:**

| Parameter | Typ                 | Beschreibung                 |
|-----------|---------------------|------------------------------|
| `facade`  | `ApplicationFacade` | Zugriff auf Geschaeftslogik  |

**Modus-Verwaltung:**

Das `QStackedWidget` enthaelt zwei Widgets:
- Index 0: `VisitorModeWidget` (Standard beim Start)
- Index 1: `AdminModeWidget`

Der Wechsel erfolgt ueber `switch_to_visitor_mode()` und `switch_to_admin_mode()`. Beide Methoden stoppen den jeweils inaktiven Modus (`stop()`) und starten den aktiven (`start()`). Dadurch laeuft immer nur ein `CameraThread` gleichzeitig.

**Tastaturkuerzel:**

| Kuerzel  | Aktion                         |
|----------|--------------------------------|
| `F11`    | Vollbild/Fenster umschalten    |
| `Ctrl+A` | Admin Mode oeffnen             |
| `Ctrl+V` | Visitor Mode oeffnen           |
| `ESC`    | Zurueck zu Visitor Mode        |

**Sprachwechsel:**

Das `VisitorModeWidget` emittiert das Signal `language_changed(str)`. Das `MainWindow` verbindet sich darauf und aktualisiert den Fenstertitel aus `APP_TITLE[language]`.

**Lifecycle:**

Im `closeEvent()` werden beide Modi gestoppt. Die Reihenfolge ist Visitor zuerst, dann Admin.

---

### VisitorModeWidget

**Datei:** `visitor_mode.py`

Das `VisitorModeWidget` ist die primaere Ansicht fuer Museumsbesucher. Es zeigt eine Fullscreen-Visualisierung der CNN-Layer-Aktivierungen mit ueberlagerten Overlay-Widgets.

**Konstruktor-Parameter:**

| Parameter | Typ                 | Beschreibung                 |
|-----------|---------------------|------------------------------|
| `facade`  | `ApplicationFacade` | Zugriff auf Geschaeftslogik  |

**Enthaltene Widgets (alle als Overlays positioniert):**

| Widget                 | Position              | Beschreibung                              |
|------------------------|-----------------------|-------------------------------------------|
| `CameraDisplayWidget`  | Vollflaeche           | Kamera-Feed / Visualisierung              |
| `LayerButtonBar`       | Unten zentriert       | Layer-Auswahl-Buttons                     |
| `InfoPanel`            | Rechts oben           | Layer-Beschreibungstext (HTML)             |
| `AboutWidget`          | Rechts oben (Icon-Bar)| Info-Slideshow (3 Seiten, aufklappbar)     |
| `OutputRankingWidget`  | Rechts neben Buttons  | Top-3-Predictions als Balkendiagramm       |
| `GradCAMWidget`        | Links, vertikal zentriert | GradCAM-Overlay (nur bei layer3/layer4) |
| `GradCAMSubtitleWidget`| Links unten           | GradCAM-Untertitel (nur bei layer3/layer4) |
| `TitleTextWidget`      | Oben mittig           | Bilingualer Titel-Text (immer sichtbar)    |
| Language-Toggle        | Rechts oben (Icon-Bar)| Sprachwechsel DE/EN                        |
| Frame-Overlay          | Vollflaeche           | Dekorativer HUD-Rahmen (PNG)              |
| Icon-Bar-Hintergrund   | Rechts oben           | Dekorativer Hintergrund hinter About/Language |

**Zustand:**

| Attribut          | Typ    | Beschreibung                                |
|-------------------|--------|---------------------------------------------|
| `_current_layer`  | `str`  | Aktuell angezeigter Layer (initial: erster verfuegbarer) |
| `_language`       | `str`  | Aktuelle Sprache ("de" oder "en")           |
| `_cursor_visible` | `bool` | Custom-Cursor sichtbar oder versteckt       |

**Custom-Cursor:**

Im Visitor Mode wird ein PNG-basierter Custom-Cursor verwendet. Der Cursor ist initial unsichtbar (BlankCursor) und wird erst bei Mausbewegung eingeblendet. Bei Mausklick wechselt das Cursor-Bild auf eine "geklickt"-Variante. Nach Loslassen verschwindet der Cursor wieder. Das Verhalten wird ueber einen Application-Level `eventFilter` gesteuert, der in `start()` installiert und in `stop()` entfernt wird.

**Signals:**

| Signal                  | Parameter | Beschreibung                            |
|-------------------------|-----------|-----------------------------------------|
| `language_changed(str)` | `str`     | Emittiert bei Sprachwechsel ("de"/"en") |

---

## Widgets

Alle wiederverwendbaren Widgets liegen im Package `view/widgets/`. Sie sind ueber `view/widgets/__init__.py` importierbar. Dieser Abschnitt gibt eine Kurzuebersicht. Die vollstaendige technische Referenz (Attribute, Signals, Datenfluesse, Rendering-Details, Seiteneffekte) findet sich in `view/widgets/legacy-widgets-doc.md`.

### BaseOverlayWidget

**Datei:** `widgets/base_overlay.py`

Basisklasse fuer transparente Overlay-Widgets. Setzt `WA_TranslucentBackground` und stellt Fade-In/Fade-Out-Animationen ueber `QGraphicsOpacityEffect` bereit. Definiert die Methode `update_language(language)`, die Subklassen ueberschreiben um sprachspezifische Inhalte zu aktualisieren.

Wird verwendet von: `LayerButtonBar`, `InfoPanel`, `AboutWidget`, `OutputRankingWidget`, `GradCAMWidget`, `TitleTextWidget`, `GradCAMSubtitleWidget`.

### CameraDisplayWidget

**Datei:** `widgets/camera_display.py`

Ein `QLabel`, das als Kamera-Display dient. Wird von beiden Modi verwendet (Visitor und Admin). Der Slot `update_frame(np.ndarray)` konvertiert eingehende RGB-NumPy-Arrays via `numpy_to_qpixmap()` in ein `QPixmap` und zeigt es an. Die Skalierung erfolgt auf die aktuelle Widget-Groesse mit Beibehaltung des Seitenverhaeltnisses.

Das Styling erfolgt ueber den `objectName` "camera-display" und den zugehoerigen QSS-Selektor in `base.qss`.

### LayerButton

**Datei:** `widgets/layer_button.py`

Ein `QPushButton` mit `checkable`-Eigenschaft fuer die Layer-Navigation. Emittiert bei Klick das Signal `layer_selected(str)` mit dem internen Layer-Namen.

Besondere Merkmale:
- Mindestgroesse aus `BUTTON_DIMS` (150x80 px)
- Font und Groesse aus `FONT_SIZES`
- Pulse-Animation: Periodisches Wachsen/Schrumpfen (10%, 2s Zyklus) ueber `QPropertyAnimation` auf eine Custom `pulse_scale`-Property. Die Basisgroesse wird nach Layout-Finalisierung via `capture_base_size()` erfasst.

### ArchLayerButton

**Datei:** `widgets/helpers/arch_layer_button.py`

Subklasse von `LayerButton`, die das QSS-basierte Rendering durch Custom `QPainter`-Zeichnung ersetzt. Zeichnet eine CNN-Architektur-Visualisierung mit Knoten (vertikale Spalte am linken Rand), Verbindungslinien zum rechten Rand, Glow-Effekten und einem Label. Das Rendering ist zustandsabhaengig (default/hover/checked) mit unterschiedlichen Farben aus `view.styles.colors`.

Zeichen-Parameter (Knotenradius, Abstande, Schriftgroesse) stammen aus `ARCH_LAYER_BTN_DIMS` in `dimensions.py`.

### LayerButtonBar

**Datei:** `widgets/layer_button_bar.py`

Eine horizontale Leiste aus `ArchLayerButton`-Instanzen. Verwaltet den aktiven Button (Radio-Button-Verhalten: nur ein Button gleichzeitig `checked`). Emittiert `layer_selected(str)` bei Klick.

Jeder Button ist in einen Fixed-Size `QWidget`-Container eingebettet. Die Container-Groesse wird nach Layout-Finalisierung per `QTimer.singleShot(0, ...)` auf die maximale Pulse-Groesse (110% + 6px Puffer) gesetzt. Nach dem Container-Resize emittiert die Bar das Signal `layout_ready`, damit der Parent die Overlay-Positionierung aktualisiert.

Die Knoten-Anzahl pro Layer ist in `DEFAULT_NODE_COUNTS` hinterlegt und entspricht der ResNet18-Architektur (conv1: 12, layer1: 8, layer2: 6, layer3: 4, layer4: 1).

### InfoPanel

**Datei:** `widgets/info_panel.py`

Ein Overlay-Widget mit semi-transparentem Cyberpunk-Hintergrund (Gradient + Glow-Border via `paintEvent`). Enthaelt ein read-only `QTextEdit` fuer HTML-formatierten Text. Wird im Visitor Mode fuer Layer-Beschreibungen verwendet.

Der Hintergrund wird manuell in `paintEvent()` gezeichnet mit Gradient-Farben aus `CYBERPUNK_BG_TOP/BOT` und Alpha-Wert aus `INFO_PANEL_BG_OPACITY`.

### AboutWidget

**Datei:** `widgets/about_widget.py`

Ein aufklappbares Info-Widget. Zeigt ein Info-Icon, das auf Klick einen Content-Bereich mit 3-Seiten-Slideshow oeffnet. Navigation ueber Pfeil-Buttons oder horizontale Swipe-Geste. Seitenindikator zeigt aktuelle Position (z.B. "2/3").

Die Inhalte stammen aus `about_widget_content.py` und sind bilingual (DE/EN). Logo-Bilder werden als QTextDocument-Ressourcen registriert und im HTML ueber Dateinamen referenziert.

Schliessen: Klick ausserhalb des Widgets (Application-Level `eventFilter`) oder erneuter Klick auf das Icon.

Signal `expanded_changed(bool)` wird emittiert wenn sich der Expand-Status aendert. Der Visitor Mode verbindet sich darauf und blendet das InfoPanel aus, solange das AboutWidget geoeffnet ist.

### OutputRankingWidget

**Datei:** `widgets/output_ranking_widget.py`

Zeigt die Top-3-Klassifikationsergebnisse des CNN als Balkendiagramm. Jede Zeile besteht aus Klassenname, proportionalem Balken und Prozentzahl. Die Balkenfarbe interpoliert linear zwischen gedaempftem und hellem Cyan basierend auf der Wahrscheinlichkeit.

Das Widget startet unsichtbar und wird erst eingeblendet, wenn die Top-1-Prediction ueber `MIN_CONFIDENCE` (10%) liegt. Im deutschen Modus werden Klassennamen ueber `IMAGENET_DE` uebersetzt.

Cyberpunk-Hintergrund mit Gradient und Glow-Border via `paintEvent()`.

### GradCAMWidget

**Datei:** `widgets/gradcam_widget.py`

Zeigt GradCAM-Heatmaps. Das Widget ist nur fuer die letzten beiden CNN-Layer sichtbar (konfigurierbar ueber `visible_layers` im Konstruktor). `set_current_layer()` steuert die Sichtbarkeit.

Das GradCAM-Bild wird kreisfoermig maskiert dargestellt. In `update_frame()` wird ein `QPainterPath` mit Ellipse als Clip-Path verwendet. Der Hintergrund ist ein PNG-basierter Glow-Kreis (`gradcam.png`), der in `paintEvent()` zentriert skaliert gezeichnet wird.

### TitleTextWidget

**Datei:** `widgets/title_text_widget.py`

Ein Overlay-Widget, das einen kurzen bilingualen Titel-Text anzeigt (z.B. "Wie sieht KI mich?"). Das Widget erbt von `BaseOverlayWidget` und enthaelt ein `QLabel` mit ObjectName `"title-text"` fuer QSS-Styling. Der Text wird in Magenta-Farbe (`ARCH_LAYER_MAGENTA`) dargestellt, bold, 18px, Consolas.

Das Widget ist rein dekorativ und immer sichtbar im Visitor Mode. Mouse-Events werden durchgelassen (`WA_TransparentForMouseEvents`). Die bilingualen Texte stammen aus `title_text_content.py` und werden ueber `update_language()` bei Sprachwechsel aktualisiert.

Positionierung: Oben mittig, halbe Fensterbreite, `TITLE_TEXT_DIMS.margin_top` (30px) vom oberen Rand.

### GradCAMSubtitleWidget

**Datei:** `widgets/gradcam_subtitle_widget.py`

Ein Overlay-Widget, das einen bilingualen Untertitel-Text unterhalb des GradCAM-Kreises anzeigt (z.B. "Was fokussiert die KI?"). Funktional identisch zum TitleTextWidget, jedoch nur sichtbar wenn das GradCAMWidget eingeblendet ist (letzte zwei Layer). Die Visibility wird ueber `set_current_layer()` gesteuert (gleiche `visible_layers` wie GradCAMWidget).

Das Widget ist rein dekorativ, Mouse-Events werden durchgelassen. Styling ueber QSS-Selektor `QLabel#gradcam-subtitle-text` in `base.qss` (Magenta, bold, 20px). Bilingualer Text aus `gradcam_subtitle_content.py`.

Positionierung: Links, absolute Koordinaten ueber `GRADCAM_SUBTITLE_DIMS` (margin_left, margin_top).

---

## Threading-Modell

### CameraThread

**Datei:** `camera_thread.py`

Die gesamte Frame-Verarbeitung laeuft in einem `QThread` ab, um den GUI-Thread nicht zu blockieren. Jeder Modus (Visitor und Admin) erstellt seine eigene `CameraThread`-Instanz.

**Konstruktor-Parameter:**

| Parameter      | Typ                 | Beschreibung                      |
|----------------|---------------------|-----------------------------------|
| `facade`       | `ApplicationFacade` | Zugriff auf Geschaeftslogik       |
| `target_layer` | `str`               | Initialer Layer fuer Visualisierung |

**Signals:**

| Signal                       | Parameter      | Beschreibung                          |
|------------------------------|----------------|---------------------------------------|
| `frame_ready(np.ndarray)`    | `np.ndarray`   | Neuer Visualisierungs-Frame verfuegbar |
| `predictions_ready(list)`    | `list`         | Top-K Predictions verfuegbar          |
| `gradcam_ready(np.ndarray)`  | `np.ndarray`   | GradCAM-Overlay verfuegbar            |
| `error_occurred(str)`        | `str`          | Fehlermeldung                         |

**Hauptschleife (`run()`):**

Die Schleife laeuft mit ca. 30 FPS (`time.sleep(1/30)`). Pro Iteration:

1. Frame mit Visualisierung holen (entweder via `get_visualization_for_layer` oder `get_visualization_with_preset` wenn ein temporaeres Preset gesetzt ist)
2. `frame_ready` Signal emittieren
3. Falls Predictions-Intervall (1.0s) abgelaufen: Predictions holen und `predictions_ready` emittieren
4. Falls GradCAM-Intervall (0.5s) abgelaufen und aktueller Layer in `_gradcam_layers`: GradCAM berechnen und `gradcam_ready` emittieren

**Fehlerbehandlung:**

Bei `CameraError` wird ein Fehlerzaehler inkrementiert. Nach 5 aufeinanderfolgenden Fehlern stoppt sich der Thread selbst und emittiert `error_occurred`. Bei anderen Exceptions wird sofort `error_occurred` emittiert.

**Temporaeres Preset (Admin Mode):**

`set_temp_preset(preset)` setzt ein temporaeres `PresetConfig`, das anstelle des persistierten aktiven Presets fuer die Visualisierung verwendet wird. `clear_temp_preset()` entfernt es. Dieses Muster ermoeglicht die Live-Vorschau im Admin-Modus, ohne die gespeicherte Konfiguration zu veraendern.

**Throttling-Intervalle:**

| Signal         | Intervall | Begruendung                               |
|----------------|-----------|--------------------------------------------|
| `frame_ready`  | ~33ms     | 30 FPS Zielrate                            |
| `predictions`  | 1.0s      | Predictions aendern sich langsam           |
| `gradcam`      | 0.5s      | Rechenintensiv (Forward + Backward Pass)   |

---

## Datenfluss

### Visitor Mode: Startup

```
main.py
    |
    +--> ApplicationFacade erstellen (DI)
    +--> facade.initialize()  (Modell laden, Kamera starten)
    +--> QApplication erstellen
    +--> StyleManager.get_stylesheet()  -->  app.setStyleSheet()
    +--> MainWindow(facade)
    |       |
    |       +--> VisitorModeWidget(facade)
    |       |       +--> Widgets erstellen (CameraDisplay, ButtonBar, InfoPanel, ...)
    |       |       +--> _position_overlays()
    |       |
    |       +--> AdminModeWidget(facade)
    |               +--> Editor-Panel + Preview-Panel erstellen
    |               +--> ChannelManager erstellen
    |               +--> Initiales Preset laden
    |
    +--> window.switch_to_visitor_mode()
    |       |
    |       +--> VisitorModeWidget.start()
    |               +--> CameraThread erstellen
    |               +--> Signals verbinden (frame_ready, predictions_ready, gradcam_ready)
    |               +--> CameraThread.start()
    |               +--> Custom-Cursor aktivieren (BlankCursor + EventFilter)
    |
    +--> window.showFullScreen()
    +--> app.exec()  (Event Loop)
```

### Visitor Mode: Frame-Zyklus

```
CameraThread.run()
    |
    +--> facade.get_visualization_for_layer("layer2")
    |       |
    |       +--> CameraService.get_frame()             --> RGB NumPy (H, W, 3)
    |       +--> ModelService.extract_layer_activations --> Tensor (C, H, W)
    |       +--> PresetService.get_active_preset        --> PresetConfig
    |       +--> VisualizationService.visualize          --> RGB NumPy (600, 800, 3)
    |
    +--> frame_ready.emit(frame)
    |       |
    |       +--> CameraDisplayWidget.update_frame(frame)
    |               +--> numpy_to_qpixmap(frame, label_size)
    |               +--> self.setPixmap(pixmap)
    |
    +--> (alle 1.0s) facade.get_top_predictions()
    |       +--> predictions_ready.emit(predictions)
    |               +--> OutputRankingWidget.update_predictions(predictions)
    |
    +--> (alle 0.5s, nur layer3/layer4) facade.compute_gradcam()
            +--> gradcam_ready.emit(overlay)
                    +--> GradCAMWidget.update_frame(overlay)
                            +--> Kreisfoermige Maskierung via QPainterPath
```

### Visitor Mode: Layer-Wechsel

```
User klickt Layer-Button
    |
    +--> ArchLayerButton.clicked
    |       |
    |       +--> LayerButtonBar._on_button_clicked(layer_name)
    |               +--> set_active_layer(layer_name)  (Radio-Button, Pulse)
    |               +--> layer_selected.emit(layer_name)
    |
    +--> VisitorModeWidget._on_layer_selected(layer_name)
            |
            +--> _current_layer = layer_name
            +--> _update_layer_info(layer_name)
            |       +--> LAYER_DESCRIPTIONS[language][layer_name]
            |       +--> InfoPanel.set_content(html)
            |
            +--> GradCAMWidget.set_current_layer(layer_name)
            |       +--> setVisible(layer_name in visible_layers)
            |
            +--> GradCAMSubtitleWidget.set_current_layer(layer_name)
            |       +--> setVisible(layer_name in visible_layers)
            |
            +--> CameraThread.change_layer(layer_name)
                    +--> _target_layer = layer_name
                    +--> (naechster Loop-Durchlauf verwendet neuen Layer)
```

### Visitor Mode: Sprachwechsel

```
User klickt Language-Toggle
    |
    +--> VisitorModeWidget._on_language_toggled()
            |
            +--> _language = "en" (bzw. "de")
            |
            +--> LayerButtonBar.update_language("en")
            |       +--> Button-Texte aus BUTTON_LABELS["en"] setzen
            |
            +--> AboutWidget.update_language("en")
            |       +--> Seiteninhalte aus PAGE_CONTENTS["en"] laden
            |
            +--> OutputRankingWidget.update_language("en")
            |       +--> Titel aus WIDGET_TITLE["en"]
            |       +--> _language = "en"  (fuer Klassennamen bei naechstem update)
            |
            +--> GradCAMWidget.update_language("en")
            |       +--> Titel aus WIDGET_TITLE["en"]
            |
            +--> TitleTextWidget.update_language("en")
            |       +--> Text aus TITLE_TEXT["en"]
            |
            +--> GradCAMSubtitleWidget.update_language("en")
            |       +--> Text aus GRADCAM_SUBTITLE_TEXT["en"]
            |
            +--> _update_layer_info(current_layer)
            |       +--> LAYER_DESCRIPTIONS["en"][layer_name]
            |       +--> InfoPanel.set_content(html)
            |
            +--> language_changed.emit("en")
                    |
                    +--> MainWindow._on_language_changed("en")
                            +--> setWindowTitle(APP_TITLE["en"])
```

### Modus-Wechsel: Visitor zu Admin

```
User drueckt Ctrl+A
    |
    +--> MainWindow.switch_to_admin_mode()
            |
            +--> VisitorModeWidget.stop()
            |       +--> Custom-Cursor entfernen
            |       +--> CameraThread.stop()  +  thread.wait()
            |       +--> CameraDisplayWidget.clear()
            |
            +--> QStackedWidget.setCurrentIndex(1)
            |
            +--> AdminModeWidget.start()
                    +--> Preset-Selector auf aktives Preset synchronisieren
                    +--> CameraThread erstellen + starten
                    +--> _on_param_changed()  (initiale Live-Vorschau)
```

### Modus-Wechsel: Admin zu Visitor

```
User drueckt ESC oder Ctrl+V
    |
    +--> MainWindow.switch_to_visitor_mode()
            |
            +--> AdminModeWidget.stop()
            |       +--> CameraThread.stop()  +  thread.wait()
            |       +--> Preview-Display.clear()
            |
            +--> QStackedWidget.setCurrentIndex(0)
            |
            +--> VisitorModeWidget.start()
                    +--> CameraThread erstellen + starten
                    +--> Custom-Cursor aktivieren
```

### Anwendungs-Shutdown

```
User schliesst Fenster
    |
    +--> MainWindow.closeEvent()
    |       +--> VisitorModeWidget.stop()
    |       +--> AdminModeWidget.stop()
    |       +--> event.accept()
    |
    +--> app.exec() kehrt zurueck
    |
    +--> facade.shutdown()
            +--> CameraService.stop()  (Kamera-Hardware freigeben)
```

---

## Overlay-Positionierung

Alle Widgets im Visitor Mode ausser dem `CameraDisplayWidget` sind Overlays. Sie schweben ueber dem Kamera-Feed und werden nicht ueber das Standard-Layout-System positioniert, sondern manuell in `_position_overlays()`.

Diese Methode wird bei jedem `resizeEvent` aufgerufen (z.B. beim Wechsel zwischen Fenster- und Vollbildmodus).

**Positionierungsschema:**

```
+-----------------------------------------------------+
|  [Icon-Bar-BG]  [Language] [About]                   |
|              [TitleText]               [InfoPanel]   |
|                                                       |
|              [GradCAM]                                |
|                                                       |
|                                                       |
|          [-------LayerButtonBar-------] [Ranking]     |
+-----------------------------------------------------+
```

| Widget            | Positionierung                                     |
|-------------------|----------------------------------------------------|
| Frame-Overlay     | 0,0 bis volle Fenstergroesse (unterhalb aller Overlays) |
| LayerButtonBar    | Unten zentriert, `OVERLAY_DIMS.button_bar_margin` vom unteren Rand |
| InfoPanel         | Rechts oben, Abstaende aus `INFO_PANEL_DIMS`       |
| Icon-Bar-BG       | Rechts oben, Abstaende aus `ICON_BAR_DIMS`         |
| AboutWidget       | Rechts in der Icon-Bar (Icon via AlignRight)        |
| Language-Toggle   | Links in der Icon-Bar                               |
| OutputRanking     | Rechts neben der ButtonBar, vertikal zentriert      |
| TitleTextWidget   | Oben mittig, halbe Fensterbreite, `TITLE_TEXT_DIMS.margin_top` |
| GradCAMWidget     | Links, vertikal zentriert, `GRADCAM_DIMS.margin_left` |
| GradCAMSubtitleWidget | Links, `GRADCAM_SUBTITLE_DIMS.margin_left/margin_top` |

Die Z-Reihenfolge wird durch die Aufrufreihenfolge von `raise_()` bestimmt. Das Frame-Overlay wird zuerst geraised, alle interaktiven Widgets danach.

---

## Mehrsprachigkeit

### Architektur

Alle sichtbaren Texte im Visitor Mode sind bilingual (Deutsch/Englisch). Der Admin Mode ist einsprachig (Deutsch).

**Sprach-State:** Der aktuelle Sprach-Code (`"de"` oder `"en"`) wird im `VisitorModeWidget._language` gehalten. Standard ist `"de"`.

**Content-Dateien:** Unter `view/media/content/` liegen Python-Module mit `dict`-Konstanten. Zwei Muster:

1. Einfacher Text:
```python
WIDGET_TITLE: dict[str, str] = {
    "de": "Modellvorhersagen",
    "en": "Model Predictions",
}
```

2. Verschachtelt (Layer-abhaengig):
```python
LAYER_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "de": {"conv1": "<h2>...</h2>", ...},
    "en": {"conv1": "<h2>...</h2>", ...},
}
```

**Zugriffsmuster:** `KONSTANTE[language]` oder `KONSTANTE[language][key]`.

### Sprachwechsel-Ablauf

1. User klickt Language-Toggle
2. `VisitorModeWidget._on_language_toggled()` toggelt `_language`
3. Alle Overlay-Widgets mit `update_language()`-Methode werden aktualisiert
4. Das InfoPanel wird ueber `_update_layer_info()` (via `set_content`) aktualisiert
5. Das Signal `language_changed` wird emittiert (MainWindow aktualisiert Fenstertitel)

### ImageNet-Klassennamen

Die 1000 ImageNet-Klassennamen liegen auf Englisch im Modell. In `imagenet_translations.py` ist ein Dictionary `IMAGENET_DE` mit Deutsch-Uebersetzungen hinterlegt. Das `OutputRankingWidget` verwendet `IMAGENET_DE.get(name, name)` mit Fallback auf den englischen Namen.

---

## Medien und Content

### Content-Dateien (`media/content/`)

| Datei                          | Konstante             | Typ                                   | Verwendung                  |
|--------------------------------|-----------------------|---------------------------------------|-----------------------------|
| `main_window_content.py`       | `APP_TITLE`           | `dict[str, str]`                      | Fenstertitel                |
| `layer_button_bar_content.py`  | `BUTTON_LABELS`       | `dict[str, dict[str, str]]`           | Button-Beschriftungen       |
| `info_panel_content.py`        | `LAYER_DESCRIPTIONS`  | `dict[str, dict[str, str]]`           | Layer-Beschreibungstexte    |
| `about_widget_content.py`      | `PAGE_CONTENTS`       | `dict[str, list[str]]`                | About-Seiten (HTML)         |
| `output_ranking_content.py`    | `WIDGET_TITLE`        | `dict[str, str]`                      | Widget-Titel                |
| `gradcam_widget_content.py`    | `WIDGET_TITLE`        | `dict[str, str]`                      | Widget-Titel                |
| `title_text_content.py`        | `TITLE_TEXT`          | `dict[str, str]`                      | Titel-Text                  |
| `gradcam_subtitle_content.py`  | `GRADCAM_SUBTITLE_TEXT` | `dict[str, str]`                    | GradCAM-Untertitel          |
| `imagenet_translations.py`     | `IMAGENET_DE`         | `dict[str, str]`                      | EN->DE Klassennamen-Mapping |

### Statische Medien

| Verzeichnis     | Inhalt                                                |
|-----------------|-------------------------------------------------------|
| `media/icon/`   | `info_icon.png`, `lang_flag.png`, `cursor.png`, `cursor_clicked.png` |
| `media/img/`    | `bg0.png` (Frame-Overlay), `hbox_info_lang.png` (Icon-Bar-BG), `gradcam.png` (Glow-Kreis), Logo-Bilder |

Alle Pfade werden relativ zum jeweiligen Modul via `Path(__file__).parent` aufgeloest.

---

## Utilities

### frame_converter

**Datei:** `utils/frame_converter.py`

Einzelne Funktion `numpy_to_qpixmap()`, die ein RGB-NumPy-Array (H, W, 3, uint8) in ein `QPixmap` konvertiert. Optionale Parameter:

- `target_size: QSize` -- Skalierung auf Zielgroesse
- `keep_aspect_ratio: bool` -- Seitenverhaeltnis beibehalten (Standard: True)

Bei `keep_aspect_ratio=True` wird `KeepAspectRatioByExpanding` verwendet. Das resultierende Pixmap kann groesser als die Zielgroesse sein und wird per zentriertem Cropping auf die exakte Groesse zugeschnitten.

Die Konvertierung laeuft ueber `QImage(frame.data, ...)` mit Format `Format_RGB888`. Das setzt voraus, dass das NumPy-Array im Speicher zusammenhaengend (contiguous) ist.

---

## Seiteneffekte

### Widget-Lifecycle

| Methode                            | Widget              | Art des Seiteneffekts                                 |
|------------------------------------|---------------------|-------------------------------------------------------|
| `start()`                          | VisitorModeWidget   | Erstellt CameraThread, installiert EventFilter, setzt Override-Cursor |
| `stop()`                           | VisitorModeWidget   | Stoppt CameraThread, entfernt EventFilter, entfernt Override-Cursor |
| `start()`                          | AdminModeWidget     | Erstellt CameraThread, setzt temporaeres Preset        |
| `stop()`                           | AdminModeWidget     | Stoppt CameraThread                                    |
| `switch_to_visitor_mode()`         | MainWindow          | Ruft stop()/start() auf beiden Widgets auf              |
| `switch_to_admin_mode()`           | MainWindow          | Ruft stop()/start() auf beiden Widgets auf              |
| `closeEvent()`                     | MainWindow          | Stoppt beide Widgets                                    |

### CameraThread

| Methode               | Art des Seiteneffekts                                         |
|-----------------------|---------------------------------------------------------------|
| `run()`               | Endlosschleife mit Facade-Aufrufen (Kamera, Modell, Visualisierung) |
| `stop()`              | Setzt `_running = False`, wartet auf Thread-Ende (`wait()`)   |
| `change_layer()`      | Aendert `_target_layer` (naechster Loop-Durchlauf nutzt neuen Layer) |
| `set_temp_preset()`   | Aendert `_temp_preset` (naechster Loop-Durchlauf nutzt neues Preset) |

### Signal-Verbindungen im Visitor Mode

Beim `start()` des Visitor Mode werden folgende Verbindungen hergestellt:

```
CameraThread.frame_ready       --> CameraDisplayWidget.update_frame
CameraThread.predictions_ready --> OutputRankingWidget.update_predictions
CameraThread.gradcam_ready     --> GradCAMWidget.update_frame
CameraThread.error_occurred    --> VisitorModeWidget._on_error_occurred
```

Beim `stop()` wird der CameraThread gestoppt und auf `None` gesetzt. Die Verbindungen werden dadurch implizit aufgeloest.

### Seiteneffektfreie Widgets

Folgende Widgets veraendern keinen globalen Zustand:

- `CameraDisplayWidget.update_frame()` -- setzt nur das eigene Pixmap
- `InfoPanel.set_content()` -- setzt nur den eigenen Text
- `LayerButtonBar.set_active_layer()` -- aendert nur eigenen Button-State
- Alle `update_language()`-Methoden -- aendern nur eigene Texte
- `GradCAMWidget.set_current_layer()` -- aendert nur eigene Visibility
- `GradCAMSubtitleWidget.set_current_layer()` -- aendert nur eigene Visibility
- `TitleTextWidget.update_language()` -- aendert nur eigenen Label-Text

---

## Erweiterung

### Neues Widget hinzufuegen

Eine ausfuehrliche technische Referenz aller bestehenden Widgets (Attribute, Signals, Datenfluesse, Rendering-Details) findet sich in `view/widgets/legacy-widgets-doc.md`. Eine Anleitung zum Erstellen neuer Widgets findet sich in `view/widgets/widgets-dev-guide.md`.

### Neuen Modus hinzufuegen

1. Mode-Widget in `view/` erstellen (z.B. `view/my_mode.py`)
2. Konstruktor nimmt `ApplicationFacade` entgegen
3. `start()` und `stop()` Methoden implementieren (Lifecycle analog Visitor/Admin)
4. In `MainWindow._init_ui()`: Widget erstellen und zum `QStackedWidget` hinzufuegen
5. Wechsel-Methode in `MainWindow` ergaenzen (analog `switch_to_admin_mode()`)
6. Tastaturkuerzel in `_init_shortcuts()` registrieren
7. In `__init__.py` exportieren

### Neues Overlay im Visitor Mode hinzufuegen

1. Widget-Klasse erstellen (von `BaseOverlayWidget` ableiten fuer Transparenz und Fade-Animationen)
2. Im `VisitorModeWidget.__init__` (bzw. `_init_ui`) instanziieren
3. In `_position_overlays()` positionieren und `raise_()` aufrufen
4. Falls bilingual: `update_language()` ueberschreiben und in `_on_language_toggled()` aufrufen
5. Dimensionen als frozen Dataclass in `dimensions.py` definieren

### Neuen Content bilingual machen

1. Content-Datei in `media/content/` erstellen oder anpassen: Wert von `str` auf `dict[str, str]` aendern
2. Widget-Konstruktor: Zugriff mit `["de"]` als Default
3. `update_language()`-Override implementieren
4. In `VisitorModeWidget._on_language_toggled()` die Widget-Liste erweitern
