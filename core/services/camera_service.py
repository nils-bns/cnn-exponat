"""CameraService - Webcam-Zugriff."""

import logging
import numpy as np
import cv2
from core.exceptions import CameraNotAvailableError, CameraFrameError


logger = logging.getLogger(__name__)


class CameraService:
    """Liest Bilder von der Webcam.

    Verwendet OpenCV für plattformunabhängigen Kamera-Zugriff.
    Konvertiert Frames von BGR (OpenCV) zu RGB und spiegelt sie
    standardmäßig horizontal (Spiegel-Effekt für Besucher).
    """

    DEFAULT_CAMERA_INDEX = 0
    DEFAULT_FLIP_HORIZONTAL = True

    def __init__(
        self,
        camera_index: int = DEFAULT_CAMERA_INDEX,
        flip_horizontal: bool = DEFAULT_FLIP_HORIZONTAL,
    ):
        """Initialisiert CameraService.

        Args:
            camera_index: Index der Kamera (0 = default)
            flip_horizontal: Ob das Kamerabild horizontal gespiegelt wird
                (Spiegel-Effekt, Default True)
        """
        self._camera_index = camera_index
        self._flip_horizontal = flip_horizontal
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
        self._release_camera()
        logger.info("Kamera gestoppt")

    def _release_camera(self) -> None:
        """Gibt das Kamera-Handle frei und setzt den Zustand zurück.

        Idempotent: Kann auch aufgerufen werden, wenn kein Handle existiert.
        Setzt `_running` auf False, damit ein anschließendes `start()` das
        Gerät sauber neu öffnet.
        """
        if self._camera is not None:
            self._camera.release()
            self._camera = None
        self._running = False

    def reconnect(self) -> bool:
        """Gibt die Kamera frei und öffnet sie neu.

        Wird bei Verbindungsverlust im Betrieb (oder fehlender Kamera beim
        Start) wiederholt aufgerufen, bis das Gerät zurück ist.

        Returns:
            True, wenn die Kamera erfolgreich neu geöffnet wurde, sonst False.
        """
        logger.warning(
            "Versuche Kamera neu zu verbinden (Index %s)", self._camera_index
        )
        self._release_camera()
        try:
            self.start()
            logger.info("Kamera neu verbunden")
            return True
        except CameraNotAvailableError:
            logger.warning("Kamera weiterhin nicht verfügbar")
            return False

    def get_frame(self) -> np.ndarray:
        """Holt aktuellen Frame von der Kamera.

        Returns:
            RGB-Bild als NumPy-Array (H, W, 3), horizontal gespiegelt
            sofern `flip_horizontal=True` (Default)

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

        if self._flip_horizontal:
            frame_rgb = cv2.flip(frame_rgb, 1)

        return frame_rgb

    def is_running(self) -> bool:
        """Prüft, ob Kamera läuft.

        Returns:
            True wenn Kamera läuft, sonst False
        """
        return self._running

