"""CameraService - Webcam-Zugriff."""

import logging
import numpy as np
import cv2
from core.exceptions import CameraNotAvailableError, CameraFrameError


logger = logging.getLogger(__name__)


class CameraService:
    """Liest Bilder von der Webcam.

    Verwendet OpenCV für plattformunabhängigen Kamera-Zugriff.
    Konvertiert Frames von BGR (OpenCV) zu RGB.
    """

    DEFAULT_CAMERA_INDEX = 0

    def __init__(self, camera_index: int = DEFAULT_CAMERA_INDEX):
        """Initialisiert CameraService.

        Args:
            camera_index: Index der Kamera (0 = default)
        """
        self._camera_index = camera_index
        self._camera: cv2.VideoCapture | None = None
        self._running = False

    def start(self) -> None:
        """Startet die Kamera und initialisiert den Stream.

        Raises:
            CameraNotAvailableError: Wenn Kamera nicht verfügbar
        """
        if self._running:
            logger.warning("Kamera läuft bereits")
            return

        logger.info(f"Starte Kamera mit Index {self._camera_index}")
        self._camera = cv2.VideoCapture(self._camera_index)

        if not self._camera.isOpened():
            raise CameraNotAvailableError(
                f"Kamera mit Index {self._camera_index} nicht verfügbar"
            )

        self._running = True
        logger.info("Kamera erfolgreich gestartet")

    def stop(self) -> None:
        """Stoppt die Kamera und gibt Ressourcen frei."""
        if not self._running:
            logger.warning("Kamera läuft nicht")
            return

        logger.info("Stoppe Kamera")
        if self._camera is not None:
            self._camera.release()
            self._camera = None
        self._running = False
        logger.info("Kamera gestoppt")

    def get_frame(self) -> np.ndarray:
        """Holt aktuellen Frame von der Kamera.

        Returns:
            RGB-Bild als NumPy-Array (H, W, 3)

        Raises:
            CameraNotAvailableError: Wenn Kamera nicht läuft
            CameraFrameError: Wenn Frame nicht gelesen werden konnte
        """
        if not self._running or self._camera is None:
            raise CameraNotAvailableError("Kamera ist nicht gestartet")

        ret, frame = self._camera.read()

        if not ret or frame is None:
            raise CameraFrameError("Frame konnte nicht gelesen werden")

        # BGR (OpenCV) → RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return frame_rgb

    def is_running(self) -> bool:
        """Prüft, ob Kamera läuft.

        Returns:
            True wenn Kamera läuft, sonst False
        """
        return self._running

