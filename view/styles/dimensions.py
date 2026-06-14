"""Zentrale Dimensionen für UI-Komponenten.

Verwendet Dataclasses für gruppierte Dimensionen.
Ersetzt das entfernte ui_layout System mit konkreten, verwendeten Werten.
"""

from dataclasses import dataclass

# ============================================================================
# Button-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class ButtonDimensions:
    """Dimensionen für Standard-Buttons."""
    min_width: int = 150
    min_height: int = 80
    border_radius: int = 10
    padding: int = 10
    border_width: int = 2

# Singleton-Instanz
BUTTON_DIMS = ButtonDimensions()

# ============================================================================
# Display-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class DisplayDimensions:
    """Dimensionen für Kamera-Displays."""
    # Visitor Mode Fullscreen
    visitor_min_width: int = 800
    visitor_min_height: int = 600

    # Admin Mode Preview
    admin_preview_width: int = 640
    admin_preview_height: int = 480

# Singleton-Instanz
DISPLAY_DIMS = DisplayDimensions()

# ============================================================================
# Overlay-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class OverlayDimensions:
    """Dimensionen fuer Overlay-Widgets (Button-Bar)."""
    # Button-Bar
    button_bar_height: int = 120
    button_bar_margin: int = 100
    button_spacing: int = 15
    button_bar_margin_inner: int = 10  # ContentsMargins der LayerButtonBar
    output_ranking_gap: int = 10 # Abstand vom Outputranking zur ButtonBar
    icon_button_padding: int = 12

# Singleton-Instanz
OVERLAY_DIMS = OverlayDimensions()

# ============================================================================
# Info-Panel-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class InfoPanelDimensions:
    """Dimensionen fuer das Info-Panel im Visitor Mode."""
    width: int = 300
    height: int = 340
    margin_right: int = 100
    margin_top: int = 200
    border_radius: int = 8         # Cyberpunk-Abrundung
    border_width: float = 1.5      # Glow-Rand-Breite
    layout_padding: int = 6        # Innenabstand damit paintEvent-Rand sichtbar bleibt

# Singleton-Instanz
INFO_PANEL_DIMS = InfoPanelDimensions()

# ============================================================================
# About-Widget-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class AboutWidgetDimensions:
    """Dimensionen fuer das About-Widget im Visitor Mode."""
    # Icon-Button
    icon_size: int = 55

    # Content-Bereich
    content_width: int = 300
    content_height: int = 425

    # Positionierung (Abstand vom Rand)
    margin_right: int = 40
    margin_top: int = 30

    # Cyberpunk-Styling
    border_radius: int = 8         # Abrundung des Content-Containers
    border_width: float = 1.5      # Glow-Rand-Breite

# Singleton-Instanz
ABOUT_DIMS = AboutWidgetDimensions()

# ============================================================================
# Output-Ranking-Widget-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class OutputRankingDimensions:
    """Dimensionen fuer das Output-Ranking-Widget im Visitor Mode."""
    # Gesamtgroesse
    width: int = 250
    height: int = 120

    # Balken
    bar_height: int = 16
    bar_max_width: int = 80

    # Abstaende
    padding: int = 10
    border_radius: int = 8

# Singleton-Instanz
OUTPUT_RANKING_DIMS = OutputRankingDimensions()

# ============================================================================
# GradCAM-Widget-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class GradCAMDimensions:
    """Dimensionen fuer das GradCAM-Widget im Visitor Mode."""
    # Gesamtgroesse (quadratisch fuer Kreis-Hintergrund)
    # Groesser als Kamerabild, damit Glow-Kreis sichtbar bleibt
    width: int = 360
    height: int = 360

    # Innen-Abstand (Glow-Rand um das Kamerabild)
    padding: int = 50
    border_radius: int = 8

    # Positionierung
    margin_left: int = 100

# Singleton-Instanz
GRADCAM_DIMS = GradCAMDimensions()

# ============================================================================
# Icon-Bar-Dimensionen (About + Language Icons)
# ============================================================================

@dataclass(frozen=True)
class IconBarDimensions:
    """Dimensionen fuer die Icon-Bar (About + Language) im Visitor Mode."""
    # Hintergrundbild-Groesse
    width: int = 155
    height: int = 58

    # Positionierung (Abstand vom Rand)
    margin_right: int = 100
    margin_top: int = 50

    # Innenabstand (Icons zum Rand des Hintergrunds)
    padding: int = 10

    # Chamfer-Tiefe fuer oktagone Form (QPainterPath)
    chamfer: int = 10

    # Flaggen-/Sprach-Icon-Groesse (entkoppelt vom About-Icon)
    flag_icon_size: int = 55

# Singleton-Instanz
ICON_BAR_DIMS = IconBarDimensions()

# ============================================================================
# Title-Text-Widget-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class TitleTextDimensions:
    """Dimensionen fuer das Title-Text-Widget im Visitor Mode."""
    font_size: int = 25
    margin_top: int = 10       # Abstand vom oberen Rand

# Singleton-Instanz
TITLE_TEXT_DIMS = TitleTextDimensions()

# ============================================================================
# GradCAM-Subtitle-Text-Widget-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class GradCAMSubtitleDimensions:
    """Dimensionen fuer das GradCAM-Subtitle-Widget im Visitor Mode."""
    font_size: int = 20
    gap_to_gradcam: int = 10  # Vertikaler Abstand unterhalb des GradCAM-Widgets

# Singleton-Instanz
GRADCAM_SUBTITLE_DIMS = GradCAMSubtitleDimensions()

# ============================================================================
# ArchLayerButton-Dimensionen
# ============================================================================

@dataclass(frozen=True)
class ArchLayerButtonDimensions:
    """Zeichen-Konstanten für ArchLayerButton (QPainter-Rendering)."""
    node_radius: int = 4
    node_x: int = 22
    node_spacing_preferred: int = 12
    margin_vertical: int = 10
    scan_line_step: int = 4
    border_radius: int = 8
    label_font_size: int = 10
    label_font_family: str = "Consolas"

# Singleton-Instanz
ARCH_LAYER_BTN_DIMS = ArchLayerButtonDimensions()

# ============================================================================
# Cursor-Dimensionen (Visitor Mode)
# ============================================================================

@dataclass(frozen=True)
class CursorDimensions:
    """Dimensionen fuer den Custom-Cursor im Visitor Mode."""
    size: int = 32  # Breite und Hoehe in Pixel (quadratisch)

# Singleton-Instanz
CURSOR_DIMS = CursorDimensions()

# ============================================================================
# Font-Größen
# ============================================================================

@dataclass(frozen=True)
class FontSizes:
    """Font-Größen für verschiedene UI-Elemente."""
    small: int = 12
    medium: int = 14
    large: int = 18
    xlarge: int = 24
    font_family: str = "Consolas"  # Standard-Button-Font (layer_button.py)

# Singleton-Instanz
FONT_SIZES = FontSizes()

# ============================================================================
# Export für from view.styles.dimensions import *
# ============================================================================

__all__ = [
    'ButtonDimensions',
    'DisplayDimensions',
    'OverlayDimensions',
    'InfoPanelDimensions',
    'AboutWidgetDimensions',
    'OutputRankingDimensions',
    'GradCAMDimensions',
    'FontSizes',
    'IconBarDimensions',
    'ArchLayerButtonDimensions',
    'CursorDimensions',
    'BUTTON_DIMS',
    'DISPLAY_DIMS',
    'OVERLAY_DIMS',
    'INFO_PANEL_DIMS',
    'ABOUT_DIMS',
    'OUTPUT_RANKING_DIMS',
    'GRADCAM_DIMS',
    'ICON_BAR_DIMS',
    'TitleTextDimensions',
    'TITLE_TEXT_DIMS',
    'GradCAMSubtitleDimensions',
    'GRADCAM_SUBTITLE_DIMS',
    'FONT_SIZES',
    'ARCH_LAYER_BTN_DIMS',
    'CURSOR_DIMS',
]
