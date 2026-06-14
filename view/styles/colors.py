"""Zentrale Farbdefinitionen für die Anwendung.

Alle Farben als Hex-Strings definiert.
Verwendung: Direkt in Python oder über StyleManager in QSS.
"""

# ============================================================================
# Primärfarben (Buttons, Hauptinteraktion)
# ============================================================================

PRIMARY = "#2196F3"  # Material Blue
PRIMARY_HOVER = "#1976D2"  # Dunkleres Blau
PRIMARY_PRESSED = "#0D47A1"  # Noch dunkler
PRIMARY_BORDER = "#1976D2"

# ============================================================================
# Akzentfarben (Aktive States, Highlights)
# ============================================================================

ACTIVE = "#FF9800"  # Material Orange
ACTIVE_HOVER = "#FB8C00"
ACTIVE_BORDER = "#F57C00"

# ============================================================================
# Erfolg / Fehler / Warnung
# ============================================================================

SUCCESS = "#4CAF50"  # Grün
SUCCESS_HOVER = "#45A049"

DANGER = "#d9534f"  # Rot
DANGER_HOVER = "#c9302c"

WARNING = "#FFC107"  # Gelb
WARNING_HOVER = "#FFB300"

# ============================================================================
# Hintergründe
# ============================================================================

BACKGROUND_DARK = "#000000"  # Schwarz (Visualisierungen)
BACKGROUND_LIGHT = "#f5f5f5"  # Helles Grau (Formulare)
BACKGROUND_MEDIUM = "#333333"  # Mittleres Grau

# ============================================================================
# Borders & Dividers
# ============================================================================

BORDER_DEFAULT = "#555555"  # Mittleres Grau
BORDER_LIGHT = "#cccccc"  # Helles Grau
BORDER_DARK = "#333333"  # Dunkles Grau

# ============================================================================
# Text
# ============================================================================

TEXT_PRIMARY = "#ffffff"  # Weiß
TEXT_SECONDARY = "#aaaaaa"  # Helles Grau
TEXT_DARK = "#000000"  # Schwarz (auf hellem Hintergrund)

# ============================================================================
# Cyberpunk Theme – App-weite Primärfarben (Stufe 1)
# Werden von allen Widgets geteilt: InfoPanel, ArchLayerButton, OutputRanking, Cursor
# ============================================================================

CYBERPUNK_CYAN   = "#00f0ff"   # Primärer Akzent – Neon Cyan
CYBERPUNK_BG_TOP = "#0a0e1a"   # Dunkler Hintergrund (Gradient-Start)
CYBERPUNK_BG_BOT = "#050810"   # Dunklerer Hintergrund (Gradient-Ende)

# ============================================================================
# ArchLayerButton – Komponenten-spezifische Farben (Stufe 2)
# Nur ArchLayerButton; Änderung berührt keine anderen Widgets
# ============================================================================

ARCH_LAYER_CYAN_BRIGHT    = "#33ffff"   # Hover-Akzent (heller als CYBERPUNK_CYAN)
ARCH_LAYER_MAGENTA        = "#ff00aa"   # Checked/selected state
ARCH_LAYER_BG_HOVER_TOP   = "#0f1a2e"
ARCH_LAYER_BG_HOVER_BOT   = "#060d1a"
ARCH_LAYER_BG_CHECKED_TOP = "#1a0a2e"
ARCH_LAYER_BG_CHECKED_BOT = "#0d0520"

# ============================================================================
# OutputRankingWidget – Komponenten-spezifische Farben (Stufe 2)
# RGB-Tupel (int, int, int) für Farbinterpolation in _get_bar_color()
# Hinweis: OUTPUT_RANKING_BAR_BRIGHT entspricht CYBERPUNK_CYAN als RGB-Tupel
# ============================================================================

OUTPUT_RANKING_BAR_DARK   = (0, 150, 180)   # Balken-Gradient dunkel (gedämpftes Cyan)
OUTPUT_RANKING_BAR_BRIGHT = (0, 240, 255)   # Balken-Gradient hell (= CYBERPUNK_CYAN als RGB)

# ============================================================================
# Cyberpunk Overlay-Stil (InfoPanel, AboutWidget)
# OVERLAY_BG_TOP/BOT/BORDER_COLOR entfernt → direkt CYBERPUNK_* verwenden
# ============================================================================

OVERLAY_BORDER_ALPHA = 80                           # Rand-Alpha (0-255, ≈31% Deckkraft)
OVERLAY_BG_OPACITY = 128                            # Basis-Deckkraft (0-255) – gemeinsamer Fallback
INFO_PANEL_BG_OPACITY = OVERLAY_BG_OPACITY          # Fine-tuning InfoPanel
ABOUT_BG_OPACITY = OVERLAY_BG_OPACITY               # Fine-tuning AboutWidget
def _hex_to_rgba(hex_color: str, alpha: int) -> str:
    r, g, b = (int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"

OVERLAY_BORDER_GLOW_RGBA = _hex_to_rgba(CYBERPUNK_CYAN, OVERLAY_BORDER_ALPHA)    # Rand für QSS
OVERLAY_BG_RGBA = _hex_to_rgba(CYBERPUNK_BG_TOP, ABOUT_BG_OPACITY)               # Hintergrund AboutWidget für QSS

# AboutWidget – weißes Styling (Stufe 2)
ABOUT_BG_WHITE_RGBA = "rgba(255, 255, 255, 180)"    # Weißer, halbtransparenter Hintergrund
ABOUT_TEXT_COLOR = TEXT_DARK                         # Dunkler Text auf weißem Hintergrund

# IconBarBgWidget – Glass-Fill (Stufe 2)
ICON_BAR_GLASS_ALPHA = 90                            # White glass fill alpha (≈35% Deckkraft)

# ============================================================================
# Export für from view.styles.colors import *
# ============================================================================

__all__ = [
    'PRIMARY', 'PRIMARY_HOVER', 'PRIMARY_PRESSED', 'PRIMARY_BORDER',
    'ACTIVE', 'ACTIVE_HOVER', 'ACTIVE_BORDER',
    'SUCCESS', 'SUCCESS_HOVER',
    'DANGER', 'DANGER_HOVER',
    'WARNING', 'WARNING_HOVER',
    'BACKGROUND_DARK', 'BACKGROUND_LIGHT', 'BACKGROUND_MEDIUM',
    'BORDER_DEFAULT', 'BORDER_LIGHT', 'BORDER_DARK',
    'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_DARK',
    # Cyberpunk Theme – Stufe 1
    'CYBERPUNK_CYAN', 'CYBERPUNK_BG_TOP', 'CYBERPUNK_BG_BOT',
    # ArchLayerButton – Stufe 2
    'ARCH_LAYER_CYAN_BRIGHT', 'ARCH_LAYER_MAGENTA',
    'ARCH_LAYER_BG_HOVER_TOP', 'ARCH_LAYER_BG_HOVER_BOT',
    'ARCH_LAYER_BG_CHECKED_TOP', 'ARCH_LAYER_BG_CHECKED_BOT',
    # OutputRankingWidget – Stufe 2
    'OUTPUT_RANKING_BAR_DARK', 'OUTPUT_RANKING_BAR_BRIGHT',
    # Overlay-Stil (spezifische Werte – OVERLAY_BG_TOP/BOT/BORDER_COLOR entfernt)
    'OVERLAY_BORDER_ALPHA', 'OVERLAY_BG_OPACITY',
    'INFO_PANEL_BG_OPACITY', 'ABOUT_BG_OPACITY',
    'OVERLAY_BORDER_GLOW_RGBA', 'OVERLAY_BG_RGBA',
    # AboutWidget – weißes Styling (Stufe 2)
    'ABOUT_BG_WHITE_RGBA', 'ABOUT_TEXT_COLOR',
    # IconBarBgWidget – Glass-Fill (Stufe 2)
    'ICON_BAR_GLASS_ALPHA',
]
