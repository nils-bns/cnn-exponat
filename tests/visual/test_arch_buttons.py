"""Standalone-Test: CNN-Architektur-Buttons mit QPainter.

Startet ein eigenes Fenster mit Prototyp-Buttons.
Kein Import aus dem Projekt noetig — rein zum Testen der Optik.

Usage:
    python tests/visual/test_arch_buttons.py
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush,
    QLinearGradient, QRadialGradient,
)


# CNN-Layer-Definitionen: (Anzahl Knoten, Label)
LAYERS = [
    (12, "Conv1"),
    (8, "Conv2"),
    (6, "Conv3"),
    (4, "FC1"),
    (1, "Output"),
]

# Cyberpunk Farben
NEON_CYAN = QColor("#00f0ff")
NEON_MAGENTA = QColor("#ff00aa")
NEON_BLUE = QColor("#4488ff")
DARK_BG = QColor("#0a0e1a")
DARK_BG_HOVER = QColor("#111828")
CHECKED_BG = QColor("#1a0a2e")
BORDER_GLOW = QColor("#00f0ff")
BORDER_CHECKED = QColor("#ff00aa")


class ArchLayerButton(QWidget):
    """Prototyp-Button: CNN-Layer, Cyberpunk-Stil."""

    def __init__(self, num_nodes: int, label: str, btn_width: int = 150, parent=None):
        super().__init__(parent)
        self._num_nodes = num_nodes
        self._label = label
        self._hovered = False
        self._checked = False
        self._btn_width = btn_width

        self.setFixedSize(QSize(btn_width, 180))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def sizeHint(self):
        return QSize(self._btn_width, 180)

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # --- Hintergrund mit Gradient ---
        if self._checked:
            bg_top = QColor("#1a0a2e")
            bg_bot = QColor("#0d0520")
            accent = NEON_MAGENTA
        elif self._hovered:
            bg_top = QColor("#0f1a2e")
            bg_bot = QColor("#060d1a")
            accent = QColor("#33ffff")
        else:
            bg_top = QColor("#0a0e1a")
            bg_bot = QColor("#050810")
            accent = NEON_CYAN

        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0, bg_top)
        bg_grad.setColorAt(1, bg_bot)
        p.setBrush(QBrush(bg_grad))

        # Border
        border_color = BORDER_CHECKED if self._checked else BORDER_GLOW
        border_alpha = 180 if self._hovered or self._checked else 80
        border_col = QColor(border_color)
        border_col.setAlpha(border_alpha)
        p.setPen(QPen(border_col, 1.5))
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 8, 8)

        # --- Scan-Lines (subtiler Cyberpunk-Effekt) ---
        scan_pen = QPen(QColor(255, 255, 255, 8), 1.0)
        p.setPen(scan_pen)
        for sy in range(0, h, 4):
            p.drawLine(QPointF(2, sy), QPointF(w - 2, sy))

        # --- Knoten am linken Rand, fixer Abstand, vertikal zentriert ---
        node_radius = 4
        node_x = 22  # nah am linken Rand
        node_spacing = 12  # fixer Abstand zwischen Knoten

        # Gesamthoehe der Knotenspalte
        column_h = (self._num_nodes - 1) * node_spacing if self._num_nodes > 1 else 0
        # Vertikal zentrieren
        start_y = (h - column_h) / 2

        nodes = []
        for i in range(self._num_nodes):
            y = start_y + i * node_spacing
            nodes.append(QPointF(node_x, y))

        # --- Verbindungslinien: Knoten -> rechter Rand (fanning out) ---
        num_targets = max(3, self._num_nodes // 2)
        target_x = w - 5
        # Targets vertikal zentriert, gleiche Logik wie Knoten
        target_col_h = (num_targets - 1) * node_spacing if num_targets > 1 else 0
        targets_top = (h - target_col_h) / 2
        target_spacing = node_spacing

        for node in nodes:
            for t in range(num_targets):
                target_y = targets_top + t * target_spacing
                # Farbe: Gradient von Cyan nach transparent
                line_col = QColor(accent)
                line_col.setAlpha(35)
                p.setPen(QPen(line_col, 0.8))
                p.drawLine(node, QPointF(target_x, target_y))

        # --- Glow hinter Knoten ---
        p.setPen(Qt.PenStyle.NoPen)
        for node in nodes:
            glow = QRadialGradient(node, node_radius * 4)
            glow_col = QColor(accent)
            glow_col.setAlpha(50)
            glow.setColorAt(0, glow_col)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.drawEllipse(node, node_radius * 4, node_radius * 4)

        # --- Knoten zeichnen ---
        node_outline = QColor(accent)
        node_outline.setAlpha(220)
        p.setPen(QPen(node_outline, 1.8))
        node_fill = QColor(accent)
        node_fill.setAlpha(60)
        p.setBrush(QBrush(node_fill))

        for node in nodes:
            p.drawEllipse(node, node_radius, node_radius)

        # --- Label rechts unten ---
        p.setPen(QPen(accent))
        font = QFont("Consolas", 10, QFont.Weight.Bold)
        p.setFont(font)
        text_rect = QRectF(node_x + 15, h - 24, w - node_x - 20, 20)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._label)

        p.end()


class TestWindow(QWidget):
    """Testfenster mit allen Layer-Buttons als Pipeline."""

    # Button-Breiten: abnehmend wie die CNN-Architektur
    BUTTON_WIDTHS = [170, 150, 130, 110, 80]
    # Abstände zwischen Buttons: abnehmend fuer Pipeline-Effekt
    SPACINGS = [12, 8, 5, 3]  # 4 Luecken zwischen 5 Buttons

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNN Arch Buttons - Cyberpunk Pipeline")
        self.setStyleSheet("background-color: #050508;")

        layout = QHBoxLayout(self)
        layout.setSpacing(0)  # Spacing manuell per Spacer
        layout.setContentsMargins(20, 20, 20, 20)

        for i, (num_nodes, label) in enumerate(LAYERS):
            btn_w = self.BUTTON_WIDTHS[i]
            btn = ArchLayerButton(num_nodes, label, btn_width=btn_w)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)

            # Spacer zwischen Buttons (abnehmend)
            if i < len(LAYERS) - 1:
                gap = self.SPACINGS[i]
                spacer = QSpacerItem(gap, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                layout.addSpacerItem(spacer)


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
