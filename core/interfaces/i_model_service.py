"""Interface für CNN-Model-Inferenz."""

from typing import Protocol
import numpy as np
import torch


class IModelService(Protocol):
    """Interface für CNN-Model-Inferenz."""

    def load_model(self) -> None:
        """Lädt ResNet18-Modell (pre-trained)."""
        ...

    def get_layer_names(self) -> list[str]:
        """Gibt Liste aller verfügbaren Layer-Namen zurück."""
        ...

    def get_layer_channel_count(self, layer_name: str) -> int:
        """Gibt die Anzahl der Channels fuer einen Layer zurueck.

        Args:
            layer_name: Name des Layers

        Returns:
            Anzahl der Channels im Layer

        Raises:
            InvalidLayerError: Wenn layer_name ungueltig
        """
        ...

    def extract_layer_activations(
        self,
        image: np.ndarray,
        layer_name: str
    ) -> torch.Tensor:
        """Extrahiert Aktivierungen eines spezifischen Layers.

        Args:
            image: RGB-Bild (H, W, 3)
            layer_name: Name des Layers (z.B. 'layer1', 'layer2')

        Returns:
            Aktivierungs-Tensor (C, H, W) für gewählten Layer

        Raises:
            ValueError: Wenn layer_name ungültig
        """
        ...

    def get_top_predictions(self, k: int = 3) -> list[tuple[str, float]]:
        """Gibt Top-K Predictions des letzten Forward Pass zurueck.

        Args:
            k: Anzahl der Top-Predictions

        Returns:
            Liste von (Klassenname, Wahrscheinlichkeit) Tupeln
        """
        ...

    def compute_gradcam(self, image: np.ndarray, layer_name: str) -> np.ndarray:
        """Berechnet GradCAM-Heatmap fuer einen Layer.

        Args:
            image: RGB-Bild (H, W, 3)
            layer_name: Ziel-Layer fuer GradCAM (z.B. 'layer3', 'layer4')

        Returns:
            RGB-Overlay-Bild (H, W, 3) mit dtype uint8
        """
        ...

