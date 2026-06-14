"""Interface für Kamera-Zugriff."""

from typing import Protocol
import numpy as np


class ICameraService(Protocol):
    """Interface für Kamera-Zugriff."""

    def start(self) -> None:
        """Startet die Kamera und initialisiert den Stream."""
        ...

    def stop(self) -> None:
        """Stoppt die Kamera und gibt Ressourcen frei."""
        ...

    def get_frame(self) -> np.ndarray:
        """Holt aktuellen Frame von der Kamera.

        Returns:
            RGB-Bild als NumPy-Array (H, W, 3)

        Raises:
            CameraNotAvailableError: Wenn Kamera nicht verfügbar
        """
        ...

    def is_running(self) -> bool:
        """Prüft, ob Kamera läuft."""
        ...


