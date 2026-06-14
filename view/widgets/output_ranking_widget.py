"""OutputRankingWidget fuer Visitor Mode.

Zeigt die Top-3-Klassifikationsergebnisse des ResNet18-Modells
als horizontale Balken an. Semi-transparentes Overlay-Widget.
"""

import logging

from PyQt6.QtWidgets import QVBoxLayout, QGridLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient

from view.media.content.imagenet_translations import IMAGENET_DE
from view.media.content.output_ranking_content import WIDGET_TITLE
from view.widgets.base_overlay import BaseOverlayWidget
from view.styles import OUTPUT_RANKING_DIMS
from view.styles.colors import (
    ARCH_LAYER_MAGENTA,
    CYBERPUNK_BG_TOP,
    CYBERPUNK_BG_BOT,
    CYBERPUNK_CYAN,
    OVERLAY_BORDER_ALPHA,
    OUTPUT_RANKING_BAR_DARK,
    OUTPUT_RANKING_BAR_BRIGHT,
    TEXT_PRIMARY,
)

logger = logging.getLogger(__name__)

# Farben aus view.styles.colors importiert (keine lokalen Konstanten)
_BG_TOP = QColor(CYBERPUNK_BG_TOP)
_BG_BOT = QColor(CYBERPUNK_BG_BOT)
_c = QColor(CYBERPUNK_CYAN)
_BORDER_GLOW = QColor(_c.red(), _c.green(), _c.blue(), OVERLAY_BORDER_ALPHA)


class OutputRankingWidget(BaseOverlayWidget):
    """Widget fuer Top-3-Klassifikationsergebnisse.

    Attributes:
        MIN_CONFIDENCE: Minimale Konfidenz der Top-1-Prediction,
            damit das Widget angezeigt wird (0.0 - 1.0). Default: 0.5 (50%).

    Zeigt Klassenname, proportionalen Balken und Prozentzahl
    fuer die drei wahrscheinlichsten ImageNet-Klassen an.

    Features:
    - Semi-transparenter Hintergrund (konsistent mit InfoPanel)
    - 3 Zeilen: Klassenname | Balken | Prozentzahl
    - Balkenfarbe als Gradient (dunkel bei niedrigen, hell bei hohen Werten)
    - Startet unsichtbar, wird bei ersten Predictions eingeblendet

    Usage:
        widget = OutputRankingWidget(parent)
        widget.update_predictions([("tabby", 0.86), ("tiger_cat", 0.63)])
    """

    # Grenzwert: Widget wird nur angezeigt wenn Top-1 >= diesem Wert
    MIN_CONFIDENCE = 0.1

    def __init__(self, parent: QWidget | None = None):
        """Initialisiert OutputRankingWidget.

        Args:
            parent: Parent-Widget (VisitorModeWidget)
        """
        super().__init__(parent)

        self.setFixedSize(OUTPUT_RANKING_DIMS.width, OUTPUT_RANKING_DIMS.height)
        self.setVisible(False)

        self._name_labels: list[QLabel] = []
        self._bar_widgets: list[QWidget] = []
        self._percent_labels: list[QLabel] = []
        self._language: str = "de"

        self._init_ui()

        logger.debug("OutputRankingWidget initialisiert")

    def _init_ui(self) -> None:
        """Initialisiert das UI-Layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            OUTPUT_RANKING_DIMS.padding,
            OUTPUT_RANKING_DIMS.padding,
            OUTPUT_RANKING_DIMS.padding,
            OUTPUT_RANKING_DIMS.padding
        )
        layout.setSpacing(6)

        # Titel (rechts ausgerichtet)
        self._title_label = QLabel(WIDGET_TITLE["de"], self)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._title_label.setObjectName("overlay-title")
        self._title_label.setStyleSheet(f"color: {ARCH_LAYER_MAGENTA};")
        layout.addWidget(self._title_label)

        # Grid fuer Prediction-Zeilen
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setColumnMinimumWidth(0, 80)
        grid.setColumnMinimumWidth(2, 40)
        layout.addLayout(grid)

        for i in range(3):
            # Klassenname (linksbuendig)
            name_label = QLabel("", self)
            name_label.setObjectName("overlay-text")
            name_label.setStyleSheet(f"color: {CYBERPUNK_CYAN};")
            name_label.setFixedWidth(130)
            grid.addWidget(name_label, i, 0)
            self._name_labels.append(name_label)

            # Balken (proportionale Breite)
            bar = QWidget(self)
            bar.setFixedHeight(OUTPUT_RANKING_DIMS.bar_height)
            bar.setFixedWidth(0)
            grid.addWidget(bar, i, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            self._bar_widgets.append(bar)

            # Prozentzahl (rechtsbuendig)
            percent_label = QLabel("", self)
            percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            percent_label.setObjectName("overlay-text")
            percent_label.setStyleSheet(f"color: {CYBERPUNK_CYAN};")
            percent_label.setFixedWidth(40)
            grid.addWidget(percent_label, i, 2)
            self._percent_labels.append(percent_label)

        layout.addStretch()

    @pyqtSlot(list)
    def update_predictions(self, predictions: list[tuple[str, float]]) -> None:
        """Aktualisiert die angezeigten Predictions.

        Args:
            predictions: Liste von (Klassenname, Wahrscheinlichkeit) Tupeln,
                         sortiert nach Wahrscheinlichkeit absteigend
        """
        if not predictions or predictions[0][1] < self.MIN_CONFIDENCE:
            self.setVisible(False)
            return

        self.setVisible(True)

        for i in range(3):
            if i < len(predictions):
                name, probability = predictions[i]
                percent = int(probability * 100)

                display_name = IMAGENET_DE.get(name, name) if self._language == "de" else name
                self._name_labels[i].setText(display_name)
                self._percent_labels[i].setText(f"{percent}%")

                bar_width = int(probability * OUTPUT_RANKING_DIMS.bar_max_width)
                self._bar_widgets[i].setFixedWidth(max(bar_width, 2))

                color = self._get_bar_color(probability)
                self._bar_widgets[i].setStyleSheet(
                    f"background-color: {color}; border-radius: 2px;"
                )
            else:
                self._name_labels[i].setText("")
                self._percent_labels[i].setText("")
                self._bar_widgets[i].setFixedWidth(0)

        logger.debug(f"Predictions aktualisiert: {len(predictions)} Eintraege")

    def _get_bar_color(self, probability: float) -> str:
        """Berechnet Balkenfarbe basierend auf Wahrscheinlichkeit.

        Interpoliert linear zwischen gedaempftem und hellem Cyan.

        Args:
            probability: Wahrscheinlichkeit (0.0 - 1.0)

        Returns:
            Hex-Farbcode (z.B. '#4CAF50')
        """
        r = int(OUTPUT_RANKING_BAR_DARK[0] + (OUTPUT_RANKING_BAR_BRIGHT[0] - OUTPUT_RANKING_BAR_DARK[0]) * probability)
        g = int(OUTPUT_RANKING_BAR_DARK[1] + (OUTPUT_RANKING_BAR_BRIGHT[1] - OUTPUT_RANKING_BAR_DARK[1]) * probability)
        b = int(OUTPUT_RANKING_BAR_DARK[2] + (OUTPUT_RANKING_BAR_BRIGHT[2] - OUTPUT_RANKING_BAR_DARK[2]) * probability)
        return f"#{r:02x}{g:02x}{b:02x}"

    def paintEvent(self, event) -> None:
        """Zeichnet Cyberpunk-Hintergrund mit Gradient und Glow-Border.

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = OUTPUT_RANKING_DIMS.border_radius

        # Hintergrund-Gradient (dunkelblau, wie ArchLayerButton)
        bg_grad = QLinearGradient(0, 0, 0, self.height())
        bg_grad.setColorAt(0, _BG_TOP)
        bg_grad.setColorAt(1, _BG_BOT)
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(QPen(_BORDER_GLOW, 1.5))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, r, r)

        super().paintEvent(event)

    def update_language(self, language: str) -> None:
        """Aktualisiert Titel und speichert Sprache fuer Klassennamen-Uebersetzung.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        self._language = language
        self._title_label.setText(WIDGET_TITLE.get(language, WIDGET_TITLE["de"]))

        logger.debug(f"OutputRankingWidget Sprache aktualisiert: {language}")
