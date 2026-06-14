"""Interface für Feature-Map-Visualisierung."""

from typing import Protocol
import numpy as np
import torch
from core.models import PresetConfig


class IVisualizationService(Protocol):
    """Interface für Feature-Map-Visualisierung."""

    def visualize(
        self,
        activations: torch.Tensor,
        preset: PresetConfig
    ) -> np.ndarray:
        """Transformiert Aktivierungen in visualisierbares Bild.

        Args:
            activations: Aktivierungs-Tensor (C, H, W)
            preset: Preset-Konfiguration

        Returns:
            RGB-Bild (H, W, 3) ready for display
        """
        ...

