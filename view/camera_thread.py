"""QThread für asynchrone Frame-Verarbeitung.

Verantwortlichkeiten:
- Kontinuierlicher Kamera-Frame-Abruf in separatem Thread
- Emission von Signals bei neuem Frame
- Thread-Lifecycle-Management
- Temporäres Preset-Override für Admin-Modus Live-Vorschau
"""

import logging
import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from core.facade import ApplicationFacade
from core.exceptions import CameraError
from core.models import PresetConfig


logger = logging.getLogger(__name__)


class CameraThread(QThread):
    """Thread für asynchrone Kamera-Frame-Verarbeitung.

    Holt kontinuierlich Frames von der Kamera und verarbeitet sie
    mit dem ApplicationFacade. Emittiert Signals für UI-Updates.

    Signals:
        frame_ready: Emittiert wenn neuer Frame verfügbar (np.ndarray)
        error_occurred: Emittiert bei Fehler (str)
    """

    # Qt Signals
    frame_ready = pyqtSignal(np.ndarray)
    predictions_ready = pyqtSignal(list)
    gradcam_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)

    # Throttling-Intervalle
    PREDICTIONS_INTERVAL_S = 1.0
    GRADCAM_INTERVAL_S = 1/30

    def __init__(
        self,
        facade: ApplicationFacade,
        target_layer: str = "layer1"
    ):
        """Initialisiert den CameraThread.

        Args:
            facade: ApplicationFacade-Instanz
            target_layer: Initialer Layer für Visualisierung
        """
        super().__init__()

        self._facade = facade
        self._target_layer = target_layer
        self._running = False
        self._paused = False
        self._temp_preset: PresetConfig | None = None  # Für Live-Vorschau
        self._last_predictions_time: float = 0.0
        self._last_gradcam_time: float = 0.0
        self._gradcam_layers: list[str] = []

        logger.debug(f"CameraThread erstellt (Layer: {target_layer})")

    def run(self) -> None:
        """Hauptschleife des Threads.

        Wird automatisch beim Start des Threads aufgerufen.
        Holt kontinuierlich Frames und verarbeitet sie.
        """
        self._running = True
        logger.info("CameraThread gestartet")

        consecutive_errors = 0
        max_consecutive_errors = 5

        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue

            try:
                # Frame mit Visualisierung holen
                # Wenn temporäres Preset gesetzt, verwende dieses (Live-Vorschau)
                if self._temp_preset is not None:
                    frame = self._facade.get_visualization_with_preset(
                        self._target_layer,
                        self._temp_preset
                    )
                else:
                    # Standard: Verwende aktives Preset
                    frame = self._facade.get_visualization_for_layer(self._target_layer)

                # Signal emittieren
                self.frame_ready.emit(frame)

                # Predictions emittieren (throttled)
                current_time = time.time()
                if current_time - self._last_predictions_time >= self.PREDICTIONS_INTERVAL_S:
                    predictions = self._facade.get_top_predictions()
                    if predictions:
                        self.predictions_ready.emit(predictions)
                        self._last_predictions_time = current_time

                # GradCAM emittieren (throttled, nur fuer bestimmte Layer)
                if (self._target_layer in self._gradcam_layers
                        and current_time - self._last_gradcam_time
                        >= self.GRADCAM_INTERVAL_S):
                    try:
                        gradcam_overlay = self._facade.compute_gradcam(
                            self._target_layer
                        )
                        self.gradcam_ready.emit(gradcam_overlay)
                        self._last_gradcam_time = current_time
                    except Exception as e:
                        logger.warning("GradCAM-Fehler: %s", e)

                # Error-Counter zurücksetzen
                consecutive_errors = 0

                # Kurze Pause (30 FPS)
                time.sleep(1.0 / 30.0)

            except CameraError as e:
                consecutive_errors += 1
                logger.warning(f"Kamera-Fehler: {e} (#{consecutive_errors})")

                if consecutive_errors >= max_consecutive_errors:
                    error_msg = f"Kamera nicht verfügbar: {e}"
                    self.error_occurred.emit(error_msg)
                    logger.error(f"Zu viele aufeinanderfolgende Fehler, stoppe Thread")
                    self._running = False
                else:
                    # Kurz warten vor erneutem Versuch
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Unerwarteter Fehler in CameraThread: {e}", exc_info=True)
                error_msg = f"Unerwarteter Fehler: {e}"
                self.error_occurred.emit(error_msg)
                time.sleep(0.5)

        logger.info("CameraThread beendet")

    def stop(self) -> None:
        """Stoppt den Thread gracefully."""
        if self._running:
            logger.info("Stoppe CameraThread")
            self._running = False
            self.wait()  # Warte auf Thread-Ende

    def pause(self) -> None:
        """Pausiert die Frame-Verarbeitung."""
        self._paused = True
        logger.debug("CameraThread pausiert")

    def resume(self) -> None:
        """Setzt die Frame-Verarbeitung fort."""
        self._paused = False
        logger.debug("CameraThread fortgesetzt")

    def change_layer(self, layer_name: str) -> None:
        """Ändert den aktiven Layer für Visualisierung.

        Args:
            layer_name: Neuer Layer-Name
        """
        if layer_name != self._target_layer:
            logger.info(f"Layer-Wechsel: {self._target_layer} -> {layer_name}")
            self._target_layer = layer_name

    def set_temp_preset(self, preset: PresetConfig) -> None:
        """Setzt temporäres Preset für Live-Vorschau (Admin-Modus).

        Args:
            preset: Temporäres Preset zur Verwendung
        """
        self._temp_preset = preset
        logger.debug(f"Temporäres Preset gesetzt: {preset.name}")

    def clear_temp_preset(self) -> None:
        """Entfernt temporäres Preset (zurück zum aktiven Preset)."""
        self._temp_preset = None
        logger.debug("Temporäres Preset entfernt")

    def set_gradcam_layers(self, layers: list[str]) -> None:
        """Setzt die Layer fuer die GradCAM berechnet wird.

        Args:
            layers: Liste von Layer-Namen (z.B. ['layer3', 'layer4'])
        """
        self._gradcam_layers = layers
        logger.debug("GradCAM-Layer gesetzt: %s", layers)

    @property
    def is_running(self) -> bool:
        """Prüft ob Thread läuft."""
        return self._running

    @property
    def current_layer(self) -> str:
        """Gibt aktuellen Layer zurück."""
        return self._target_layer

