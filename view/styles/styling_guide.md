# Styling Guide

Anleitung zur visuellen Anpassung der CNN-Visualisierungs-App.

---

## Kurzübersicht: Wo ändere ich was?

| Ich will ändern... | Datei | Abschnitt |
|--------------------|-------|-----------|
| Cyberpunk-Grundfarbe (Cyan, Hintergrund) | `colors.py` | `CYBERPUNK_*` |
| Layer-Button Farben (Hover, Checked) | `colors.py` | `ARCH_LAYER_*` |
| Balken-Farben im Ranking-Widget | `colors.py` | `OUTPUT_RANKING_BAR_*` |
| Admin-Mode Button-Farben | `colors.py` | `PRIMARY`, `SUCCESS`, `DANGER` etc. |
| Layer-Button Größe / Knotenabstand | `dimensions.py` | `ArchLayerButtonDimensions` |
| Button-Bar Abstände | `dimensions.py` | `OverlayDimensions` |
| Info-Panel / About-Widget Größe | `dimensions.py` | `InfoPanelDimensions` / `AboutWidgetDimensions` |
| Schriftgröße & Schriftart | `dimensions.py` | `FontSizes` |
| Admin-Mode QSS-Styling | `base.qss` | Selektoren mit `{platzhalter}` |

---

## Wichtig: Zwei Rendering-Systeme

Die App hat zwei verschiedene Wege, wie Widgets gezeichnet werden:

**QSS** (Admin Mode, Standard-Qt-Widgets):
Stylesheets wie CSS. Farben werden als Hex-String aus `colors.py` über Platzhalter eingesetzt.

**QPainter** (Visitor Mode, Custom Widgets):
Widgets wie `ArchLayerButton`, `InfoPanel`, `OutputRankingWidget` zeichnen sich selbst per Code.
Hier wirken QSS-Änderungen **nicht** – nur Änderungen in `colors.py` und `dimensions.py` direkt.

---

## 1. Cyberpunk-Farben ändern (Visitor Mode)

`view/styles/colors.py`

### Farb-Hierarchie

```
Stufe 1 – App-weite Grundfarben (CYBERPUNK_*)
│  Alle Cyberpunk-Widgets teilen diese Farben.
│  Hier ändern = überall gleichzeitig geändert.
│
├── CYBERPUNK_CYAN   = "#00f0ff"   → Neon-Cyan (Ränder, Knoten, Cursor)
├── CYBERPUNK_BG_TOP = "#0a0e1a"   → Hintergrund-Gradient oben
└── CYBERPUNK_BG_BOT = "#050810"   → Hintergrund-Gradient unten

Stufe 2 – Komponenten-spezifische Farben
│  Nur ein Widget betroffen. Isolierte Änderung möglich.
│
├── ARCH_LAYER_*        → Nur ArchLayerButton (Layer-Buttons im Visitor Mode)
└── OUTPUT_RANKING_*    → Nur OutputRankingWidget (Konfidenz-Balken)
```

### Cyberpunk-Akzentfarbe ändern (z.B. Grün statt Cyan)

```python
# colors.py – Stufe 1 ändern → wirkt auf InfoPanel, Layer-Buttons, Cursor gleichzeitig
CYBERPUNK_CYAN   = "#00ff88"   # Neon-Grün statt Cyan

# Stufe 2 muss separat angepasst werden (erbt nicht automatisch):
ARCH_LAYER_CYAN_BRIGHT    = "#33ffaa"   # Helleres Grün für Hover
OVERLAY_BORDER_GLOW_RGBA  = "rgba(0, 255, 136, 80)"  # QSS-Randfarbe anpassen
```

### Layer-Button Farben ändern

```python
# colors.py – Stufe 2 (nur ArchLayerButton)
ARCH_LAYER_CYAN_BRIGHT    = "#33ffff"   # Hover-State (heller als Cyan)
ARCH_LAYER_MAGENTA        = "#ff00aa"   # Checked/Aktiv-State
ARCH_LAYER_BG_HOVER_TOP   = "#0f1a2e"  # Hintergrund bei Hover (oben)
ARCH_LAYER_BG_HOVER_BOT   = "#060d1a"  # Hintergrund bei Hover (unten)
ARCH_LAYER_BG_CHECKED_TOP = "#1a0a2e"  # Hintergrund wenn aktiv (oben)
ARCH_LAYER_BG_CHECKED_BOT = "#0d0520"  # Hintergrund wenn aktiv (unten)
```

### Konfidenz-Balken Farben ändern

```python
# colors.py – Stufe 2 (nur OutputRankingWidget)
# RGB-Tupel, werden interpoliert (niedrige → hohe Konfidenz)
OUTPUT_RANKING_BAR_DARK   = (0, 150, 180)   # Farbe bei ~0% Konfidenz
OUTPUT_RANKING_BAR_BRIGHT = (0, 240, 255)   # Farbe bei ~100% Konfidenz
```

---

## 2. Admin-Mode Farben ändern

`view/styles/colors.py`

Diese Farben steuern die Standard-Qt-Buttons im Admin Mode über QSS:

```python
PRIMARY = "#2196F3"         # Haupt-Buttons (blau)
PRIMARY_HOVER = "#1976D2"

SUCCESS = "#4CAF50"         # Speichern / Bestätigen (grün)
DANGER  = "#d9534f"         # Löschen / Abbrechen (rot)
WARNING = "#FFC107"         # Warnungen (gelb)
```

Änderungen hier werden automatisch in `base.qss` via Platzhalter `{primary}`, `{success}` etc. eingesetzt.

---

## 3. Abstände & Größen ändern

`view/styles/dimensions.py`

Alle Maße sind in Dataclasses gruppiert. Den Wert in der Dataclass ändern → sofort wirksam.

### Layer-Buttons (Visitor Mode)

```python
class ArchLayerButtonDimensions:
    node_radius: int = 4         # Radius der Knoten-Punkte (px)
    node_x: int = 22             # X-Position der Knotenspalte
    node_spacing_preferred: int = 12  # Abstand zwischen Knoten
    margin_vertical: int = 10    # Rand oben/unten für Knoten
    scan_line_step: int = 4      # Abstand der Scan-Lines (größer = weniger Linien)
    border_radius: int = 8       # Abrundung der Button-Ecken
    label_font_size: int = 10    # Schriftgröße des Layer-Labels
    label_font_family: str = "Consolas"  # Schriftart des Layer-Labels
```

### Button-Bar (Visitor Mode)

```python
class OverlayDimensions:
    button_bar_height: int = 120       # Höhe der Button-Leiste
    button_bar_margin: int = 100       # Abstand vom Rand des Fensters
    button_spacing: int = 15           # Abstand zwischen den Buttons
    button_bar_margin_inner: int = 10  # Innenabstand der Button-Bar
```

### Info-Panel

```python
class InfoPanelDimensions:
    width: int = 300          # Breite (px)
    height: int = 400         # Höhe (px)
    margin_right: int = 100   # Abstand vom rechten Rand
    margin_top: int = 200     # Abstand vom oberen Rand
    border_radius: int = 8    # Abrundung
    border_width: float = 1.5 # Breite des Cyan-Randes
```

### Schriftgrößen & Schriftart

```python
class FontSizes:
    small: int = 12
    medium: int = 14
    large: int = 18           # Schriftgröße der Layer-Buttons
    xlarge: int = 24
    font_family: str = "Consolas"  # Schriftart aller Visitor-Mode Widgets
```

---

## 4. QSS-Styling anpassen (Admin Mode)

`view/styles/base.qss`

Wird beim App-Start geladen. Verwendet Platzhalter, die aus `colors.py` und `dimensions.py` befüllt werden.

```css
/* Platzhalter werden automatisch ersetzt – z.B. {primary} → "#2196F3" */
QPushButton#action-button-primary {
    background-color: {primary};
    border-radius: {button_border_radius}px;
}
```

Selektoren nutzen Qt6 ID-Syntax:
```css
/* ✅ Richtig: */
QPushButton#layer-button { ... }

/* ❌ Falsch (CSS-Klassen funktionieren nicht): */
.layer-button { ... }
```

### Bestehende Platzhalter

| Platzhalter | Quelle | Beschreibung |
|-------------|--------|-------------|
| `{primary}`, `{success}`, `{danger}` etc. | `colors.py` | Farben |
| `{font_small}`, `{font_medium}`, `{font_large}`, `{font_xlarge}` | `dimensions.py` → `FontSizes` | Schriftgroessen |
| `{font_family}` | `dimensions.py` → `FontSizes.font_family` | Schriftart (alle Visitor-Mode Selektoren) |

### Neuen Platzhalter in QSS verwenden

1. Farbe in `colors.py` oder Wert in `dimensions.py` definieren
2. In `style_manager.py` → `_replace_placeholders()` eintragen
3. In `base.qss` als `{name}` verwenden

---

## 5. Praktische Szenarien

### Szenario A: Cyan → Lila (App-weit)

```python
# colors.py
CYBERPUNK_CYAN            = "#cc00ff"   # Lila
ARCH_LAYER_CYAN_BRIGHT    = "#dd44ff"   # Helles Lila für Hover
OUTPUT_RANKING_BAR_BRIGHT = (204, 0, 255)   # Als RGB-Tupel
OVERLAY_BORDER_GLOW_RGBA  = "rgba(204, 0, 255, 80)"
OVERLAY_BG_RGBA           = f"rgba(10, 14, 26, {ABOUT_BG_OPACITY})"  # unverändert
```

### Szenario B: Layer-Buttons größer & weiter auseinander

```python
# dimensions.py
class OverlayDimensions:
    button_spacing: int = 25      # war 15
    button_bar_margin_inner: int = 15  # war 10
```

### Szenario C: Schriftart der Layer-Labels ändern

```python
# dimensions.py
class ArchLayerButtonDimensions:
    label_font_family: str = "Courier New"  # war "Consolas"
    label_font_size: int = 12               # war 10
```

---

## 6. Struktur-Übersicht

```
view/styles/
├── colors.py          # Alle Farben als Hex-Strings oder RGB-Tupel
│                        CYBERPUNK_* (Stufe 1) + ARCH_LAYER_* / OUTPUT_RANKING_* (Stufe 2)
├── dimensions.py      # Abstände, Größen, Schriften als Dataclasses
├── base.qss           # QSS-Template für Admin Mode (Platzhalter {name})
├── style_manager.py   # Lädt base.qss, setzt Platzhalter ein
└── styling_guide.md   # Diese Datei
```

---

## 7. Best Practices

✅ Cyberpunk-Farben nur in `colors.py` ändern – nie hardcoded in Widget-Dateien
✅ Für neue Widgets: erst prüfen ob `CYBERPUNK_*` passt, sonst neue `WIDGET_*`-Konstante anlegen
✅ QSS-Platzhalter verwenden statt Hex-Strings direkt in `base.qss`
✅ Dimensionen immer in der zugehörigen Dataclass ändern, nicht im Widget-Code
✅ QTextEdit-Widgets brauchen `document().setDefaultStyleSheet()` fuer font-family -- QSS allein reicht dort nicht

❌ Keine Farb-Hex-Strings direkt in Widget-Dateien (z.B. `QColor("#00f0ff")` ohne Import)
❌ Visitor-Mode Widgets reagieren nicht auf QSS – dort `colors.py`/`dimensions.py` ändern
❌ Dot-Notation in QSS-Selektoren (`.name`) funktioniert nicht mit Qt6 `setObjectName`
