"""Wiederverwendbares Kamera-Display-Widget.

Genutzt von BEIDEN Modi (Visitor + Admin).
Ersetzt QLabel + inline Frame-Konvertierung.
"""

import logging
import numpy as np
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSlot

from view.utils.frame_converter import numpy_to_qpixmap

logger = logging.getLogger(__name__)


class CameraDisplayWidget(QLabel):
    """Fullscreen-fähiges Kamera-Display.

    Features:
    - Automatische Frame-Konvertierung (NumPy → QPixmap)
    - Aspect-Ratio-erhaltende Skalierung
    - Zentrales Styling über StyleManager

    Verwendung:
        display = CameraDisplayWidget()
        camera_thread.frame_ready.connect(display.update_frame)
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialisiert Camera-Display-Widget.

        Args:
            parent: Parent-Widget
        """
        super().__init__(parent)

        # Alignment
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Styling
        self._apply_styles()

        # Platzhalter-Text
        self.setText("Warte auf Kamera-Feed...")

        logger.debug("CameraDisplayWidget initialisiert")

    def _apply_styles(self) -> None:
        """Setzt ObjectName fuer base.qss-Selektor."""
        self.setObjectName("camera-display")

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame: np.ndarray) -> None:
        """Aktualisiert Display mit neuem Frame.

        Slot für camera_thread.frame_ready Signal.

        Args:
            frame: RGB-Bild als NumPy array (H, W, 3)
        """
        try:
            # Konvertierung mit Skalierung auf Label-Größe
            pixmap = numpy_to_qpixmap(frame, self.size())
            self.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"Fehler bei Frame-Update: {e}")
            self.setText("Fehler bei Frame-Anzeige")
