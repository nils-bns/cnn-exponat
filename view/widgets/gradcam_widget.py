"""GradCAM-Widget fuer Visitor Mode.

Zeigt GradCAM-Visualisierung mit dekorativem Glow-Kreis-Hintergrund.
Das Kamerabild wird kreisfoermig maskiert innerhalb des Kreises dargestellt.
"""

import logging
from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QPainter, QPixmap, QPainterPath

from view.media.content.gradcam_widget_content import WIDGET_TITLE
from view.utils.frame_converter import numpy_to_qpixmap
from view.widgets.base_overlay import BaseOverlayWidget
from view.styles import GRADCAM_DIMS

logger = logging.getLogger(__name__)

_GRADCAM_BG_PATH = Path(__file__).parent.parent / "media" / "img" / "gradcam.png"


class GradCAMWidget(BaseOverlayWidget):
    """UI-Rahmen fuer GradCAM-Visualisierung mit Kreis-Hintergrund.

    Zeigt sich nur bei den letzten beiden CNN-Layern.
    Stellt update_frame(np.ndarray) als Schnittstelle bereit,
    ueber die der GradCAM-Implementierer seine Daten einspeist.
    Das Bild wird kreisfoermig maskiert innerhalb eines Glow-Kreises
    (gradcam.png) dargestellt.

    Usage:
        widget = GradCAMWidget(visible_layers=['layer3', 'layer4'], parent=parent)
        widget.set_current_layer('layer3')  # Widget wird sichtbar
        widget.update_frame(frame)          # GradCAM-Frame anzeigen
    """

    def __init__(
        self, visible_layers: list[str], parent: QWidget | None = None
    ):
        """Initialisiert GradCAMWidget.

        Args:
            visible_layers: Layer-Namen bei denen das Widget sichtbar ist
            parent: Parent-Widget (VisitorModeWidget)
        """
        super().__init__(parent)

        self._visible_layers = visible_layers

        self.setFixedSize(GRADCAM_DIMS.width, GRADCAM_DIMS.height)
        self.setVisible(False)

        self._display_label: QLabel | None = None

        # Hintergrundbild (Glow-Kreis) laden
        self._bg_pixmap = QPixmap(str(_GRADCAM_BG_PATH))
        if self._bg_pixmap.isNull():
            logger.warning(
                "GradCAM-Hintergrundbild nicht ladbar: %s", _GRADCAM_BG_PATH
            )

        self._init_ui()

        logger.debug(
            "GradCAMWidget initialisiert (sichtbar bei: %s)",
            self._visible_layers,
        )

    def _init_ui(self) -> None:
        """Initialisiert das UI-Layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            GRADCAM_DIMS.padding,
            GRADCAM_DIMS.padding,
            GRADCAM_DIMS.padding,
            GRADCAM_DIMS.padding,
        )
        layout.setSpacing(0)

        # Titel (aktuell Leerstring, Label bleibt fuer spaeteren Gebrauch)
        self._title_label = QLabel(WIDGET_TITLE["de"], self)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._title_label.setObjectName("overlay-title")
        self._title_label.setVisible(False)

        # Display-Bereich (GradCAM-Frames, kreisfoermig maskiert)
        self._display_label = QLabel(self)
        self._display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display_label.setObjectName("overlay-text")
        layout.addWidget(self._display_label, stretch=1)

    def set_current_layer(self, layer_name: str) -> None:
        """Steuert Visibility basierend auf Layer-Name.

        Args:
            layer_name: Aktuell aktiver Layer-Name
        """
        should_show = layer_name in self._visible_layers
        self.setVisible(should_show)
        logger.debug(
            "GradCAM Visibility: %s (Layer: %s)", should_show, layer_name
        )

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame: np.ndarray) -> None:
        """Aktualisiert das angezeigte Bild mit kreisfoermiger Maskierung.

        Das GradCAM-Bild wird kreisfoermig zugeschnitten, damit es
        innerhalb des Glow-Kreises (gradcam.png) dargestellt wird.

        Args:
            frame: RGB-Bild als NumPy array (H, W, 3) mit dtype uint8
        """
        label_size = self._display_label.size()
        pixmap = numpy_to_qpixmap(frame, label_size)

        # Kreisfoermige Maskierung
        diameter = min(pixmap.width(), pixmap.height())
        masked = QPixmap(pixmap.size())
        masked.fill(Qt.GlobalColor.transparent)

        painter = QPainter(masked)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Kreis-Clip zentriert auf dem Pixmap
        path = QPainterPath()
        cx = pixmap.width() / 2
        cy = pixmap.height() / 2
        radius = diameter / 2
        path.addEllipse(cx - radius, cy - radius, diameter, diameter)
        painter.setClipPath(path)

        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        self._display_label.setPixmap(masked)

    def paintEvent(self, event) -> None:
        """Zeichnet GradCAM-Hintergrundbild (Glow-Kreis).

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._bg_pixmap.isNull():
            scaled_bg = self._bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Zentriert zeichnen
            x = (self.width() - scaled_bg.width()) // 2
            y = (self.height() - scaled_bg.height()) // 2
            painter.drawPixmap(x, y, scaled_bg)

        super().paintEvent(event)

    def update_language(self, language: str) -> None:
        """Aktualisiert Titel fuer die angegebene Sprache.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        self._title_label.setText(WIDGET_TITLE.get(language, WIDGET_TITLE["de"]))

        logger.debug(f"GradCAMWidget Sprache aktualisiert: {language}")
