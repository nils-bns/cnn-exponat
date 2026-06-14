# CNN-Visualisierung Museum-Projekt

Interaktive Visualisierung der Repraesentationen eines Convolutional Neural Networks (ResNet18) fuer Museums-Installationen.

## Technische Hochschule Ostwestfalen-Lippe 
### Fachbereich 8, Angewandte Informatik
### Wintersemester 2025 / 2026
### Team:
- Marten Ahmann
- Nils Berns
- Mohamed Cheikh
- Daniel Hofmann
- Dylan Senger
- Fighan Suliman

---

## Inhaltsverzeichnis

- [Ueber das Projekt](#ueber-das-projekt)
- [Features](#features)
- [Systemvoraussetzungen](#systemvoraussetzungen)
- [Installation](#installation)
- [Verwendung](#verwendung)
- [Architektur](#architektur)
- [Tests](#tests)
- [Konfiguration](#konfiguration)
- [Entwicklung](#entwicklung)
- [Dokumentation](#dokumentation)
- [Troubleshooting](#troubleshooting)

---

## Ueber das Projekt

Dieses Projekt ermoeglicht Museumsbesuchern ein intuitives Verstaendnis davon, wie ein Convolutional Neural Network (CNN) Bilder intern verarbeitet. Die Anwendung visualisiert in Echtzeit, wie verschiedene Layer eines ResNet18-Modells auf Live-Kamera-Input reagieren.

**Hauptzielgruppen:**
- **Museumsbesucher**: Interaktive Exploration ueber Touchscreen-Interface
- **Museumspersonal**: Anpassung von Visualisierungs-Presets ueber den Admin-Modus

**Technologie-Stack:**
- **Deep Learning**: PyTorch, torchvision (ResNet18)
- **Computer Vision**: OpenCV
- **GUI Framework**: PyQt6
- **Architektur**: 3-Layer-Architecture (View, Core, Storage)

---

## Features

### Besuchermodus
- **Live-Visualisierung**: Echtzeit-Verarbeitung von Webcam-Input durch CNN-Layer
- **Layer-Navigation**: Touch-optimierte Buttons mit CNN-Architektur-Visualisierung fuer alle ResNet18-Layer
- **Vollbild-Modus**: Immersive Darstellung ohne Systemelemente
- **Kontextinformationen**: Erklaerende Texte zu jedem Layer (bilingual DE/EN)
- **GradCAM-Overlay**: Grad-weighted Class Activation Mapping fuer die letzten CNN-Layer
- **Top-3-Predictions**: Klassifikationsergebnisse als Balkendiagramm
- **About-Slideshow**: Aufklappbare Info-Seiten mit Projekt- und Institutsbeschreibung
- **Mehrsprachigkeit**: Vollstaendige Unterstuetzung fuer Deutsch und Englisch

### Admin-Modus
- **Preset-Editor**: Grafische Anpassung aller Visualisierungsparameter
- **Live-Vorschau**: Sofortiges Feedback bei Parameter-Aenderungen (ohne Speichern)
- **Flexible Channel-Auswahl**: 1 bis 3 Channels pro Preset, dynamisch hinzufueg- und entfernbar
- **Persistierung**: Speichern von Presets in JSON (atomare Schreiboperationen)
- **Preset-Verwaltung**: 3 Presets pro Layer, aktives Preset fuer Visitor-Modus waehlbar

### Visualisierungsmodi
- **Colormap**: Channel-Auswahl mit Blending (Max, Mean, Overlay) und Colormaps (Viridis, Plasma, Inferno, Magma, Jet, Hot)
- **RGB Composite**: Drei Channels direkt auf R, G, B gemappt

---

## Systemvoraussetzungen

### Hardware
- **CPU**: Intel i5 oder AMD Ryzen 5 (oder besser)
- **RAM**: 8 GB minimum (16 GB empfohlen)
- **GPU**: Optional - CUDA-faehige NVIDIA GPU fuer bessere Performance
- **Webcam**: USB-Webcam oder integrierte Kamera
- **Display**: 1920x1080 oder hoeher (Touchscreen optional)

### Software
- **Betriebssystem**: Windows 10/11, macOS 11+, Linux (Ubuntu 20.04+)
- **Python**: 3.13 oder hoeher
- **pip**: 23.0 oder hoeher

---

## Installation

### 1. herunterladen

```bash
# ZIP herunterladen und entpacken
```

### 2. Virtuelle Umgebung erstellen (empfohlen)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Hinweis**: Der erste Download kann laenger dauern, da PyTorch (~2 GB) heruntergeladen wird.

### 4. Installation verifizieren

```bash
# Unit-Tests ausfuehren
pytest tests/ -v

# Integration-Tests ausfuehren
pytest tests/test_integration.py -v
```

---

## Verwendung

### Standard-Modus (Besuchermodus)

```bash
python main.py
```

**Steuerung:**
- **Layer auswaehlen**: Auf Layer-Button klicken/tippen
- **Vollbild**: `F11` druecken
- **Fenster-Modus**: `F11` erneut druecken
- **Admin-Modus**: `Ctrl+A` druecken
- **Visitor-Modus**: `ESC` oder `Ctrl+V` druecken
- **Beenden**: `ESC` (im Vollbild) oder Fenster schliessen

### Admin-Modus

```bash
python main.py
# Dann: Ctrl+A druecken
```

**Funktionen:**
- **Preset bearbeiten**: Layer auswaehlen, Parameter anpassen, "Preset speichern"
- **Live-Vorschau**: Aenderungen werden sofort visualisiert (ohne zu speichern)
- **Als aktiv markieren**: Bestimmt welches Preset im Visitor-Modus angezeigt wird

### Konfigurationsdatei

Die Anwendung erstellt automatisch `config.json` im Projektverzeichnis. Diese kann auch manuell bearbeitet werden (Vorsicht: Struktur beachten!).

---

## Architektur

Das Projekt folgt einer strikten **3-Layer-Architecture**:

```
+---------------------------------------------------+
|                  VIEW LAYER                        |
|      PyQt6 UI, User Interaction, Threading         |
|  (MainWindow, VisitorMode, AdminMode, Widgets)     |
+------------------------+--------------------------+
                         | Qt Signals/Slots
+------------------------v--------------------------+
|                  CORE LAYER                        |
|     Business Logic, Services, Orchestration        |
|  (Facade, CameraService, ModelService, ...)        |
+------------------------+--------------------------+
                         | Data Objects
+------------------------v--------------------------+
|                STORAGE LAYER                       |
|        Data Persistence, JSON Management           |
|        (ConfigManager, DefaultConfig)              |
+---------------------------------------------------+
```

Abhaengigkeitsrichtung: View haengt von Core ab, Core haengt von Storage ab. Umgekehrte Abhaengigkeiten existieren nicht.

### Hauptkomponenten

**View Layer** (`view/`):
- `MainWindow`: Hauptfenster mit Modus-Verwaltung (QStackedWidget)
- `VisitorModeWidget`: Fullscreen-UI fuer Besucher mit Overlay-Widgets
- `AdminModeWidget`: Preset-Editor mit Live-Vorschau (Package `admin_mode/`)
- `CameraThread`: QThread fuer asynchrone Frame-Verarbeitung (~30 FPS)
- Widgets (`widgets/`): LayerButtonBar, InfoPanel, AboutWidget, OutputRankingWidget, GradCAMWidget, CameraDisplayWidget, ArchLayerButton
- Styling (`styles/`): Zentrales Farb- und Dimensions-System, QSS-Templates

**Core Layer** (`core/`):
- `ApplicationFacade`: Einziger Einstiegspunkt fuer den View Layer
- `CameraService`: Webcam-Zugriff via OpenCV
- `ModelService`: ResNet18-Inferenz, Layer-Extraktion, GradCAM
- `VisualizationService`: Feature Maps zu darstellbaren RGB-Bildern
- `PresetService`: Preset-CRUD und Zustandsverwaltung
- Interfaces (`interfaces/`): Protocols fuer alle Services (strukturelles Subtyping)
- Datenmodelle (`models.py`): PresetConfig, LayerPresets, ConfigData

**Storage Layer** (`storage/`):
- `ConfigManager`: JSON-Persistierung mit atomaren Schreiboperationen
- `DefaultConfig`: Standard-Presets fuer alle ResNet18-Layer
- `IConfigStorage`: Protocol-Interface fuer den Core Layer

Detaillierte Dokumentation: siehe [Dokumentation](#dokumentation).

---

## Tests

### Unit-Tests ausfuehren

```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage-Report
pytest tests/ --cov=core --cov=storage --cov=view --cov-report=html

# Spezifische Tests
pytest tests/test_facade.py -v
pytest tests/test_camera_service.py -v
```

### Integration-Tests

```bash
# End-to-End Workflows
pytest tests/test_integration.py -v

# Performance-Benchmarks
pytest tests/test_integration.py::TestPerformance -v
```

### Test-Coverage

Die Test-Coverage liegt bei **>85%** fuer Core- und Storage-Layer.

---

## Konfiguration

### config.json Struktur

```json
{
  "version": "1.0",
  "presets": {
    "conv1": {
      "layer_name": "conv1",
      "active_preset_id": 0,
      "presets": [
        {
          "preset_id": 0,
          "name": "Edge Detection",
          "channels": [0, 1, 2],
          "colormap": "viridis",
          "normalize": true,
          "blend_mode": "max",
          "visualization_mode": "colormap"
        }
      ]
    },
    "layer1": { "..." : "..." },
    "layer2": { "..." : "..." },
    "layer3": { "..." : "..." },
    "layer4": { "..." : "..." }
  }
}
```

### Preset-Parameter

| Parameter            | Werte                                        | Beschreibung                                          |
|----------------------|----------------------------------------------|-------------------------------------------------------|
| `visualization_mode` | `"colormap"`, `"rgb"`                        | Visualisierungsmodus                                  |
| `channels`           | Liste von int, `-1` = nicht belegt           | Channel-Indizes (1-3 Channels)                        |
| `colormap`           | `"viridis"`, `"plasma"`, `"inferno"`, `"magma"`, `"jet"`, `"hot"` | Farbskala (nur Colormap-Modus) |
| `blend_mode`         | `"max"`, `"mean"`, `"overlay"`               | Blending-Methode (nur Colormap-Modus)                 |
| `normalize`          | `true`, `false`                              | Min-Max-Normalisierung                                |

### Styling

Das visuelle Erscheinungsbild wird zentral ueber das `view/styles/`-Package gesteuert:

- **Farben**: `colors.py` -- Cyberpunk-Farbpalette (Stufe 1: app-weit, Stufe 2: komponentenspezifisch)
- **Dimensionen**: `dimensions.py` -- Groessen, Abstaende, Schriftarten als frozen Dataclasses
- **QSS-Templates**: `base.qss` -- Qt-Stylesheets mit Platzhaltern fuer den Admin-Modus

Details: siehe `view/styles/styling_guide.md`.

---

## Entwicklung

### Projektstruktur

```
museum-cnn-visualization/
|
|-- core/                           # Core Layer (Business Logic)
|   |-- interfaces/                 # Service Interfaces (Protocols)
|   |   |-- i_camera_service.py
|   |   |-- i_model_service.py
|   |   |-- i_visualization_service.py
|   |   +-- i_preset_service.py
|   |-- services/                   # Service Implementations
|   |   |-- camera_service.py
|   |   |-- model_service.py
|   |   |-- visualization_service.py
|   |   +-- preset_service.py
|   |-- facade.py                   # Application Facade
|   |-- models.py                   # Data Models (Dataclasses)
|   |-- exceptions.py               # Custom Exceptions
|   +-- core-doc.md                 # Core Layer Dokumentation
|
|-- storage/                        # Storage Layer (Persistence)
|   |-- config_manager.py           # JSON Configuration Manager
|   |-- default_config.py           # Default Presets
|   |-- interfaces.py               # IConfigStorage Protocol
|   +-- storage-doc.md              # Storage Layer Dokumentation
|
|-- view/                           # View Layer (PyQt6 UI)
|   |-- admin_mode/                 # Admin-Modus (Preset-Editor)
|   |   |-- admin_mode_widget.py    # Haupt-Widget mit Editor + Vorschau
|   |   |-- channel_manager.py      # Channel-Verwaltung + ChannelSpinBox
|   |   |-- preset_builder.py       # PresetConfig-Factory
|   |   +-- admin-mode-doc.md       # Admin Mode Dokumentation
|   |-- widgets/                    # Wiederverwendbare UI-Komponenten
|   |   |-- helpers/                # Spezialisierte Widget-Varianten
|   |   |   +-- arch_layer_button.py
|   |   |-- base_overlay.py         # Basisklasse fuer Overlays
|   |   |-- camera_display.py       # Kamera-Display
|   |   |-- layer_button.py         # Layer-Button (Pulse-Animation)
|   |   |-- layer_button_bar.py     # Horizontale Button-Leiste
|   |   |-- info_panel.py           # Layer-Beschreibungen
|   |   |-- about_widget.py         # Info-Slideshow
|   |   |-- output_ranking_widget.py # Top-3-Predictions
|   |   |-- gradcam_widget.py       # GradCAM-Visualisierung
|   |   |-- legacy-widgets-doc.md   # Widget-Referenz
|   |   +-- widgets-dev-guide.md    # Widget-Entwicklungsanleitung
|   |-- media/                      # Statische Medien
|   |   |-- content/                # Bilinguale Texte (DE/EN)
|   |   |-- icon/                   # Icons (Info, Sprache, Cursor)
|   |   +-- img/                    # Bilder (Logos, Hintergruende)
|   |-- styles/                     # Zentrales Styling-System
|   |   |-- colors.py               # Farbdefinitionen
|   |   |-- dimensions.py           # Dimensionen als Dataclasses
|   |   |-- base.qss                # QSS-Template
|   |   |-- style_manager.py        # Platzhalter-Ersetzung
|   |   +-- styling_guide.md        # Styling-Anleitung
|   |-- utils/                      # Hilfsfunktionen
|   |   +-- frame_converter.py      # NumPy zu QPixmap
|   |-- main_window.py              # Hauptfenster
|   |-- visitor_mode.py             # Besuchermodus
|   |-- camera_thread.py            # Asynchrone Frame-Verarbeitung
|   |-- view-doc.md                 # View Layer Dokumentation
|   |-- view_dataflow.md            # Datenfluesse und Kommunikationswege
|   +-- README.md                   # View-Dokumentationsuebersicht
|
|-- tests/                          # Unit & Integration Tests
|   |-- test_*.py                   # Test-Module (9 Dateien)
|   |-- test_integration.py         # End-to-End Tests
|   +-- visual/                     # Visuelle Tests
|       +-- test_arch_buttons.py
|
|-- main.py                         # Application Entry Point
|-- requirements.txt                # Python Dependencies
|-- config.json                     # Runtime Configuration (auto-generated)
+-- README.md                       # Dieses Dokument
```

### Coding Guidelines

- **PEP 8**: Aller Code folgt dem PEP 8 Style Guide
- **Type Hints**: Vollstaendige Type Annotations
- **Docstrings**: Google-Style Docstrings
- **KISS**: Keep It Simple, Stupid
- **Single Responsibility**: Ein Service = Eine Verantwortlichkeit

### Erweiterung

Anleitungen zur Erweiterung der Anwendung finden sich in der jeweiligen Layer-Dokumentation:

- **Neuen Service hinzufuegen**: siehe `core/core-doc.md`, Abschnitt "Erweiterung"
- **Neues Widget erstellen**: siehe `view/widgets/widgets-dev-guide.md`
- **Neuen Visualisierungsmodus**: siehe `core/core-doc.md`, Abschnitt "Neuen Visualisierungs-Mode hinzufuegen"
- **Neues Preset-Feld**: siehe `storage/storage-doc.md`, Abschnitt "Erweiterung"
- **Styling anpassen**: siehe `view/styles/styling_guide.md`

---

## Dokumentation

Die Codebase enthaelt ausfuehrliche technische Dokumentation fuer jeden Layer:

### Storage Layer
| Dokument | Pfad | Inhalt |
|----------|------|--------|
| Storage Layer Doku | `storage/storage-doc.md` | ConfigManager, Serialisierung, atomare Schreiboperationen, Migrationslogik, JSON-Schema |

### Core Layer
| Dokument | Pfad | Inhalt |
|----------|------|--------|
| Core Layer Doku | `core/core-doc.md` | Datenmodelle, Interfaces, Services, Facade, Datenfluss, Seiteneffekte |

### View Layer
| Dokument | Pfad | Inhalt |
|----------|------|--------|
| Uebersicht | `view/README.md` | Einstiegspunkt mit Lesereihenfolge |
| View Layer Doku | `view/view-doc.md` | Gesamtarchitektur, Hauptkomponenten, Threading, Overlay-System, Mehrsprachigkeit |
| Datenfluesse | `view/view_dataflow.md` | Alle Benutzerinteraktionen und resultierende Datenfluesse durch alle drei Schichten |
| Admin Mode | `view/admin_mode/admin-mode-doc.md` | Preset-Editor: UI-Aufbau, Channel-Verwaltung, Live-Vorschau, Persistierung |
| Widget-Referenz | `view/widgets/legacy-widgets-doc.md` | Technische Referenz aller Widgets: Attribute, Signals, Rendering, Seiteneffekte |
| Widget-Entwicklung | `view/widgets/widgets-dev-guide.md` | Anleitung zum Erstellen neuer Widgets (3-Schritte-Ablauf) |
| Styling Guide | `view/styles/styling_guide.md` | Farben, Dimensionen, QSS-Templates, Konventionen |

### Empfohlene Lesereihenfolge

1. Diese README (Ueberblick)
2. `core/core-doc.md` (Geschaeftslogik und Datenmodelle)
3. `storage/storage-doc.md` (Persistierung)
4. `view/view-doc.md` (UI-Architektur)
5. `view/view_dataflow.md` (Interaktionen End-to-End)
6. Spezialdokumente je nach Bedarf

---

## Troubleshooting

### Kamera wird nicht erkannt

```bash
# Windows: Kamera-Berechtigungen in Einstellungen pruefen
# macOS: System Preferences, Security & Privacy, Camera

# Test: Kamera direkt oeffnen
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAILED')"
```

### PyTorch-Installation schlaegt fehl

```bash
# Windows (CPU-only):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Windows (CUDA 11.8):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# macOS:
pip install torch torchvision
```

### SSL-Fehler beim Modell-Download (macOS)

```
SSL: CERTIFICATE_VERIFY_FAILED
```

Python auf macOS bringt eigene SSL-Zertifikate mit, installiert diese aber nicht automatisch. Loesung:

```bash
# Im Python-Installationsordner das Zertifikats-Script ausfuehren:
/Applications/Python\ 3.x/Install\ Certificates.command
```

Alternativ:

```bash
pip install --upgrade certifi
```

### Langsame Performance

- **GPU nutzen**: CUDA-faehige GPU installieren
- **Aufloesung reduzieren**: Kamera-Aufloesung in `CameraService` anpassen
- **Frame-Skipping**: Nur jeden N-ten Frame verarbeiten

---