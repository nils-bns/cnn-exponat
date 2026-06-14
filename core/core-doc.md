# Core Layer

Dieses Dokument beschreibt Aufbau, Verantwortlichkeiten und Zusammenspiel der Komponenten im `core/`-Package. Es richtet sich an Entwickler, die den Code warten, erweitern oder reviewen.

---

## Inhaltsverzeichnis

1. [Einordnung in die Gesamtarchitektur](#einordnung-in-die-gesamtarchitektur)
2. [Package-Struktur](#package-struktur)
3. [Datenmodelle](#datenmodelle)
4. [Interfaces (Protocols)](#interfaces-protocols)
5. [Services](#services)
6. [Facade](#facade)
7. [Exceptions](#exceptions)
8. [Datenfluss](#datenfluss)
9. [Seiteneffekte](#seiteneffekte)
10. [Design-Entscheidungen](#design-entscheidungen)
11. [Erweiterung](#erweiterung)

---

## Einordnung in die Gesamtarchitektur

Die Anwendung folgt einer Drei-Schichten-Architektur:

```
View (PyQt6)  -->  Core (Services + Facade)  -->  Storage (JSON-Config)
```

Der Core Layer ist die mittlere Schicht. Er enthaelt die gesamte Geschaeftslogik und stellt sie ueber eine Facade bereit. Der View Layer greift ausschliesslich ueber die `ApplicationFacade` auf den Core zu -- nie direkt auf einzelne Services. Der Storage Layer wird vom Core ueber das `IConfigStorage`-Interface angesprochen.

Abhaengigkeitsrichtung: View haengt von Core ab, Core haengt von Storage ab. Umgekehrte Abhaengigkeiten existieren nicht.

---

## Package-Struktur

```
core/
    __init__.py                 # Public API: Models, Facade, Exceptions
    exceptions.py               # Exception-Hierarchie
    facade.py                   # ApplicationFacade (Orchestrierung)
    models.py                   # Dataclasses (PresetConfig, LayerPresets, ConfigData)
    interfaces/
        __init__.py             # Re-Export aller Protocols
        i_camera_service.py     # ICameraService Protocol
        i_model_service.py      # IModelService Protocol
        i_visualization_service.py  # IVisualizationService Protocol
        i_preset_service.py     # IPresetService Protocol
    services/
        camera_service.py       # Webcam-Zugriff via OpenCV
        model_service.py        # ResNet18-Inferenz und Layer-Extraktion
        visualization_service.py    # Feature-Map-Rendering
        preset_service.py       # Preset-Verwaltung
```

---

## Datenmodelle

Definiert in `models.py`. Alle Modelle sind `@dataclass`-Klassen mit Validierung im `__post_init__`.

### PresetConfig

Repraesentiert eine einzelne Visualisierungs-Konfiguration.

| Feld                | Typ         | Default       | Beschreibung |
|---------------------|-------------|---------------|--------------|
| `preset_id`         | `int`       | --            | 0, 1 oder 2 |
| `name`              | `str`       | --            | Anzeigename |
| `channels`          | `list[int]` | --            | Channel-Indizes. `-1` bedeutet "nicht belegt" |
| `colormap`          | `str`       | `"viridis"`   | Matplotlib-Colormap-Name |
| `normalize`         | `bool`      | `True`        | Min-Max-Normalisierung an/aus |
| `blend_mode`        | `str`       | `"max"`       | `max`, `mean` oder `overlay` |
| `visualization_mode`| `str`       | `"colormap"`  | `colormap` oder `rgb` |

Validierungsregeln:
- `preset_id` muss 0, 1 oder 2 sein.
- Mindestens ein gueltiger Channel (nicht -1) ist erforderlich.
- Im `rgb`-Mode muessen genau 3 Channels angegeben sein.
- `blend_mode` ist auf die drei genannten Werte beschraenkt.

### LayerPresets

Gruppiert bis zu 3 Presets fuer einen bestimmten Layer.

| Feld               | Typ                  | Default | Beschreibung |
|--------------------|----------------------|---------|--------------|
| `layer_name`       | `str`                | --      | z.B. `"layer1"` |
| `presets`          | `list[PresetConfig]` | `[]`    | Maximal 3 Eintraege |
| `active_preset_id` | `int`                | `0`     | Welches Preset aktiv ist |

### ConfigData

Top-Level-Datenstruktur, die der `config.json` entspricht.

| Feld      | Typ                          | Default | Beschreibung |
|-----------|------------------------------|---------|--------------|
| `presets`  | `dict[str, LayerPresets]`   | `{}`    | Key = Layer-Name |
| `version` | `str`                        | `"1.0"` | Schema-Version |

---

## Interfaces (Protocols)

Alle Interfaces liegen in `core/interfaces/` und verwenden `typing.Protocol` (strukturelles Subtyping). Es gibt keine expliziten Vererbungen -- eine Klasse erfuellt ein Protocol, wenn sie die passenden Methoden implementiert.

### ICameraService

Webcam-Zugriff. Lifecycle: `start()` -> `get_frame()` (beliebig oft) -> `stop()`.

```
start() -> None
stop() -> None
get_frame() -> np.ndarray        # RGB (H, W, 3)
is_running() -> bool
```

### IModelService

CNN-Modell und Inferenz.

```
load_model() -> None
get_layer_names() -> list[str]
get_layer_channel_count(layer_name: str) -> int
extract_layer_activations(image: np.ndarray, layer_name: str) -> torch.Tensor
get_top_predictions(k: int = 3) -> list[tuple[str, float]]
compute_gradcam(image: np.ndarray, layer_name: str) -> np.ndarray
```

### IVisualizationService

Rendering von Feature Maps.

```
visualize(activations: torch.Tensor, preset: PresetConfig) -> np.ndarray
```

### IPresetService

Preset-CRUD und Zustandsverwaltung.

```
get_preset(layer_name: str, preset_id: int) -> PresetConfig
get_active_preset(layer_name: str) -> PresetConfig
set_active_preset(layer_name: str, preset_id: int) -> None
save_preset(layer_name: str, preset_id: int, preset: PresetConfig) -> None
get_all_presets_for_layer(layer_name: str) -> list[PresetConfig]
```

---

## Services

### CameraService

**Datei:** `services/camera_service.py`

Kapselt OpenCV-Kamerazugriff. Konvertiert intern von BGR (OpenCV-Standard) nach RGB. Der Default-Kamera-Index ist `0` und wird als Klassenkonstante `DEFAULT_CAMERA_INDEX` gefuehrt.

Zustand: `_running` (bool) und `_camera` (VideoCapture oder None). Nach `stop()` wird die VideoCapture-Instanz freigegeben.

### ModelService

**Datei:** `services/model_service.py`

Laedt ein vortrainiertes ResNet18-Modell und registriert Forward-Hooks auf den fuenf extrahierbaren Layern:

| Layer   | Channels |
|---------|----------|
| `conv1` | 64       |
| `layer1`| 64       |
| `layer2`| 128      |
| `layer3`| 256      |
| `layer4`| 512      |

Die Channel-Anzahlen sind als Dictionary in `get_layer_channel_count()` hardcoded, weil die ResNet18-Architektur fix ist. Eine dynamische Ermittlung ueber Hooks waere unnoetig aufwaendig.

**Forward Pass:** `extract_layer_activations()` fuehrt einen Forward Pass durch (`torch.no_grad`), speichert alle Aktivierungen ueber die registrierten Hooks und gibt den gewuenschten Layer zurueck. Die Batch-Dimension wird entfernt, sodass das Ergebnis die Form `(C, H, W)` hat.

**Predictions:** `get_top_predictions()` liest die gecachten Logits des letzten Forward Pass, wendet Softmax an und gibt die Top-K Klassen zurueck. Die Labels stammen aus den ImageNet-Metadaten der Weights.

**GradCAM:** `compute_gradcam()` fuehrt einen separaten Forward+Backward Pass mit Gradienten durch. Temporaere Hooks werden nach Verwendung entfernt (finally-Block). Das Ergebnis ist ein RGB-Overlay aus Heatmap und Eingabebild.

### VisualizationService

**Datei:** `services/visualization_service.py`

Transformiert einen Aktivierungs-Tensor in ein darstellbares RGB-Bild. Unterstuetzt zwei Modi:

**Colormap-Mode** (Standard):
1. Channel-Auswahl (`_select_channels`) -- filtert `-1`-Eintraege und ungueltige Indizes
2. Blending (`_blend_channels`) -- `max`, `mean` oder `overlay`
3. Normalisierung (`_normalize`) -- Min-Max auf [0, 1]
4. Colormap-Anwendung (`_apply_colormap`) -- Matplotlib-Colormaps
5. Resize auf `DISPLAY_WIDTH x DISPLAY_HEIGHT` (800x600)

**RGB-Mode:**
Drei ausgewaehlte Channels werden direkt auf R, G, B gemappt. Jeder Channel wird separat normalisiert. Kein Blending, keine Colormap.

Der `overlay`-Blend-Mode verwendet Luma-Koeffizienten nach ITU-R BT.601 (0.299, 0.587, 0.114) fuer perzeptuelle Helligkeitsgewichtung.

### PresetService

**Datei:** `services/preset_service.py`

Verwaltet Presets ueber das `IConfigStorage`-Interface des Storage Layers. Laedt die Konfiguration einmalig beim Start und haelt sie im Speicher. Aenderungen (Save, Set Active) werden sofort persistent geschrieben.

Validierung von `layer_name` und `preset_id` erfolgt in privaten Hilfsmethoden (`_validate_layer_name`, `_validate_preset_id`).

---

## Facade

**Datei:** `facade.py`

Die `ApplicationFacade` ist der einzige Einstiegspunkt fuer den View Layer. Sie nimmt alle vier Services per Constructor Injection entgegen und orchestriert deren Zusammenspiel.

### Lifecycle

```python
facade = ApplicationFacade(camera, model, visualization, presets)
facade.initialize()      # Modell laden + Kamera starten + initialen Layer setzen
# ... Anwendung laeuft ...
facade.shutdown()        # Kamera stoppen
```

### Visualisierungs-Workflow

Die zentrale Methode `get_visualization_for_layer(layer_name)` fuehrt die komplette Pipeline durch:

1. Frame von Kamera holen
2. Layer-Aktivierungen extrahieren (Forward Pass)
3. Aktives Preset fuer den Layer laden
4. Visualisierung rendern

`get_visualization_with_preset()` funktioniert identisch, verwendet aber ein uebergebenes Preset statt des aktiven -- gedacht fuer Live-Vorschau im Admin-Mode.

### Delegation

Die meisten Methoden delegieren direkt an den zustaendigen Service:

| Facade-Methode                | Delegiert an        |
|-------------------------------|---------------------|
| `get_layer_names()`           | ModelService        |
| `get_layer_channel_count()`   | ModelService        |
| `get_top_predictions()`       | ModelService        |
| `compute_gradcam()`           | ModelService        |
| `get_preset()`                | PresetService       |
| `get_active_preset()`         | PresetService       |
| `set_active_preset()`         | PresetService       |
| `save_preset()`               | PresetService       |
| `get_all_presets_for_layer()` | PresetService       |

### State

Die Facade haelt nur ein einziges Stueck eigenen Zustand: `_current_layer` (der aktuell ausgewaehlte Layer). Layer-Wechsel werden ueber `change_layer()` mit Validierung gegen die verfuegbaren Layer durchgefuehrt.

---

## Exceptions

Definiert in `exceptions.py`. Hierarchisch aufgebaut mit `CNNVisualizationError` als Basis:

```
CNNVisualizationError
    CameraError
        CameraNotAvailableError
        CameraFrameError
    ModelError
        ModelLoadError
        InvalidLayerError
    ConfigError
        InvalidPresetError
        ConfigLoadError
        ConfigSaveError
```

Die Hierarchie erlaubt sowohl granulares als auch uebergreifendes Exception-Handling. Beispiel: `except CameraError` faengt sowohl "Kamera nicht verfuegbar" als auch "Frame nicht lesbar" ab.

---

## Datenfluss

Ein typischer Visualisierungs-Zyklus:

```
View ruft facade.get_visualization_for_layer("layer2") auf
    |
    +--> CameraService.get_frame()
    |        Kamera -> BGR Frame -> RGB NumPy-Array (H, W, 3)
    |
    +--> ModelService.extract_layer_activations(frame, "layer2")
    |        RGB-Bild -> Preprocessing (Resize 224x224, Normalize)
    |        -> Forward Pass durch ResNet18
    |        -> Hook speichert Aktivierung
    |        -> Tensor (128, H, W) fuer layer2
    |
    +--> PresetService.get_active_preset("layer2")
    |        -> PresetConfig aus gespeicherter Konfiguration
    |
    +--> VisualizationService.visualize(tensor, preset)
    |        -> Channel-Auswahl -> Blending -> Normalisierung
    |        -> Colormap -> Resize auf 800x600
    |        -> RGB NumPy-Array (600, 800, 3)
    |
    +--> Rueckgabe an View zur Darstellung
```

---

## Seiteneffekte

Nicht alle Methoden im Core Layer sind seiteneffektfrei. Dieser Abschnitt listet alle Methoden auf, die Zustand veraendern, Hardware ansprechen oder auf das Dateisystem schreiben. Die Kenntnis dieser Seiteneffekte ist relevant fuer Fehlersuche, Testbarkeit und das Verstaendnis der Aufruf-Reihenfolge.

### Uebersicht

| Methode | Service | Art des Seiteneffekts |
|---------|---------|-----------------------|
| `start()` | CameraService | Hardware (Kamera oeffnen) |
| `stop()` | CameraService | Hardware (Kamera freigeben) |
| `load_model()` | ModelService | Speicher (Modell laden, Hooks registrieren) |
| `extract_layer_activations()` | ModelService | Interner Zustand (Aktivierungs-Cache, Logit-Cache) |
| `compute_gradcam()` | ModelService | Interner Zustand (Gradienten-Reset) |
| `set_active_preset()` | PresetService | Dateisystem (config.json schreiben) |
| `save_preset()` | PresetService | Dateisystem (config.json schreiben) |
| `initialize()` | Facade | Kombiniert: Hardware + Speicher + Zustand |
| `change_layer()` | Facade | Interner Zustand (`_current_layer`) |
| `shutdown()` | Facade | Hardware (Kamera freigeben) |

### CameraService

**`start()`** -- Oeffnet die physische Kamera ueber `cv2.VideoCapture`. Das belegt eine Hardware-Ressource des Betriebssystems. Wenn die Kamera bereits durch einen anderen Prozess belegt ist, schlaegt der Aufruf fehl (`CameraNotAvailableError`). Ein doppelter Aufruf ist harmlos -- die Methode erkennt `_running == True` und kehrt frueh zurueck.

**`stop()`** -- Gibt die VideoCapture-Instanz frei und setzt den internen Zustand zurueck (`_camera = None`, `_running = False`). Muss aufgerufen werden, bevor die Anwendung beendet wird, da die Kamera-Ressource sonst vom Betriebssystem erst nach Prozessende freigegeben wird. Ein Aufruf im Zustand "nicht gestartet" ist harmlos.

### ModelService

**`load_model()`** -- Laedt das ResNet18-Modell mit vortrainierten ImageNet-Gewichten in den GPU- oder CPU-Speicher. Registriert Forward-Hooks auf allen fuenf Layern. Nach diesem Aufruf bleiben die Hooks fuer die gesamte Lebensdauer des Service bestehen. Der Speicherverbrauch liegt bei ca. 45 MB (ResNet18). Darf nur einmal aufgerufen werden -- ein zweiter Aufruf wuerde doppelte Hooks registrieren.

**`extract_layer_activations()`** -- Fuehrt einen Forward Pass durch und hat dabei zwei Seiteneffekte:
1. `_activations` wird zunaechst geleert (`clear()`) und dann durch die Hooks mit den Aktivierungen aller Layer neu befuellt. Alte Aktivierungen aus einem vorherigen Aufruf sind danach nicht mehr verfuegbar.
2. `_last_output` wird mit den Logits des Forward Pass ueberschrieben. Dieser Wert wird von `get_top_predictions()` gelesen. Die Predictions beziehen sich also immer auf den zuletzt verarbeiteten Frame.

Diese beiden Seiteneffekte sind gewollt: Sie bilden einen impliziten Cache, der verhindert, dass fuer Predictions ein separater Forward Pass noetig ist.

**`compute_gradcam()`** -- Fuehrt einen eigenen Forward+Backward Pass mit aktivierten Gradienten durch. Dabei wird `model.zero_grad()` aufgerufen, was alle bestehenden Gradienten im Modell zuruecksetzt. Die temporaeren Hooks (fuer Aktivierung und Gradient) werden im `finally`-Block entfernt, sodass keine Hooks zurueckbleiben. Die regulaeren Forward-Hooks aus `_register_hooks()` werden davon nicht beruehrt, aber `_activations` und `_last_output` werden durch den internen Forward Pass ueberschrieben.

### PresetService

**`set_active_preset()`** -- Aendert die `active_preset_id` im In-Memory-Zustand und schreibt die gesamte Konfiguration anschliessend persistent auf das Dateisystem (`config.json`). Der Schreibvorgang erfolgt ueber den ConfigManager des Storage Layers.

**`save_preset()`** -- Ersetzt ein bestehendes Preset in der In-Memory-Konfiguration (oder fuegt ein neues hinzu, falls keines mit der ID existiert) und schreibt danach persistent. Beide Operationen -- In-Memory-Update und Disk-Write -- passieren synchron im selben Aufruf. Es gibt keine Moeglichkeit, nur im Speicher zu aendern ohne zu persistieren.

### Facade

**`initialize()`** -- Kombiniert drei Seiteneffekte in fester Reihenfolge:
1. `model.load_model()` -- Modell in Speicher laden
2. `camera.start()` -- Kamera-Hardware oeffnen
3. `_current_layer` auf den ersten verfuegbaren Layer setzen

Wenn Schritt 1 fehlschlaegt (`ModelLoadError`), wird Schritt 2 nicht ausgefuehrt. Wenn Schritt 2 fehlschlaegt (`CameraNotAvailableError`), ist das Modell bereits geladen, aber die Kamera nicht gestartet. Eine partielle Initialisierung ist also moeglich und muss vom Aufrufer behandelt werden.

**`change_layer()`** -- Setzt `_current_layer` auf den neuen Wert. Validiert vorher gegen die verfuegbaren Layer und wirft `ValueError` bei ungueltigem Namen. Kein Seiteneffekt auf Hardware oder Dateisystem -- rein interner Zustand.

**`shutdown()`** -- Ruft `camera.stop()` auf und faengt dabei auftretende Exceptions ab (Logging statt Weiterwerfen). Dadurch ist `shutdown()` sicher aufrufbar, auch wenn die Kamera nie gestartet wurde oder bereits gestoppt ist.

### Seiteneffektfreie Methoden

Alle anderen Methoden sind seiteneffektfrei. Sie lesen vorhandenen Zustand oder transformieren Daten, ohne etwas zu veraendern:

- Alle `get_*`-Methoden der Facade (ausser `get_visualization_for_layer` und `get_visualization_with_preset`, die indirekt `extract_layer_activations` aufrufen und damit den Aktivierungs-Cache ueberschreiben)
- `VisualizationService.visualize()` und alle privaten Hilfsmethoden
- `PresetService.get_preset()`, `get_active_preset()`, `get_all_presets_for_layer()`
- `ModelService.get_layer_names()`, `get_layer_channel_count()`, `get_top_predictions()`
- `CameraService.is_running()`

Wichtiger Sonderfall: `get_visualization_for_layer()` und `get_visualization_with_preset()` wirken auf den ersten Blick wie reine Getter, loesen aber intern `extract_layer_activations()` aus. Damit ueberschreiben sie den Aktivierungs- und Logit-Cache im ModelService.

---

## Design-Entscheidungen

### Protocol statt ABC

Interfaces verwenden `typing.Protocol` (strukturelles Subtyping) statt `abc.ABC`. Services muessen nicht explizit von einem Interface erben -- sie erfuellen es automatisch, wenn die passenden Methoden vorhanden sind. Das reduziert Kopplungen und vereinfacht Tests (Mock-Objekte brauchen keine Vererbung).

### Facade Pattern

Der View Layer kommuniziert nie direkt mit Services. Die Facade buendelt den Zugriff, orchestriert den Datenfluss und kapselt die interne Service-Struktur. Aenderungen an einzelnen Services (z.B. ein anderes CNN-Modell) erfordern keine Aenderungen im View.

### Dependency Injection

Alle Services werden in `main.py` instanziiert und der Facade per Constructor Injection uebergeben. Das ermoeglicht Testbarkeit (Mocking) und macht Abhaengigkeiten explizit sichtbar.

### Hardcoded Channel Counts

`ModelService.get_layer_channel_count()` gibt Werte aus einem statischen Dictionary zurueck statt sie dynamisch zu ermitteln. Begruendung: Die Architektur von ResNet18 ist fix. Eine dynamische Ermittlung (z.B. ueber einen Probe-Forward-Pass) waere unverhältnismäßig aufwaendig fuer keinen praktischen Nutzen.

### Channel-Sentinel -1

Der Wert `-1` in `PresetConfig.channels` bedeutet "nicht belegt". Das erlaubt flexible Channel-Konfigurationen mit variabler Laenge (1-3 Channels), wobei immer eine feste Listenlaenge beibehalten werden kann. Alle Services filtern `-1`-Eintraege vor der Verarbeitung heraus.

---

## Erweiterung

### Neuen Service hinzufuegen

1. Protocol in `core/interfaces/` definieren
2. Implementation in `core/services/` erstellen
3. Protocol in `core/interfaces/__init__.py` re-exportieren
4. Facade um Delegation-Methoden erweitern
5. In `main.py` instanziieren und der Facade uebergeben

### Neues CNN-Modell unterstuetzen

Der `ModelService` ist auf ResNet18 spezialisiert. Fuer ein anderes Modell:

1. Neuen Service erstellen, der `IModelService` erfuellt
2. `AVAILABLE_LAYERS` und `channel_counts` anpassen
3. Hook-Registrierung auf die neue Architektur abstimmen
4. In `main.py` den neuen Service statt `ModelService` verwenden

### Neuen Visualisierungs-Mode hinzufuegen

1. In `PresetConfig.__post_init__` den neuen Mode zur Validierung hinzufuegen
2. In `VisualizationService.visualize()` das Routing erweitern
3. Eigene `_visualize_[mode]_mode()`-Methode implementieren
