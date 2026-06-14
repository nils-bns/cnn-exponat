"""Spezialisierte Widgets für die View Layer.

Exports:
    LayerButton: Touch-optimierter Button für Layer-Auswahl
    BaseOverlayWidget: Basis für transparente Overlay-Widgets
    CameraDisplayWidget: Kamera-Display mit automatischer Frame-Konvertierung
    LayerButtonBar: Horizontale Button-Leiste für Layer-Auswahl
    InfoPanel: Info-Panel für Layer-Beschreibungen
    AboutWidget: About-Widget mit Icon-Toggle und scrollbarem Content
    OutputRankingWidget: Top-3-Klassifikationsergebnisse als Balkendiagramm
    IconBarBgWidget: Dekorativer Glas-Hintergrund für die Icon-Bar
"""

from view.widgets.layer_button import LayerButton
from view.widgets.base_overlay import BaseOverlayWidget
from view.widgets.camera_display import CameraDisplayWidget
from view.widgets.layer_button_bar import LayerButtonBar
from view.widgets.info_panel import InfoPanel
from view.widgets.about_widget import AboutWidget
from view.widgets.output_ranking_widget import OutputRankingWidget
from view.widgets.gradcam_widget import GradCAMWidget
from view.widgets.icon_bar_bg_widget import IconBarBgWidget
from view.widgets.title_text_widget import TitleTextWidget
from view.widgets.gradcam_subtitle_widget import GradCAMSubtitleWidget

__all__ = [
    "LayerButton",
    "BaseOverlayWidget",
    "CameraDisplayWidget",
    "LayerButtonBar",
    "InfoPanel",
    "AboutWidget",
    "OutputRankingWidget",
    "GradCAMWidget",
    "IconBarBgWidget",
    "TitleTextWidget",
    "GradCAMSubtitleWidget",
]

