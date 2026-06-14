"""ApplicationFacade - Orchestration aller Core-Services."""

import logging
import numpy as np
from core.interfaces import (
    ICameraService,
    IModelService,
    IVisualizationService,
    IPresetService
)
from core.models import PresetConfig


logger = logging.getLogger(__name__)


class ApplicationFacade:
    """Facade für koordinierte Nutzung aller Core-Services.

    Vereinfacht View-Zugriff durch High-Level-Methoden und
    orchestriert den Datenfluss zwischen Services.
    """

    def __init__(
        self,
        camera: ICameraService,
        model: IModelService,
        visualization: IVisualizationService,
        presets: IPresetService
    ):
        """Initialisiert ApplicationFacade mit Dependency Injection.

        Args:
            camera: CameraService-Instanz
            model: ModelService-Instanz
            visualization: VisualizationService-Instanz
            presets: PresetService-Instanz
        """
        self._camera = camera
        self._model = model
        self._visualization = visualization
        self._presets = presets
        self._current_layer: str | None = None

        logger.info("ApplicationFacade erstellt")

    def initialize(self) -> None:
        """Initialisiert alle Services (Modell laden, Kamera starten).

        Raises:
            ModelLoadError: Wenn Modell nicht geladen werden kann
            CameraNotAvailableError: Wenn Kamera nicht verfügbar
        """
        logger.info("Initialisiere ApplicationFacade...")

        # Lade Model
        self._model.load_model()
        logger.info("Model geladen")

        # Starte Kamera
        self._camera.start()
        logger.info("Kamera gestartet")

        # Setze initialen Layer
        layers = self.get_layer_names()
        if layers:
            self._current_layer = layers[0]
            logger.info(f"Initialer Layer: {self._current_layer}")

        logger.info("ApplicationFacade erfolgreich initialisiert")

    def get_visualization_for_layer(self, layer_name: str) -> np.ndarray:
        """Kompletter Workflow: Frame holen → Inferenz → Visualisierung.

        Args:
            layer_name: ResNet18-Layer (z.B. 'layer1', 'layer2')

        Returns:
            Visualisiertes RGB-Bild (H, W, 3)

        Raises:
            CameraFrameError: Wenn Frame nicht gelesen werden kann
            InvalidLayerError: Wenn layer_name ungültig
        """
        logger.debug(f"Erstelle Visualisierung für Layer '{layer_name}'")

        # 1. Frame von Kamera holen
        frame = self._camera.get_frame()

        # 2. Layer-Aktivierung extrahieren
        activations = self._model.extract_layer_activations(frame, layer_name)

        # 3. Aktives Preset holen
        preset = self._presets.get_active_preset(layer_name)

        # 4. Visualisierung anwenden
        visualization = self._visualization.visualize(activations, preset)

        return visualization

    def get_visualization_with_preset(
        self,
        layer_name: str,
        preset: PresetConfig
    ) -> np.ndarray:
        """Kompletter Workflow mit spezifischem Preset (für Live-Vorschau).

        Args:
            layer_name: ResNet18-Layer (z.B. 'layer1', 'layer2')
            preset: PresetConfig zur Verwendung (statt aktivem Preset)

        Returns:
            Visualisiertes RGB-Bild (H, W, 3)

        Raises:
            CameraFrameError: Wenn Frame nicht gelesen werden kann
            InvalidLayerError: Wenn layer_name ungültig
        """
        logger.debug(f"Erstelle Visualisierung für Layer '{layer_name}' mit Custom-Preset")

        # 1. Frame von Kamera holen
        frame = self._camera.get_frame()

        # 2. Layer-Aktivierung extrahieren
        activations = self._model.extract_layer_activations(frame, layer_name)

        # 3. Visualisierung mit übergebenem Preset anwenden
        visualization = self._visualization.visualize(activations, preset)

        return visualization

    def change_layer(self, layer_name: str) -> None:
        """Wechselt aktuellen Layer (für State-Tracking).

        Args:
            layer_name: Neuer Layer-Name

        Raises:
            ValueError: Wenn layer_name ungültig
        """
        available_layers = self.get_layer_names()
        if layer_name not in available_layers:
            raise ValueError(
                f"Ungültiger Layer '{layer_name}'. "
                f"Verfügbare Layer: {available_layers}"
            )

        self._current_layer = layer_name
        logger.info(f"Layer gewechselt zu: {layer_name}")

    def get_current_layer(self) -> str | None:
        """Gibt aktuellen Layer zurück.

        Returns:
            Name des aktuellen Layers oder None
        """
        return self._current_layer

    def get_layer_names(self) -> list[str]:
        """Delegiert an ModelService.

        Returns:
            Liste aller verfügbaren Layer-Namen
        """
        return self._model.get_layer_names()

    def get_layer_channel_count(self, layer_name: str) -> int:
        """Delegiert an ModelService.

        Args:
            layer_name: Name des Layers

        Returns:
            Anzahl der Channels im Layer

        Raises:
            InvalidLayerError: Wenn layer_name ungültig
        """
        return self._model.get_layer_channel_count(layer_name)

    def get_top_predictions(self, k: int = 3) -> list[tuple[str, float]]:
        """Gibt Top-K Predictions des letzten Forward Pass zurueck.

        Delegiert an ModelService. Gibt gecachte Predictions des letzten
        `extract_layer_activations()`-Aufrufs zurueck.

        Args:
            k: Anzahl der Top-Predictions

        Returns:
            Liste von (Klassenname, Wahrscheinlichkeit) Tupeln
        """
        return self._model.get_top_predictions(k)

    def compute_gradcam(self, layer_name: str) -> np.ndarray:
        """Berechnet GradCAM-Heatmap fuer aktuellen Kamera-Frame.

        Holt Frame intern von Kamera und delegiert an ModelService.

        Args:
            layer_name: Ziel-Layer fuer GradCAM

        Returns:
            RGB-Overlay-Bild (H, W, 3) mit dtype uint8
        """
        frame = self._camera.get_frame()
        return self._model.compute_gradcam(frame, layer_name)

    def save_preset(
        self,
        layer_name: str,
        preset_id: int,
        preset: PresetConfig
    ) -> None:
        """Delegiert an PresetService.

        Args:
            layer_name: Name des Layers
            preset_id: ID des Presets (0-2)
            preset: PresetConfig-Objekt
        """
        self._presets.save_preset(layer_name, preset_id, preset)
        logger.info(f"Preset {preset_id} für '{layer_name}' gespeichert")

    def get_all_presets_for_layer(self, layer_name: str) -> list[PresetConfig]:
        """Delegiert an PresetService.

        Args:
            layer_name: Name des Layers

        Returns:
            Liste von PresetConfig-Objekten
        """
        return self._presets.get_all_presets_for_layer(layer_name)

    def get_preset(self, layer_name: str, preset_id: int) -> PresetConfig:
        """Holt ein spezifisches Preset.

        Args:
            layer_name: Name des Layers
            preset_id: ID des Presets (0-2)

        Returns:
            PresetConfig-Objekt
        """
        return self._presets.get_preset(layer_name, preset_id)

    def get_active_preset(self, layer_name: str) -> PresetConfig:
        """Holt aktuell aktives Preset für Layer.

        Delegiert an PresetService.

        Args:
            layer_name: Name des Layers

        Returns:
            PresetConfig des aktiven Presets
        """
        return self._presets.get_active_preset(layer_name)

    def set_active_preset(self, layer_name: str, preset_id: int) -> None:
        """Delegiert an PresetService.

        Args:
            layer_name: Name des Layers
            preset_id: ID des Presets (0-2)
        """
        self._presets.set_active_preset(layer_name, preset_id)
        logger.info(f"Aktives Preset für '{layer_name}' auf {preset_id} gesetzt")

    def shutdown(self) -> None:
        """Fährt alle Services herunter."""
        logger.info("Fahre ApplicationFacade herunter...")

        try:
            self._camera.stop()
            logger.info("Kamera gestoppt")
        except Exception as e:
            logger.error(f"Fehler beim Stoppen der Kamera: {e}")

        logger.info("ApplicationFacade heruntergefahren")

