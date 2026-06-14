"""GradCAMSubtitleWidget fuer Visitor Mode.

Zeigt einen kurzen bilingualen Untertitel-Text unterhalb des GradCAM-Rahmens.
Nur sichtbar bei den letzten zwei CNN-Layern (synchron mit GradCAMWidget).
"""

import logging

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from view.media.content.gradcam_subtitle_content import GRADCAM_SUBTITLE_TEXT
from view.widgets.base_overlay import BaseOverlayWidget

logger = logging.getLogger(__name__)


class GradCAMSubtitleWidget(BaseOverlayWidget):
    """Widget fuer bilingualen Untertitel-Text bei GradCAM-Layern.

    Zeigt einen einzeiligen Text in Magenta-Farbe. Visibility wird
    ueber set_current_layer() gesteuert (nur bei visible_layers sichtbar).
    Styling ueber QSS (Selektor: QLabel#gradcam-subtitle-text in base.qss).

    Attributes:
        _label: QLabel fuer Textanzeige
        _language: Aktuelle Sprache ("de" oder "en")
        _visible_layers: Layer-Namen bei denen das Widget sichtbar ist
    """

    def __init__(
        self, visible_layers: list[str], parent: QWidget | None = None
    ):
        """Initialisiert GradCAMSubtitleWidget.

        Args:
            visible_layers: Layer-Namen bei denen das Widget sichtbar ist
            parent: Parent-Widget (VisitorModeWidget)
        """
        super().__init__(parent)

        self._visible_layers = visible_layers
        self._language: str = "de"

        self.setVisible(False)

        self._label = QLabel(self)
        self._label.setObjectName("gradcam-subtitle-text")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        # Mouse-Events durchlassen (dekoratives Widget)
        self.set_transparent_for_mouse(True)

        self._update_text()

        logger.debug(
            "GradCAMSubtitleWidget initialisiert (sichtbar bei: %s)",
            self._visible_layers,
        )

    def set_current_layer(self, layer_name: str) -> None:
        """Steuert Visibility basierend auf Layer-Name.

        Args:
            layer_name: Aktuell aktiver Layer-Name
        """
        should_show = layer_name in self._visible_layers
        self.setVisible(should_show)
        logger.debug(
            "GradCAM-Subtitle Visibility: %s (Layer: %s)",
            should_show,
            layer_name,
        )

    def update_language(self, language: str) -> None:
        """Aktualisiert den angezeigten Text fuer die neue Sprache.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        self._language = language
        self._update_text()
        logger.debug("GradCAMSubtitleWidget Sprache aktualisiert: %s", language)

    def _update_text(self) -> None:
        """Setzt den Label-Text basierend auf aktueller Sprache."""
        self._label.setText(
            GRADCAM_SUBTITLE_TEXT.get(self._language, GRADCAM_SUBTITLE_TEXT["de"])
        )
