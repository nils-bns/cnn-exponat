"""Unit tests for default configuration."""

import pytest
from storage.default_config import get_default_config
from core.models import ConfigData, LayerPresets, PresetConfig


class TestDefaultConfig:
    """Tests für Default-Konfiguration."""

    def test_get_default_config_returns_config_data(self):
        """Test: get_default_config gibt ConfigData zurück."""
        config = get_default_config()
        assert isinstance(config, ConfigData)
        assert config.version == "1.0"

    def test_all_layers_present(self):
        """Test: Alle ResNet18-Layer sind vorhanden."""
        config = get_default_config()
        required_layers = ['conv1', 'layer1', 'layer2', 'layer3', 'layer4']

        for layer in required_layers:
            assert layer in config.presets, f"Layer {layer} fehlt"
            assert isinstance(config.presets[layer], LayerPresets)

    def test_each_layer_has_three_presets(self):
        """Test: Jeder Layer hat 3 Presets."""
        config = get_default_config()

        for layer_name, layer_presets in config.presets.items():
            assert len(layer_presets.presets) == 3, \
                f"Layer {layer_name} hat {len(layer_presets.presets)} Presets statt 3"

            # Prüfe Preset-IDs
            preset_ids = [p.preset_id for p in layer_presets.presets]
            assert preset_ids == [0, 1, 2], \
                f"Layer {layer_name} hat ungültige Preset-IDs: {preset_ids}"

    def test_presets_are_valid(self):
        """Test: Alle Presets sind valide."""
        config = get_default_config()

        for layer_name, layer_presets in config.presets.items():
            for preset in layer_presets.presets:
                # Validierung durch PresetConfig.__post_init__
                assert isinstance(preset, PresetConfig)
                assert preset.preset_id in [0, 1, 2]
                assert len(preset.channels) > 0
                assert preset.name != ""
                assert preset.colormap in ['viridis', 'plasma', 'inferno', 'magma', 'jet', 'hot']
                assert preset.blend_mode in ['max', 'mean', 'overlay']

    def test_active_preset_is_zero(self):
        """Test: Aktives Preset ist standardmäßig 0."""
        config = get_default_config()

        for layer_name, layer_presets in config.presets.items():
            assert layer_presets.active_preset_id == 0, \
                f"Layer {layer_name} hat active_preset_id {layer_presets.active_preset_id}"

    def test_config_structure(self):
        """Test: Config hat presets, aber kein ui_layout oder ui_texts."""
        config = get_default_config()
        assert config.presets is not None
        assert len(config.presets) == 5
        assert not hasattr(config, 'ui_layout')
        assert not hasattr(config, 'ui_texts')

    def test_conv1_channel_count(self):
        """Test: conv1 hat angemessene Channel-Auswahl (64 channels verfügbar)."""
        config = get_default_config()
        conv1 = config.presets['conv1']

        for preset in conv1.presets:
            # Alle Channels sollten < 64 sein
            for channel in preset.channels:
                assert 0 <= channel < 64, \
                    f"conv1 Preset {preset.name} hat ungültigen Channel {channel}"

    def test_layer4_channel_count(self):
        """Test: layer4 hat angemessene Channel-Auswahl (512 channels verfügbar)."""
        config = get_default_config()
        layer4 = config.presets['layer4']

        for preset in layer4.presets:
            # Alle Channels sollten < 512 sein
            for channel in preset.channels:
                assert 0 <= channel < 512, \
                    f"layer4 Preset {preset.name} hat ungültigen Channel {channel}"

    def test_preset_names_are_descriptive(self):
        """Test: Preset-Namen sind beschreibend (nicht leer)."""
        config = get_default_config()

        for layer_name, layer_presets in config.presets.items():
            names = [p.name for p in layer_presets.presets]

            # Alle Namen sollten einzigartig sein
            assert len(names) == len(set(names)), \
                f"Layer {layer_name} hat doppelte Preset-Namen"

            # Alle Namen sollten nicht leer sein
            for name in names:
                assert len(name) > 0, \
                    f"Layer {layer_name} hat leeren Preset-Namen"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

