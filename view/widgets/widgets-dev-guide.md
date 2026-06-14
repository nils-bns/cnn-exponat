# Widgets - Entwicklungsanleitung

Anleitung zum Erstellen neuer Widgets fuer die CNN-Visualisierungs-Anwendung. Beschreibt den empfohlenen Ablauf und die Konventionen des `view/widgets/`-Packages.

---

## Inhaltsverzeichnis

1. [Ablauf](#ablauf)
2. [Schritt 1: Widget-Klasse erstellen](#schritt-1-widget-klasse-erstellen)
3. [Schritt 2: In Visitor Mode einbetten](#schritt-2-in-visitor-mode-einbetten)
4. [Schritt 3: Styling auslagern](#schritt-3-styling-auslagern)
5. [Bestehende Widgets als Referenz](#bestehende-widgets-als-referenz)
6. [Sonderfaelle](#sonderfaelle)

---

## Ablauf

Die Entwicklung eines neuen Widgets folgt drei Schritten:

1. **Widget-Klasse erstellen** -- Funktionalitaet implementieren, ObjectName setzen
2. **In Visitor Mode einbetten** -- Instanziieren, positionieren, Signals verbinden
3. **Styling auslagern** -- Dimensionen in `dimensions.py`, Farben in `colors.py`, QSS-Selektoren in `base.qss`

Diese Reihenfolge erlaubt es, das Widget zuerst funktional lauffaehig zu machen und erst danach das Styling sauber vom Code zu trennen. Inline-Styles waehrend der Entwicklung sind akzeptabel, sollten aber vor dem Abschluss in die zentrale Style-Infrastruktur ueberfuehrt werden.

---

## Schritt 1: Widget-Klasse erstellen

### Datei anlegen

Neue Widget-Dateien liegen in `view/widgets/`. Dateiname in snake_case, z.B. `my_widget.py`.

### Basisklasse waehlen

| Anwendungsfall                            | Basisklasse           |
|-------------------------------------------|-----------------------|
| Standard-Widget                           | `QWidget`             |
| Transparentes Overlay (Visitor Mode)      | `BaseOverlayWidget`   |
| Spezialisiertes Standard-Widget (z.B. QLabel) | Entsprechendes Qt-Widget |

`BaseOverlayWidget` setzt automatisch `WA_TranslucentBackground` und stellt Fade-Animationen bereit. Fuer Widgets, die ueber dem Kamera-Feed schweben sollen, ist es die richtige Wahl.

### Grundstruktur

```python
"""Kurzbeschreibung des Widgets.

Ausfuehrlichere Beschreibung, Zweck, Features.
"""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class MyWidget(QWidget):
    """Beschreibung des Widgets.

    Features:
    - Feature A
    - Feature B

    Usage:
        widget = MyWidget(parent)
        widget.update_data(data)
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._init_ui()
        logger.debug("MyWidget initialisiert")

    def _init_ui(self) -> None:
        """Initialisiert das UI-Layout."""
        layout = QVBoxLayout(self)
        # ... UI aufbauen ...

        # ObjectName fuer QSS-Styling setzen
        self.setObjectName("my-widget")
```

### Konventionen

- UI-Aufbau in `_init_ui()` auslagern
- Private Attribute mit Unterstrich-Praefix (`_label`, `_data`)
- `logger` auf Modulebene (`logging.getLogger(__name__)`)
- Type-Hints fuer alle Parameter und Rueckgabewerte
- Docstrings im Google-Stil (Args, Returns, Raises)

### Export registrieren

In `view/widgets/__init__.py` den Import und `__all__`-Export ergaenzen:

```python
from view.widgets.my_widget import MyWidget

__all__ = [
    # ... bestehende Exports ...
    "MyWidget",
]
```

---

## Schritt 2: In Visitor Mode einbetten

### Instanziierung

In `VisitorModeWidget._init_ui()` das Widget erstellen:

```python
# In _init_ui():
self._my_widget = MyWidget(self)
```

Das `self` als Parent sorgt dafuer, dass das Widget als Overlay ueber dem Kamera-Display positioniert werden kann.

### Positionierung

In `VisitorModeWidget._position_overlays()` die Position festlegen:

```python
# In _position_overlays():
if self._my_widget:
    x = ...  # Position berechnen
    y = ...
    self._my_widget.setGeometry(x, y, width, height)
    self._my_widget.raise_()  # Ueber andere Widgets heben
```

`_position_overlays()` wird bei jedem `resizeEvent` aufgerufen. Positionen muessen relativ zur Fenstergroesse berechnet werden (`self.width()`, `self.height()`).

`raise_()` bestimmt die Z-Reihenfolge. Interaktive Widgets muessen nach dem Frame-Overlay geraised werden.

### Signal-Verbindungen

Falls das Widget Daten vom CameraThread benoetigt, Signals in `VisitorModeWidget.start()` verbinden:

```python
# In start():
self._camera_thread.some_signal.connect(self._my_widget.update_slot)
```

### Sprachwechsel (falls bilingual)

1. `update_language(language)` Methode im Widget implementieren (bei BaseOverlayWidget-Subklassen ueberschreiben)
2. In `VisitorModeWidget._on_language_toggled()` die Widget-Liste erweitern:

```python
for widget in [
    self._button_bar, self._about_widget,
    self._output_ranking, self._gradcam_widget,
    self._my_widget,  # <-- neu
]:
    if widget:
        widget.update_language(self._language)
```

---

## Schritt 3: Styling auslagern

### Dimensionen definieren

In `view/styles/dimensions.py` eine frozen Dataclass erstellen:

```python
@dataclass(frozen=True)
class MyWidgetDimensions:
    """Dimensionen fuer MyWidget."""
    width: int = 200
    height: int = 150
    padding: int = 10
    border_radius: int = 8

MY_WIDGET_DIMS = MyWidgetDimensions()
```

In `__all__` der Datei ergaenzen. Dann im Widget importieren:

```python
from view.styles import MY_WIDGET_DIMS
```

### Farben verwenden

Farben aus `view/styles/colors.py` importieren. Keine lokalen Farbkonstanten definieren:

```python
from view.styles.colors import CYBERPUNK_CYAN, TEXT_PRIMARY
```

Falls eine Widget-spezifische Farbe noetig ist, in `colors.py` unter einem Stufe-2-Kommentar definieren (analog `ARCH_LAYER_*` oder `OUTPUT_RANKING_BAR_*`).

### QSS-Selektoren in base.qss

Fuer Widgets, die per QSS gestylt werden (nicht per QPainter):

1. `objectName` im Widget setzen: `self.setObjectName("my-widget")`
2. Selektor in `view/styles/base.qss` ergaenzen:

```css
QWidget#my-widget {
    background-color: {background_dark};
    color: {text_primary};
    border-radius: {my_widget_border_radius}px;
}
```

3. Falls Platzhalter benoetigt werden: In `StyleManager._replace_placeholders()` das Mapping ergaenzen.

### Custom Painting (QPainter)

Fuer Widgets mit aufwaendigem Rendering (Gradients, Glow-Effekte, Formen) wird `paintEvent()` ueberschrieben. In diesem Fall wird kein QSS fuer den Hintergrund verwendet. Farben kommen direkt aus `colors.py`, Dimensionen aus `dimensions.py`. Beispiele: `InfoPanel`, `OutputRankingWidget`, `ArchLayerButton`.

### Inline-Styles entfernen

Vor dem Abschluss pruefen:
- Keine `setStyleSheet()`-Aufrufe auf dem Widget selbst (Ausnahme: kleine Icon-Buttons mit nicht-trivialen Hover-States)
- Alle Farben aus `colors.py`
- Alle Dimensionen aus `dimensions.py`
- QSS-Selektoren ueber `objectName` statt ueber Klassen-Selektoren

---

## Bestehende Widgets als Referenz

| Widget                | Gut als Beispiel fuer                                     |
|-----------------------|-----------------------------------------------------------|
| `CameraDisplayWidget` | Einfachstes Widget. QLabel + Slot + ObjectName            |
| `InfoPanel`           | BaseOverlayWidget + Custom paintEvent + HTML-Content      |
| `OutputRankingWidget` | Dynamische Daten, Custom paintEvent, Visibility-Steuerung |
| `GradCAMWidget`       | Kreisfoermige Maskierung, Hintergrundbild, Layer-Visibility |
| `AboutWidget`         | Komplexes Widget: Slideshow, Swipe, eventFilter, Expand/Collapse |
| `LayerButton`         | Custom Property + Animation (Pulse)                       |
| `ArchLayerButton`     | Vollstaendiges QPainter-Rendering, Hover-Tracking         |

---

## Sonderfaelle

### Widget nur fuer bestimmte Layer sichtbar

Analog `GradCAMWidget`: `visible_layers` als Konstruktor-Parameter, `set_current_layer()` steuert Visibility.

### Widget mit eigenen Sub-Widgets

Fuer spezialisierte Varianten eines bestehenden Widgets ein Unterverzeichnis `helpers/` verwenden (analog `helpers/arch_layer_button.py`). In `helpers/__init__.py` exportieren.

### Widget fuer Admin Mode

Admin-Mode-Widgets gehoeren in `view/admin_mode/`, nicht in `view/widgets/`. Ausnahme: `CameraDisplayWidget` wird von beiden Modi verwendet und liegt daher in `widgets/`.

### Widget mit Facade-Zugriff

Widgets in `view/widgets/` erhalten keinen direkten Facade-Zugriff. Daten werden ueber Signals und Slots zugestellt (z.B. `CameraThread.frame_ready` --> `CameraDisplayWidget.update_frame`). Die Modi-Widgets (`VisitorModeWidget`, `AdminModeWidget`) halten die Facade-Referenz und orchestrieren den Datenfluss.
