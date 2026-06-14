"""PresetConfig-Erstellung aus UI-State.

Konsolidiert die duplizierte PresetConfig-Logik aus
_on_param_changed() und _save_current_preset().
"""

import logging
from core.models import PresetConfig


logger = logging.getLogger(__name__)


class PresetBuilder:
    """Baut PresetConfig aus UI-Werten. Eliminiert Code-Duplikat.

    Stateless Helper - nur @staticmethod, kein __init__, keine Instanz.
    Greift NICHT auf UI-Widgets zu. Alle Werte kommen als Parameter.
    """

    @staticmethod
    def build_from_ui(
        preset_id: int,
        name: str,
        is_rgb_mode: bool,
        channels: list[int],
        rgb_channels: list[int],
        colormap: str,
        normalize: bool,
        blend_mode: str,
    ) -> PresetConfig:
        """Erstellt PresetConfig basierend auf Mode und UI-Werten.

        Im RGB-Mode werden normalize, blend_mode und colormap erzwungen.
        Im Colormap-Mode werden inaktive Channels (-1) herausgefiltert.

        Args:
            preset_id: Preset-Index (0, 1 oder 2)
            name: Anzeigename des Presets
            is_rgb_mode: True wenn RGB-Modus aktiv
            channels: Colormap-Channel-Werte (kann -1 enthalten)
            rgb_channels: RGB-Channel-Werte (genau 3)
            colormap: Gewaehlte Colormap (z.B. "viridis")
            normalize: Normalisierung aktiviert
            blend_mode: Blend-Modus ("max", "mean", "overlay")

        Returns:
            Fertiges PresetConfig-Objekt
        """
        if is_rgb_mode:
            return PresetConfig(
                preset_id=preset_id,
                name=name,
                channels=rgb_channels,
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="rgb",
            )

        # Colormap-Mode: Inaktive Channels (-1) herausfiltern
        active_channels = [ch for ch in channels if ch != -1]

        return PresetConfig(
            preset_id=preset_id,
            name=name,
            channels=active_channels,
            colormap=colormap,
            normalize=normalize,
            blend_mode=blend_mode,
            visualization_mode="colormap",
        )
