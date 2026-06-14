"""Unit tests for data models."""

import pytest
from core.models import (
    PresetConfig,
    LayerPresets,
    ConfigData
)


class TestPresetConfig:
    """Tests für PresetConfig."""

    def test_valid_preset_config(self):
        """Test: Gültiges Preset."""
        preset = PresetConfig(
            preset_id=0,
            name="Test Preset",
            channels=[0, 1, 2],
            colormap="viridis",
            normalize=True,
            blend_mode="max"
        )
        assert preset.preset_id == 0
        assert preset.name == "Test Preset"
        assert preset.channels == [0, 1, 2]
        assert preset.colormap == "viridis"
        assert preset.normalize is True
        assert preset.blend_mode == "max"

    def test_preset_default_values(self):
        """Test: Default-Werte für optionale Parameter."""
        preset = PresetConfig(
            preset_id=1,
            name="Test",
            channels=[0]
        )
        assert preset.colormap == "viridis"
        assert preset.normalize is True
        assert preset.blend_mode == "max"

    def test_invalid_preset_id(self):
        """Test: Ungültige preset_id wird abgelehnt."""
        with pytest.raises(ValueError, match="preset_id muss 0, 1 oder 2 sein"):
            PresetConfig(
                preset_id=3,
                name="Test",
                channels=[0]
            )

    def test_empty_channels(self):
        """Test: Leere Channel-Liste wird abgelehnt."""
        with pytest.raises(ValueError, match="Mindestens ein Channel erforderlich"):
            PresetConfig(
                preset_id=0,
                name="Test",
                channels=[]
            )

    def test_invalid_blend_mode(self):
        """Test: Ungültiger blend_mode wird abgelehnt."""
        with pytest.raises(ValueError, match="blend_mode"):
            PresetConfig(
                preset_id=0,
                name="Test",
                channels=[0],
                blend_mode="invalid"
            )

    def test_preset_config_accepts_minus_one_channels(self):
        """Test: PresetConfig akzeptiert -1 als Channel-Wert."""
        preset = PresetConfig(
            preset_id=0,
            name="Test",
            channels=[0, -1, -1]
        )
        assert preset.channels == [0, -1, -1]

    def test_preset_config_accepts_mixed_channels(self):
        """Test: PresetConfig akzeptiert gemischte Channel-Liste."""
        preset = PresetConfig(
            preset_id=0,
            name="Mixed",
            channels=[5, -1, 10]
        )
        assert preset.channels == [5, -1, 10]

    def test_preset_config_accepts_single_valid_channel(self):
        """Test: PresetConfig akzeptiert Liste mit nur einem gültigen Channel."""
        preset = PresetConfig(
            preset_id=0,
            name="Single",
            channels=[42, -1, -1]
        )
        assert preset.channels == [42, -1, -1]

    def test_preset_config_rejects_only_minus_one_channels(self):
        """Test: PresetConfig lehnt Liste mit nur -1 Werten ab."""
        with pytest.raises(ValueError, match="Mindestens ein gültiger Channel"):
            PresetConfig(
                preset_id=0,
                name="Test",
                channels=[-1, -1, -1]
            )


class TestLayerPresets:
    """Tests für LayerPresets."""

    def test_valid_layer_presets(self):
        """Test: Gültiges LayerPresets-Objekt."""
        presets = [
            PresetConfig(preset_id=0, name="P1", channels=[0]),
            PresetConfig(preset_id=1, name="P2", channels=[1])
        ]
        layer = LayerPresets(
            layer_name="layer1",
            presets=presets,
            active_preset_id=0
        )
        assert layer.layer_name == "layer1"
        assert len(layer.presets) == 2
        assert layer.active_preset_id == 0

    def test_layer_presets_default_values(self):
        """Test: Default-Werte."""
        layer = LayerPresets(layer_name="layer1")
        assert layer.presets == []
        assert layer.active_preset_id == 0

    def test_too_many_presets(self):
        """Test: Maximal 3 Presets pro Layer."""
        presets = [
            PresetConfig(preset_id=0, name="P1", channels=[0]),
            PresetConfig(preset_id=1, name="P2", channels=[1]),
            PresetConfig(preset_id=2, name="P3", channels=[2]),
            PresetConfig(preset_id=0, name="P4", channels=[3])
        ]
        with pytest.raises(ValueError, match="Maximal 3 Presets pro Layer erlaubt"):
            LayerPresets(layer_name="layer1", presets=presets)

    def test_invalid_active_preset_id(self):
        """Test: Ungültige active_preset_id."""
        with pytest.raises(ValueError, match="active_preset_id"):
            LayerPresets(
                layer_name="layer1",
                active_preset_id=5
            )


class TestConfigData:
    """Tests für ConfigData."""

    def test_config_data_creation(self):
        """Test: ConfigData-Erstellung."""
        layer_presets = LayerPresets(
            layer_name="layer1",
            presets=[PresetConfig(preset_id=0, name="P1", channels=[0])]
        )
        config = ConfigData(
            version="1.0",
            presets={"layer1": layer_presets}
        )
        assert config.version == "1.0"
        assert "layer1" in config.presets

    def test_config_data_defaults(self):
        """Test: Default-Werte."""
        config = ConfigData()
        assert config.version == "1.0"
        assert config.presets == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

