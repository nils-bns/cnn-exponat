"""Data models for CNN Visualization application.

This module contains all dataclasses representing the application's data structures.
"""

from dataclasses import dataclass, field


@dataclass
class PresetConfig:
    """Konfiguration für ein Visualisierungs-Preset.

    Attributes:
        preset_id: ID des Presets (0, 1 oder 2)
        name: Anzeigename des Presets
        channels: Liste der zu visualisierenden Channel-Indizes
        colormap: Name der Matplotlib-Colormap (z.B. 'viridis', 'plasma') oder 'custom'
        normalize: Ob die Aktivierungen normalisiert werden sollen
        blend_mode: Wie mehrere Channels kombiniert werden ('max', 'mean', 'overlay')
        visualization_mode: Visualisierungsmodus ('colormap' oder 'rgb')
    """

    preset_id: int
    name: str
    channels: list[int]
    colormap: str = "viridis"
    normalize: bool = True
    blend_mode: str = "max"
    visualization_mode: str = "colormap"

    def __post_init__(self):
        """Validierung der Preset-Daten."""
        if self.preset_id not in [0, 1, 2]:
            raise ValueError("preset_id muss 0, 1 oder 2 sein")
        if not self.channels:
            raise ValueError("Mindestens ein Channel erforderlich")
        # Mindestens ein gültiger Channel (nicht -1) erforderlich
        valid_channels = [c for c in self.channels if c != -1]
        if not valid_channels:
            raise ValueError("Mindestens ein gültiger Channel (nicht -1) erforderlich")
        if self.blend_mode not in ['max', 'mean', 'overlay']:
            raise ValueError("blend_mode muss 'max', 'mean' oder 'overlay' sein")

        # Validierung visualization_mode
        if self.visualization_mode not in ["colormap", "rgb"]:
            raise ValueError(
                f"visualization_mode muss 'colormap' oder 'rgb' sein, "
                f"ist: {self.visualization_mode}"
            )

        # Im RGB-Mode müssen genau 3 Channels angegeben sein
        if self.visualization_mode == "rgb" and len(self.channels) != 3:
            raise ValueError(
                f"RGB-Mode benötigt genau 3 Channels (R, G, B), "
                f"hat: {len(self.channels)}"
            )


@dataclass
class LayerPresets:
    """Alle Presets für einen Layer.

    Attributes:
        layer_name: Name des ResNet18-Layers (z.B. 'layer1', 'layer2')
        presets: Liste von bis zu 3 Presets
        active_preset_id: ID des aktuell aktiven Presets
    """

    layer_name: str
    presets: list[PresetConfig] = field(default_factory=list)
    active_preset_id: int = 0

    def __post_init__(self):
        """Validierung."""
        if len(self.presets) > 3:
            raise ValueError("Maximal 3 Presets pro Layer erlaubt")
        if self.active_preset_id not in [0, 1, 2]:
            raise ValueError("active_preset_id muss 0, 1 oder 2 sein")


@dataclass
class ConfigData:
    """Gesamt-Konfiguration (entspricht config.json).

    Attributes:
        version: Versions-String der Konfiguration
        presets: Dictionary mit Layer-Namen als Keys und LayerPresets als Values
    """

    presets: dict[str, LayerPresets] = field(default_factory=dict)
    version: str = "1.0"

