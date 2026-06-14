# Admin Mode

Dieses Dokument beschreibt den Admin-Modus der CNN-Visualisierungs-Anwendung. Der Admin-Modus ist ein Preset-Editor mit Live-Vorschau, ueber den Presets fuer jeden Layer konfiguriert und persistent gespeichert werden koennen.

---

## Inhaltsverzeichnis

1. [Zweck und Zugang](#zweck-und-zugang)
2. [Package-Struktur](#package-struktur)
3. [Komponenten](#komponenten)
4. [Datenfluss](#datenfluss)
5. [UI-Aufbau](#ui-aufbau)
6. [Channel-Verwaltung](#channel-verwaltung)
7. [Visualisierungsmodi](#visualisierungsmodi)
8. [Live-Vorschau](#live-vorschau)
9. [Preset-Persistierung](#preset-persistierung)
10. [Seiteneffekte](#seiteneffekte)

---

## Zweck und Zugang

Der Admin-Modus richtet sich an Administratoren/Entwickler und ist nicht fuer Museumsbesucher gedacht. Er wird ueber `Ctrl+A` aus dem Visitor Mode heraus geoeffnet. Zurueck geht es mit `ESC` oder `Ctrl+V`.

Der Modus ermoeglicht:
- Auswahl eines Layers und eines von 3 Presets pro Layer
- Konfiguration aller Preset-Parameter (Channels, Colormap, Blend-Mode, Normalisierung, Visualisierungsmodus)
- Echtzeit-Vorschau der Aenderungen (ohne zu speichern)
- Persistentes Speichern von Presets
- Markieren eines Presets als "aktiv" (wird im Visitor Mode angezeigt)

---

## Package-Struktur

```
admin_mode/
    __init__.py              # Re-Export: AdminModeWidget
    admin_mode_widget.py     # Haupt-Widget (UI + Orchestrierung)
    channel_manager.py       # ChannelSpinBox + ChannelManager
    preset_builder.py        # PresetConfig-Factory
```

### Verantwortlichkeiten

| Modul                    | Verantwortlichkeit                                              |
|--------------------------|-----------------------------------------------------------------|
| `admin_mode_widget.py`   | UI-Aufbau, Signal-Handling, Lifecycle (start/stop), Facade-Aufrufe |
| `channel_manager.py`     | Channel-SpinBox-Steuerung, Add/Delete-Logik, Range-Updates, Visibility |
| `preset_builder.py`      | PresetConfig-Erstellung aus UI-Werten (stateless Helper)        |

Die Aufteilung folgt dem Prinzip der Verantwortungstrennung: Das Widget baut die UI auf und reagiert auf Events, der ChannelManager steuert die SpinBox-Logik, und der PresetBuilder konsolidiert die PresetConfig-Erstellung.

---

## Komponenten

### AdminModeWidget

**Datei:** `admin_mode_widget.py`

Hauptklasse des Admin-Modus. Erbt von `QWidget`.

**Konstruktor-Parameter:**

| Parameter | Typ                 | Beschreibung                |
|-----------|---------------------|-----------------------------|
| `facade`  | `ApplicationFacade` | Zugriff auf Geschaeftslogik |

**Zustand:**

| Attribut              | Typ    | Beschreibung                               |
|-----------------------|--------|--------------------------------------------|
| `_current_layer`      | `str`  | Aktuell bearbeiteter Layer (initial: erster Layer) |
| `_current_preset_id`  | `int`  | Aktuell bearbeitetes Preset (0, 1 oder 2)   |
| `_camera_thread`      | `CameraThread | Aktiver Thread fuer Live-Vorschau      |

**Lifecycle:**

| Methode   | Beschreibung                                                    |
|-----------|-----------------------------------------------------------------|
| `start()` | Synchronisiert Preset-Selector auf aktives Preset, erstellt CameraThread, startet Live-Vorschau |
| `stop()`  | Stoppt CameraThread, setzt Preview-Display zurueck              |

---

### ChannelSpinBox

**Datei:** `channel_manager.py`

Custom `QSpinBox` mit eingeschraenkter Eingabe. Der Wert `-1` (Sentinel fuer "nicht belegt") kann nur programmatisch gesetzt werden, nicht durch User-Interaktion.

**Einschraenkungen:**

| Eingabeweg       | Verhalten                                          |
|------------------|----------------------------------------------------|
| Pfeiltasten      | `stepBy()` ueberschrieben: Minimum ist 0           |
| Tastatureingabe  | `validate()` ueberschrieben: `-` wird abgelehnt    |
| Programmatisch   | `setProgrammaticValue(value)`: Erlaubt -1           |

Der Mechanismus: `setProgrammaticValue()` setzt ein internes Flag `_allow_negative = True`, ruft `setValue()` auf und setzt das Flag zurueck.

---

### ChannelManager

**Datei:** `channel_manager.py`

Verwaltet die Channel-SpinBoxen des Colormap- und RGB-Modus. Erstellt keine eigenen UI-Elemente, sondern erhaelt Referenzen auf existierende Widgets vom `AdminModeWidget`.

**Konstruktor-Parameter:**

| Parameter        | Typ                    | Beschreibung                         |
|------------------|------------------------|--------------------------------------|
| `spinboxes`      | `list[ChannelSpinBox]` | Colormap-Channel-SpinBoxen (3)       |
| `rgb_spinboxes`  | `list[ChannelSpinBox]` | RGB-Channel-SpinBoxen (3)            |
| `rows`           | `list[QWidget]`        | Channel-Row-Container                |
| `delete_buttons` | `list[QPushButton      | Delete-Buttons (None fuer Channel 1) |
| `add_button`     | `QPushButton`          | Add-Channel-Button                   |

**Methoden:**

| Methode             | Beschreibung                                                    |
|---------------------|-----------------------------------------------------------------|
| `add_channel()`     | Findet ersten Channel mit Wert -1, setzt ihn auf 0, aktualisiert Visibility |
| `delete_channel(i)` | Entfernt Channel i, laesst nachfolgende aufruecken, fuegt -1 am Ende hinzu |
| `update_visibility()`| Setzt Sichtbarkeit von Rows und Add-Button basierend auf Channel-Werten |
| `update_range(n)`   | Setzt SpinBox-Range auf [−1, n−1] (Colormap) bzw. [0, n−1] (RGB) |
| `get_channels()`    | Gibt aktuelle Colormap-Channel-Werte zurueck (kann -1 enthalten) |
| `get_rgb_channels()` | Gibt aktuelle RGB-Channel-Werte zurueck (immer 3 Werte)        |
| `set_channels()`    | Setzt Colormap-Channels programmatisch (fehlende werden mit -1 aufgefuellt) |
| `set_rgb_channels()` | Setzt RGB-Channels (fehlende werden mit Fallback 0, 1, 2 aufgefuellt) |

**Visibility-Regeln:**

- Channel 1 (Index 0) ist immer sichtbar und hat keinen Delete-Button
- Channel 2 und 3 (Index 1 und 2) sind sichtbar wenn ihr Wert != -1
- Der Add-Button ist sichtbar wenn weniger als 3 Channels aktiv sind

**Delete-Logik (Aufruecken):**

Beispiel: Channels sind [5, 10, 20]. User loescht Channel 2 (Index 1):
1. Entferne Wert an Index 1: [5, 20]
2. Fuege -1 am Ende hinzu: [5, 20, -1]
3. Setze SpinBox-Werte programmatisch (da -1 gesetzt wird)
4. Aktualisiere Visibility

---

### PresetBuilder

**Datei:** `preset_builder.py`

Stateless Helper-Klasse mit einer einzigen `@staticmethod` Methode `build_from_ui()`. Konsolidiert die PresetConfig-Erstellung, die sowohl bei der Live-Vorschau als auch beim Speichern benoetigt wird.

**Parameter:**

| Parameter      | Typ          | Beschreibung                              |
|----------------|--------------|-------------------------------------------|
| `preset_id`    | `int`        | 0, 1 oder 2                              |
| `name`         | `str`        | Anzeigename                               |
| `is_rgb_mode`  | `bool`       | True wenn RGB-Modus                       |
| `channels`     | `list[int]`  | Colormap-Channel-Werte (kann -1 enthalten)|
| `rgb_channels` | `list[int]`  | RGB-Channel-Werte (genau 3)               |
| `colormap`     | `str`        | Colormap-Name                             |
| `normalize`    | `bool`       | Normalisierung                            |
| `blend_mode`   | `str`        | Blend-Modus                               |

**Modus-spezifische Logik:**

Im RGB-Modus werden `normalize`, `blend_mode` und `colormap` erzwungen (`True`, `"max"`, `"viridis"`), da sie im RGB-Rendering nicht relevant sind. `channels` wird auf `rgb_channels` gesetzt, `visualization_mode` auf `"rgb"`.

Im Colormap-Modus werden inaktive Channels (-1) herausgefiltert. Alle Parameter werden unveraendert uebernommen. `visualization_mode` wird auf `"colormap"` gesetzt.

---

## Datenfluss

### Start des Admin-Modus

```
MainWindow.switch_to_admin_mode()
    |
    +--> VisitorModeWidget.stop()
    |
    +--> AdminModeWidget.start()
            |
            +--> facade.get_active_preset(current_layer)
            |       +--> Aktives Preset ermitteln
            |       +--> _current_preset_id synchronisieren
            |       +--> Preset-ComboBox setzen
            |       +--> _load_current_preset()
            |
            +--> CameraThread erstellen (facade, current_layer)
            |       +--> frame_ready --> CameraDisplayWidget.update_frame
            |       +--> error_occurred --> _on_error_occurred
            |
            +--> CameraThread.start()
            |
            +--> _on_param_changed()
                    +--> PresetBuilder.build_from_ui(UI-Werte)
                    +--> CameraThread.set_temp_preset(preset)
```

### Layer-Wechsel im Admin-Modus

```
User waehlt neuen Layer in ComboBox
    |
    +--> _on_layer_changed(layer_name)
            |
            +--> _current_layer = layer_name
            |
            +--> _update_channel_range(layer_name)
            |       +--> facade.get_layer_channel_count(layer_name)
            |       +--> ChannelManager.update_range(channel_count)
            |               +--> Colormap-SpinBoxen: Range [-1, count-1]
            |               +--> RGB-SpinBoxen: Range [0, count-1]
            |               +--> Werte > count auf 0 zuruecksetzen
            |
            +--> facade.get_active_preset(layer_name)
            |       +--> Preset-Selector synchronisieren
            |
            +--> _load_current_preset()
            |       +--> facade.get_preset(layer, preset_id)
            |       +--> UI-Controls mit Preset-Werten befuellen:
            |               +--> Name-Label setzen
            |               +--> Radio-Button (Colormap/RGB) setzen
            |               +--> Mode-Groups Visibility umschalten
            |               +--> Channels laden (je nach Modus)
            |               +--> Colormap-Combo setzen
            |               +--> Normalize-Checkbox setzen
            |               +--> Blend-Mode-Combo setzen
            |
            +--> CameraThread.change_layer(layer_name)
            +--> _on_param_changed()
```

### Parameter-Aenderung (Live-Vorschau)

```
User aendert Parameter (Channel-Wert, Colormap, Normalize, ...)
    |
    +--> _on_param_changed()
            |
            +--> PresetBuilder.build_from_ui(
            |       preset_id = _current_preset_id,
            |       name = "Live Preview (Preset X)",
            |       is_rgb_mode = RGB-Radio gecheckt?,
            |       channels = ChannelManager.get_channels(),
            |       rgb_channels = ChannelManager.get_rgb_channels(),
            |       colormap = Colormap-Combo Text,
            |       normalize = Normalize-Checkbox,
            |       blend_mode = Blend-Combo Text
            |   )
            |       |
            |       +--> (RGB) PresetConfig(channels=rgb_channels, mode="rgb", ...)
            |       +--> (Colormap) Filtere -1 heraus, PresetConfig(mode="colormap", ...)
            |
            +--> CameraThread.set_temp_preset(preset)
                    |
                    +--> (naechster Loop-Durchlauf)
                    +--> facade.get_visualization_with_preset(layer, preset)
                    +--> frame_ready.emit(frame)
                    +--> CameraDisplayWidget.update_frame(frame)
```

### Channel hinzufuegen

```
User klickt "+" Button
    |
    +--> _on_add_channel()
            |
            +--> ChannelManager.add_channel()
            |       +--> Finde ersten SpinBox mit Wert -1
            |       +--> Setze Wert auf 0
            |       +--> update_visibility()
            |
            +--> _on_param_changed()  (Live-Vorschau aktualisieren)
```

### Channel loeschen

```
User klickt "-" Button bei Channel i
    |
    +--> _on_delete_channel(i)
            |
            +--> ChannelManager.delete_channel(i)
            |       +--> Lese alle SpinBox-Werte: [v0, v1, v2]
            |       +--> Entferne Wert an Index i
            |       +--> Fuege -1 am Ende hinzu
            |       +--> Setze alle SpinBox-Werte programmatisch
            |       +--> update_visibility()
            |
            +--> _on_param_changed()  (Live-Vorschau aktualisieren)
```

### Preset speichern

```
User klickt "Preset speichern"
    |
    +--> _save_current_preset()
            |
            +--> facade.get_preset(layer, preset_id)
            |       +--> Aktuellen Preset-Namen holen
            |
            +--> PresetBuilder.build_from_ui(
            |       name = aktueller Preset-Name (nicht "Live Preview"),
            |       ... (restliche UI-Werte)
            |   )
            |
            +--> facade.save_preset(layer, preset_id, preset)
            |       +--> PresetService.save_preset()
            |       +--> ConfigManager.save()  (persistent auf Disk)
            |
            +--> QMessageBox.information("Erfolg", ...)
            |
            +--> (Bei Fehler) QMessageBox.critical("Fehler", ...)
```

### Preset als aktiv markieren

```
User klickt "Als aktiv markieren"
    |
    +--> _set_as_active_preset()
            |
            +--> facade.set_active_preset(layer, preset_id)
            |       +--> PresetService.set_active_preset()
            |       +--> ConfigManager.save()  (persistent auf Disk)
            |
            +--> QMessageBox.information("Erfolg", ...)
```

---

## UI-Aufbau

Das Layout ist horizontal zweigeteilt:

```
+----------------------------+---------------------------------------+
|  Preset-Editor (stretch=1) |  Live-Vorschau (stretch=2)            |
|                             |                                       |
|  [Preset-Editor Titel]      |  [Live-Vorschau Titel]                |
|                             |                                       |
|  [Layer auswaehlen]         |  +-------------------------------+    |
|  [ComboBox: conv1..layer4]  |  |                               |    |
|                             |  |   CameraDisplayWidget          |    |
|  [Preset auswaehlen]        |  |   (640x480 Minimum)            |    |
|  [ComboBox: Preset 1..3]    |  |                               |    |
|                             |  +-------------------------------+    |
|  [Parameter]                |                                       |
|  +-ScrollArea-----------+   |  "Aenderungen werden live angezeigt.  |
|  | Name: <label>        |   |   Druecken Sie 'Preset speichern'    |
|  |                      |   |   um die Einstellungen zu uebernehmen.|
|  | [Visualisierungsmodus]|  |                                       |
|  |  (o) Colormap         |  +---------------------------------------+
|  |  ( ) RGB              |
|  |                       |
|  | [Colormap-Einstellungen] |   (sichtbar wenn Colormap aktiv)
|  |  Channel 1: [SpinBox]   |
|  |  Channel 2: [SpinBox][-] |
|  |  Channel 3: [SpinBox][-] |
|  |  [+]                     |
|  |  Colormap: [ComboBox]    |
|  |                          |
|  | [RGB-Einstellungen]      |   (sichtbar wenn RGB aktiv)
|  |  Rot:   [SpinBox]        |
|  |  Gruen: [SpinBox]        |
|  |  Blau:  [SpinBox]        |
|  |                          |
|  | [x] Normalisierung       |   (nur Colormap-Mode)
|  | Blend-Modus: [ComboBox]  |   (nur Colormap-Mode)
|  +-------------------------+
|
|  [Preset speichern]         |
|  [Als aktiv markieren]      |
+----------------------------+
```

### Editor-Panel Sections

Das Editor-Panel besteht aus vertikalen Sections, die in `_create_editor_panel()` zusammengebaut werden:

1. **Titel** (`_create_editor_title()`): QLabel "Preset-Editor", fett, 18pt
2. **Layer-Auswahl** (`_create_layer_section()`): QGroupBox mit QComboBox. Items kommen aus `facade.get_layer_names()`
3. **Preset-Auswahl** (`_create_preset_section()`): QGroupBox mit QComboBox. Feste Items: "Preset 1", "Preset 2", "Preset 3"
4. **Parameter** (`_create_params_section()`): Scrollbare QGroupBox mit allen Konfigurationsoptionen
5. **Speichern-Button** (`_create_save_button()`): QPushButton mit Success-Style
6. **Aktiv-Button** (`_create_set_active_button()`): QPushButton

### Preview-Panel

Rechte Seite mit `CameraDisplayWidget` (Minimum 640x480) und Info-Text.

---

## Channel-Verwaltung

### Colormap-Mode

Im Colormap-Mode koennen 1 bis 3 Channels konfiguriert werden. Jeder Channel ist eine Zeile mit:
- Label ("Channel 1:", "Channel 2:", "Channel 3:")
- `ChannelSpinBox` (Range: -1 bis channel_count-1)
- Delete-Button ("-") fuer Channels 2 und 3

Der Wert `-1` ist der Sentinel fuer "nicht belegt". Nur programmatisch setzbar (nicht durch User-Eingabe). Der `specialValueText` ist auf `""` gesetzt, sodass `-1` als leeres Feld angezeigt wird.

Der Add-Button ("+") ist sichtbar, solange weniger als 3 Channels aktiv sind.

### RGB-Mode

Im RGB-Mode sind exakt 3 Channels erforderlich (R, G, B). Die SpinBoxen haben die Range [0, channel_count-1]. Es gibt keine Add/Delete-Buttons. Die Channels werden mit "Rot:", "Gruen:", "Blau:" beschriftet.

### Range-Updates bei Layer-Wechsel

Beim Wechsel des Layers wird `_update_channel_range()` aufgerufen:

1. `facade.get_layer_channel_count(layer_name)` liefert die Anzahl der Channels (z.B. 64 fuer layer1, 512 fuer layer4)
2. `ChannelManager.update_range(count)` setzt:
   - Colormap-SpinBoxen: Range [-1, count-1]
   - RGB-SpinBoxen: Range [0, count-1]
   - Werte die ausserhalb des neuen Bereichs liegen werden auf 0 zurueckgesetzt

---

## Visualisierungsmodi

### Modus-Wechsel

Der Modus wird ueber QRadioButtons ("Colormap" / "RGB") umgeschaltet. Bei Aenderung (`_on_mode_changed()`):

1. Colormap-GroupBox sichtbar/unsichtbar setzen
2. RGB-GroupBox sichtbar/unsichtbar setzen
3. Normalize-Checkbox und Blend-Mode-Row ausblenden im RGB-Mode
4. Bei Wechsel zu RGB: Normalisierung auf True und Blend-Mode auf "max" erzwingen
5. Live-Vorschau aktualisieren

### Colormap-Mode

- 1-3 Channels (dynamisch, Add/Delete)
- Colormap-Auswahl: viridis, plasma, inferno, magma, jet, hot
- Normalisierung (Checkbox)
- Blend-Mode: max, mean, overlay

### RGB-Mode

- Exakt 3 Channels (R, G, B)
- Keine Colormap, keine Normalisierung, kein Blend-Mode (Werte werden erzwungen)
- Jeder Channel wird direkt auf eine Farbkomponente gemappt

---

## Live-Vorschau

Jede Parameter-Aenderung loest `_on_param_changed()` aus. Diese Methode:

1. Erstellt ein temporaeres `PresetConfig` via `PresetBuilder.build_from_ui()`
2. Setzt es auf dem `CameraThread` via `set_temp_preset()`
3. Im naechsten Schleifendurchlauf des Threads wird `facade.get_visualization_with_preset()` mit dem temporaeren Preset aufgerufen
4. Das Ergebnis wird via `frame_ready` Signal an das `CameraDisplayWidget` weitergereicht

Wichtig: Die Live-Vorschau speichert nichts persistent. Das temporaere Preset existiert nur im CameraThread. Erst "Preset speichern" schreibt in die `config.json`.

---

## Preset-Persistierung

### Speichern

`_save_current_preset()` liest den Preset-Namen aus dem aktuell gespeicherten Preset (nicht den Live-Preview-Namen), erstellt ein `PresetConfig` aus den UI-Werten und ruft `facade.save_preset()` auf.

Die Facade delegiert an `PresetService.save_preset()`, das wiederum den `ConfigManager` des Storage Layers aufruft. Die gesamte Konfiguration wird als `config.json` auf Disk geschrieben.

### Aktiv setzen

`_set_as_active_preset()` ruft `facade.set_active_preset(layer, preset_id)` auf. Dies aendert die `active_preset_id` fuer den Layer und persistiert die Aenderung.

### Preset laden

`_load_current_preset()` liest das Preset via `facade.get_preset(layer, preset_id)` und befuellt alle UI-Controls:

1. Preset-Name in Label setzen
2. Radio-Button basierend auf `visualization_mode` setzen
3. Mode-Groups Visibility umschalten
4. Channels laden (je nach Modus ueber `ChannelManager.set_channels()` oder `set_rgb_channels()`)
5. Colormap-Combo auf gespeicherten Wert setzen
6. Normalize-Checkbox setzen
7. Blend-Mode-Combo setzen

---

## Seiteneffekte

### AdminModeWidget

| Methode                    | Seiteneffekt                                                      |
|----------------------------|-------------------------------------------------------------------|
| `start()`                  | Erstellt CameraThread, verbindet Signals, startet Thread          |
| `stop()`                   | Stoppt CameraThread, setzt Preview-Display zurueck                |
| `_on_layer_changed()`      | Aendert _current_layer, aktualisiert SpinBox-Ranges, laedt Preset |
| `_on_preset_changed()`     | Aendert _current_preset_id, laedt Preset, aktualisiert Vorschau   |
| `_on_param_changed()`      | Setzt temporaeres Preset auf CameraThread (keine Persistierung)   |
| `_save_current_preset()`   | Schreibt Preset persistent auf Disk (via Facade -> Storage)       |
| `_set_as_active_preset()`  | Aendert aktives Preset persistent auf Disk (via Facade -> Storage)|

### ChannelManager

Alle Methoden sind seiteneffektfrei in Bezug auf externe Systeme. Sie aendern nur die Werte und Sichtbarkeit der referenzierten UI-Widgets.

### PresetBuilder

Komplett seiteneffektfrei. Erstellt ein neues `PresetConfig`-Objekt aus uebergebenen Werten.
