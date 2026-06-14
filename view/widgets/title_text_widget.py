"""TitleTextWidget fuer Visitor Mode.

Zeigt einen kurzen bilingualen Titel-Text an (z.B. 'Wie sieht KI mich?').
Semi-transparentes Overlay-Widget, immer sichtbar im Visitor Mode.
"""

import logging

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from view.media.content.title_text_content import TITLE_TEXT
from view.widgets.base_overlay import BaseOverlayWidget

logger = logging.getLogger(__name__)


class TitleTextWidget(BaseOverlayWidget):
    """Widget fuer bilingualen Titel-Text im Visitor Mode.

    Zeigt einen einzeiligen Text in Magenta-Farbe, zentriert am
    oberen Bildschirmrand. Styling wird vollstaendig ueber QSS
    gesteuert (Selektor: QLabel#title-text in base.qss).

    Attributes:
        _label: QLabel fuer Textanzeige
        _language: Aktuelle Sprache ("de" oder "en")
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialisiert TitleTextWidget.

        Args:
            parent: Parent-Widget (VisitorModeWidget)
        """
        super().__init__(parent)

        self._language: str = "de"

        self._label = QLabel(self)
        self._label.setObjectName("title-text")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        # Mouse-Events durchlassen (dekoratives Widget)
        self.set_transparent_for_mouse(True)

        self._update_text()

        logger.debug("TitleTextWidget initialisiert")

    def update_language(self, language: str) -> None:
        """Aktualisiert den angezeigten Text fuer die neue Sprache.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        self._language = language
        self._update_text()
        logger.debug(f"TitleTextWidget Sprache aktualisiert: {language}")

    def _update_text(self) -> None:
        """Setzt den Label-Text basierend auf aktueller Sprache."""
        self._label.setText(TITLE_TEXT.get(self._language, TITLE_TEXT["de"]))
