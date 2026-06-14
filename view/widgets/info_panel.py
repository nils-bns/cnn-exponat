"""InfoPanel Widget für Visitor Mode.

Semi-transparentes Overlay-Panel zur Anzeige von Layer-Informationen.
"""

import logging
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen

from view.widgets.base_overlay import BaseOverlayWidget
from view.styles import (
    FONT_SIZES,
    INFO_PANEL_BG_OPACITY,
    INFO_PANEL_DIMS,
    OVERLAY_BORDER_ALPHA,
)
from view.styles.colors import (
    ARCH_LAYER_MAGENTA,
    CYBERPUNK_BG_BOT,
    CYBERPUNK_BG_TOP,
    CYBERPUNK_CYAN,
)

logger = logging.getLogger(__name__)


class InfoPanel(BaseOverlayWidget):
    """Info-Panel für Layer-Beschreibungen im Visitor Mode.

    Features:
    - Semi-transparenter Hintergrund (für Overlay-Effekt)
    - HTML-formatierte Textanzeige
    - Read-only QTextEdit

    Usage:
        panel = InfoPanel()
        panel.set_content("<h1>Layer 1</h1><p>Beschreibung...</p>")
        panel.clear()
    """

    def __init__(self, parent=None):
        """Initialisiert InfoPanel.

        Args:
            parent: Parent-Widget
        """
        super().__init__(parent)

        self._text_edit = QTextEdit(self)
        self._text_edit.setReadOnly(True)
        self._text_edit.setObjectName("info-panel")
        self._text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Visitor-Mode Schriftart + Header-Farbe (QTextEdit erbt
        # font-family nicht aus QSS, sondern braucht Document-Stylesheet)
        self._text_edit.document().setDefaultStyleSheet(
            f"body {{ font-family: {FONT_SIZES.font_family}; }} "
            f"h2 {{ color: {ARCH_LAYER_MAGENTA}; }}"
        )

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            INFO_PANEL_DIMS.layout_padding,
            INFO_PANEL_DIMS.layout_padding,
            INFO_PANEL_DIMS.layout_padding,
            INFO_PANEL_DIMS.layout_padding,
        )
        layout.addWidget(self._text_edit)

        # Initial leer
        self.clear()

        logger.debug("InfoPanel initialisiert")

    def set_content(self, html: str) -> None:
        """Setzt den Inhalt des Panels (HTML-formatiert).

        Args:
            html: HTML-formatierter Text (z.B. '<h1>Titel</h1><p>Text</p>')
        """
        self._text_edit.setHtml(html)
        logger.debug(f"InfoPanel Inhalt gesetzt: {len(html)} Zeichen")

    def clear(self) -> None:
        """Leert den Panel-Inhalt."""
        self._text_edit.clear()
        logger.debug("InfoPanel geleert")

    def set_plain_text(self, text: str) -> None:
        """Setzt den Inhalt als Plain-Text (ohne HTML).

        Args:
            text: Plain-Text
        """
        self._text_edit.setPlainText(text)
        logger.debug(f"InfoPanel Plain-Text gesetzt: {len(text)} Zeichen")

    def paintEvent(self, event) -> None:
        """Zeichnet Cyberpunk-Hintergrund mit Gradient und Glow-Border.

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = INFO_PANEL_DIMS.border_radius

        # Gradient-Hintergrund (dunkelblau, konsistent mit OutputRankingWidget)
        bg_grad = QLinearGradient(0, 0, 0, self.height())
        top_color = QColor(CYBERPUNK_BG_TOP)
        top_color.setAlpha(INFO_PANEL_BG_OPACITY)
        bot_color = QColor(CYBERPUNK_BG_BOT)
        bot_color.setAlpha(INFO_PANEL_BG_OPACITY)
        bg_grad.setColorAt(0, top_color)
        bg_grad.setColorAt(1, bot_color)
        painter.setBrush(QBrush(bg_grad))

        # Glow-Rand (Neon Cyan mit Alpha)
        border_color = QColor(CYBERPUNK_CYAN)
        border_color.setAlpha(OVERLAY_BORDER_ALPHA)
        painter.setPen(QPen(border_color, INFO_PANEL_DIMS.border_width))

        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, r, r)

        super().paintEvent(event)
