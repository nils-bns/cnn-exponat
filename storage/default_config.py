"""Default configuration for CNN Visualization application.

This module provides the default configuration with presets for all ResNet18 layers.
"""

from core.models import (
    ConfigData,
    LayerPresets,
    PresetConfig,
)


def get_default_config() -> ConfigData:
    """Erstellt die Standard-Konfiguration.

    Returns:
        ConfigData-Objekt mit allen Default-Werten und Presets
    """

    # Presets für conv1 (64 channels)
    conv1_presets = LayerPresets(
        layer_name="conv1",
        presets=[
            PresetConfig(
                preset_id=0,
                name="Edge Detection",
                channels=[17, 20, 20],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="rgb"
            ),
            PresetConfig(
                preset_id=1,
                name="Color Channels",
                channels=[5, 6, 11],
                colormap="inferno",
                normalize=True,
                blend_mode="max",
                visualization_mode="colormap"
            ),
            PresetConfig(
                preset_id=2,
                name="High Frequency",
                channels=[55, 28, 4],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="rgb"
            )
        ],
        active_preset_id=0
    )

    # Presets für layer1 (64 channels)
    layer1_presets = LayerPresets(
        layer_name="layer1",
        presets=[
            PresetConfig(
                preset_id=0,
                name="Low-Level Features",
                channels=[7, -1, -1],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="colormap"
            ),
            PresetConfig(
                preset_id=1,
                name="Texture Patterns",
                channels=[7, 16, 17],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="rgb"
            ),
            PresetConfig(
                preset_id=2,
                name="Combined View",
                channels=[0, 15, 30],
                colormap="viridis",
                normalize=True,
                blend_mode="overlay",
                visualization_mode="colormap"
            )
        ],
        active_preset_id=0
    )

    # Presets für layer2 (128 channels)
    layer2_presets = LayerPresets(
        layer_name="layer2",
        presets=[
            PresetConfig(
                preset_id=0,
                name="Shape Detection",
                channels=[80, -1, -1],
                colormap="inferno",
                normalize=True,
                blend_mode="max",
                visualization_mode="colormap"
            ),
            PresetConfig(
                preset_id=1,
                name="Mid-Level Features",
                channels=[10, 42, 87],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="rgb"
            ),
            PresetConfig(
                preset_id=2,
                name="Complex Patterns",
                channels=[90, 100, 110],
                colormap="inferno",
                normalize=True,
                blend_mode="overlay",
                visualization_mode="colormap"
            )
        ],
        active_preset_id=0
    )

    # Presets für layer3 (256 channels)
    layer3_presets = LayerPresets(
        layer_name="layer3",
        presets=[
            PresetConfig(
                preset_id=0,
                name="Object Parts",
                channels=[23, 47, 86],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="colormap"
            ),
            PresetConfig(
                preset_id=1,
                name="High-Level Features",
                channels=[134, 181, 75],
                colormap="magma",
                normalize=False,
                blend_mode="overlay",
                visualization_mode="colormap"
            ),
            PresetConfig(
                preset_id=2,
                name="Abstract Patterns",
                channels=[200, 220, 240],
                colormap="magma",
                normalize=True,
                blend_mode="overlay",
                visualization_mode="colormap"
            )
        ],
        active_preset_id=0
    )

    # Presets für layer4 (512 channels)
    layer4_presets = LayerPresets(
        layer_name="layer4",
        presets=[
            PresetConfig(
                preset_id=0,
                name="Object Recognition",
                channels=[0, 50, 100],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="colormap"
            ),
            PresetConfig(
                preset_id=1,
                name="Abstract Representations",
                channels=[21, 40, 47],
                colormap="viridis",
                normalize=True,
                blend_mode="max",
                visualization_mode="rgb"
            ),
            PresetConfig(
                preset_id=2,
                name="Final Features",
                channels=[450, 475, 500],
                colormap="inferno",
                normalize=True,
                blend_mode="overlay",
                visualization_mode="colormap"
            )
        ],
        active_preset_id=0
    )

    # Gesamt-Konfiguration
    config = ConfigData(
        version="1.0",
        presets={
            "conv1": conv1_presets,
            "layer1": layer1_presets,
            "layer2": layer2_presets,
            "layer3": layer3_presets,
            "layer4": layer4_presets
        }
    )

    return config

