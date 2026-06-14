"""Dekorativer Glas-Hintergrund für die Icon-Bar (About + Language)."""

import logging
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from view.styles.colors import CYBERPUNK_CYAN, ICON_BAR_GLASS_ALPHA, OVERLAY_BORDER_ALPHA
from view.styles.dimensions import ICON_BAR_DIMS

logger = logging.getLogger(__name__)


class IconBarBgWidget(QWidget):
    """Dekorativer Glas-Hintergrund für die Icon-Bar (About + Language).

    Zeichnet eine oktagone (chamfered) Form mit:
    - Weißem, halbtransparentem Fill (Glas-Effekt)
    - Cyan-Rand (konsistent mit anderen Overlays)

    Das Widget ist rein dekorativ – Mouse-Events werden durchgereicht.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialisiert IconBarBgWidget.

        Args:
            parent: Parent-Widget
        """
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        logger.debug("IconBarBgWidget initialisiert")

    def paintEvent(self, event) -> None:
        """Zeichnet die oktagone Form mit Glas-Fill und Cyan-Rand."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        chamfer = ICON_BAR_DIMS.chamfer
        w = self.width()
        h = self.height()

        path = QPainterPath()
        path.moveTo(chamfer, 0)
        path.lineTo(w - chamfer, 0)
        path.lineTo(w, chamfer)
        path.lineTo(w, h - chamfer)
        path.lineTo(w - chamfer, h)
        path.lineTo(chamfer, h)
        path.lineTo(0, h - chamfer)
        path.lineTo(0, chamfer)
        path.closeSubpath()

        painter.setBrush(QBrush(QColor(255, 255, 255, ICON_BAR_GLASS_ALPHA)))

        border_color = QColor(CYBERPUNK_CYAN)
        border_color.setAlpha(OVERLAY_BORDER_ALPHA)
        painter.setPen(QPen(border_color, 1.5))

        painter.drawPath(path)
