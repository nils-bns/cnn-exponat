"""LayerButton mit CNN-Architektur-Visualisierung.

Zeichnet Knoten und Verbindungslinien per QPainter
im Cyberpunk-Stil. Ersetzt das QSS-basierte Rendering
des Basis-LayerButtons komplett.
"""

import logging

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush,
    QLinearGradient, QRadialGradient,
)

from view.widgets.layer_button import LayerButton
from view.styles.colors import (
    CYBERPUNK_CYAN,
    CYBERPUNK_BG_TOP,
    CYBERPUNK_BG_BOT,
    ARCH_LAYER_CYAN_BRIGHT,
    ARCH_LAYER_MAGENTA,
    ARCH_LAYER_BG_HOVER_TOP,
    ARCH_LAYER_BG_HOVER_BOT,
    ARCH_LAYER_BG_CHECKED_TOP,
    ARCH_LAYER_BG_CHECKED_BOT,
)
from view.styles.dimensions import ARCH_LAYER_BTN_DIMS

logger = logging.getLogger(__name__)

# ============================================================================
# Cyberpunk-Farbpalette – importiert aus view.styles.colors
# ============================================================================

# QColor-Instanzen aus Hex-Strings
_CYAN        = QColor(CYBERPUNK_CYAN)
_CYAN_BRIGHT = QColor(ARCH_LAYER_CYAN_BRIGHT)
_MAGENTA     = QColor(ARCH_LAYER_MAGENTA)

_BG_DEFAULT_TOP  = QColor(CYBERPUNK_BG_TOP)
_BG_DEFAULT_BOT  = QColor(CYBERPUNK_BG_BOT)
_BG_HOVER_TOP    = QColor(ARCH_LAYER_BG_HOVER_TOP)
_BG_HOVER_BOT    = QColor(ARCH_LAYER_BG_HOVER_BOT)
_BG_CHECKED_TOP  = QColor(ARCH_LAYER_BG_CHECKED_TOP)
_BG_CHECKED_BOT  = QColor(ARCH_LAYER_BG_CHECKED_BOT)

# ============================================================================
# Zeichen-Konstanten – aus view.styles.dimensions
# ============================================================================

_D = ARCH_LAYER_BTN_DIMS  # Kürzel für lesbare Verwendung unten


class ArchLayerButton(LayerButton):
    """LayerButton mit CNN-Architektur-Visualisierung.

    Zeichnet die Knoten eines CNN-Layers als vertikale Spalte
    am linken Rand mit Verbindungslinien zum rechten Rand.
    Das komplette Rendering erfolgt per QPainter (kein QSS).

    Args:
        layer_name: Interner Layer-Name (z.B. "layer1.0")
        display_text: Anzuzeigender Text (z.B. "Conv1")
        num_nodes: Anzahl der Knoten fuer diesen Layer
        parent: Parent Widget
    """

    def __init__(
        self,
        layer_name: str,
        display_text: str,
        num_nodes: int,
        parent=None,
    ):
        super().__init__(layer_name, display_text, parent)
        self._num_nodes = num_nodes
        logger.debug(
            f"ArchLayerButton erstellt: {layer_name} ({num_nodes} Knoten)"
        )

    def paintEvent(self, event) -> None:
        """Zeichnet den Button mit CNN-Architektur-Visualisierung."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # --- State-abhaengige Farben ---
        if self.isChecked():
            bg_top, bg_bot = _BG_CHECKED_TOP, _BG_CHECKED_BOT
            accent = _MAGENTA
            border_base = _MAGENTA
        elif self._hovered:
            bg_top, bg_bot = _BG_HOVER_TOP, _BG_HOVER_BOT
            accent = _CYAN_BRIGHT
            border_base = _CYAN
        else:
            bg_top, bg_bot = _BG_DEFAULT_TOP, _BG_DEFAULT_BOT
            accent = _CYAN
            border_base = _CYAN

        # --- Hintergrund-Gradient ---
        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0, bg_top)
        bg_grad.setColorAt(1, bg_bot)
        p.setBrush(QBrush(bg_grad))

        border_col = QColor(border_base)
        border_col.setAlpha(180 if self.isChecked() or self._hovered else 80)
        p.setPen(QPen(border_col, 1.5))
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), _D.border_radius, _D.border_radius)

        # --- Scan-Lines ---
        p.setPen(QPen(QColor(255, 255, 255, 8), 1.0))
        for sy in range(0, h, _D.scan_line_step):
            p.drawLine(QPointF(2, sy), QPointF(w - 2, sy))

        # --- Knoten: vertikal gestapelt, Abstand passt sich an Buttonhoehe an ---
        usable_h = h - 2 * _D.margin_vertical
        max_column_h = (self._num_nodes - 1) * _D.node_spacing_preferred if self._num_nodes > 1 else 0
        node_spacing = min(_D.node_spacing_preferred, usable_h / max(1, self._num_nodes - 1))

        column_h = (self._num_nodes - 1) * node_spacing if self._num_nodes > 1 else 0
        start_y = (h - column_h) / 2

        nodes = []
        for i in range(self._num_nodes):
            y = start_y + i * node_spacing
            nodes.append(QPointF(_D.node_x, y))

        # --- Verbindungslinien: Knoten -> rechter Rand ---
        num_targets = max(3, self._num_nodes // 2)
        target_x = w - 5
        target_col_h = (num_targets - 1) * node_spacing if num_targets > 1 else 0
        targets_top = (h - target_col_h) / 2

        line_col = QColor(accent)
        line_col.setAlpha(35)
        p.setPen(QPen(line_col, 0.8))

        for node in nodes:
            for t in range(num_targets):
                target_y = targets_top + t * node_spacing
                p.drawLine(node, QPointF(target_x, target_y))

        # --- Glow hinter Knoten ---
        glow_radius = _D.node_radius * 4
        p.setPen(Qt.PenStyle.NoPen)
        for node in nodes:
            glow = QRadialGradient(node, glow_radius)
            glow_col = QColor(accent)
            glow_col.setAlpha(50)
            glow.setColorAt(0, glow_col)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.drawEllipse(node, glow_radius, glow_radius)

        # --- Knoten zeichnen ---
        node_outline = QColor(accent)
        node_outline.setAlpha(220)
        p.setPen(QPen(node_outline, 1.8))
        node_fill = QColor(accent)
        node_fill.setAlpha(60)
        p.setBrush(QBrush(node_fill))

        for node in nodes:
            p.drawEllipse(node, _D.node_radius, _D.node_radius)

        # --- Label rechts unten ---
        p.setPen(QPen(accent))
        font = QFont(_D.label_font_family, _D.label_font_size, QFont.Weight.Bold)
        p.setFont(font)
        text_rect = QRectF(_D.node_x + 15, h - 24, w - _D.node_x - 20, 20)
        p.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.text(),
        )

        p.end()

    # ------------------------------------------------------------------
    # Hover-Tracking (QPushButton hat kein eingebautes _hovered Flag)
    # ------------------------------------------------------------------

    _hovered: bool = False

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)
