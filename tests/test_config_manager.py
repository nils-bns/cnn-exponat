"""Unit tests for ConfigManager."""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from storage.config_manager import ConfigManager
from core.models import ConfigData, LayerPresets, PresetConfig
from core.exceptions import ConfigLoadError, ConfigSaveError


class TestConfigManager:
    """Tests für ConfigManager."""

    def test_init(self):
        """Test: ConfigManager-Initialisierung."""
        manager = ConfigManager("test_config.json")
        assert manager._config_path == Path("test_config.json")

    def test_load_config_creates_default_when_missing(self, tmp_path):
        """Test: Default-Config wird erstellt wenn Datei fehlt."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path)

        config = manager.load_config()

        # Config sollte erstellt worden sein
        assert config_path.exists()
        assert isinstance(config, ConfigData)
        assert config.version == "1.0"

        # Alle Layer sollten vorhanden sein
        assert "conv1" in config.presets
        assert "layer1" in config.presets
        assert "layer2" in config.presets
        assert "layer3" in config.presets
        assert "layer4" in config.presets

    def test_save_and_load_config(self, tmp_path):
        """Test: Config speichern und wieder laden."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path)

        # Erstelle Test-Config
        test_config = ConfigData(
            version="1.0",
            presets={
                "layer1": LayerPresets(
                    layer_name="layer1",
                    presets=[
                        PresetConfig(
                            preset_id=0,
                            name="Test Preset",
                            channels=[0, 1, 2],
                            colormap="viridis",
                            normalize=True,
                            blend_mode="max"
                        )
                    ],
                    active_preset_id=0
                )
            }
        )

        # Speichern
        manager.save_config(test_config)
        assert config_path.exists()

        # Laden
        loaded_config = manager.load_config()

        # Vergleichen
        assert loaded_config.version == test_config.version
        assert "layer1" in loaded_config.presets
        layer1 = loaded_config.presets["layer1"]
        assert layer1.layer_name == "layer1"
        assert len(layer1.presets) == 1
        assert layer1.presets[0].name == "Test Preset"
        assert layer1.presets[0].channels == [0, 1, 2]

    def test_load_invalid_json(self, tmp_path):
        """Test: Fehlerbehandlung bei ungültigem JSON."""
        config_path = tmp_path / "invalid.json"
        config_path.write_text("{ invalid json }", encoding='utf-8')

        manager = ConfigManager(config_path)

        with pytest.raises(ConfigLoadError):
            manager.load_config()

    def test_serialize_deserialize_complete_config(self, tmp_path):
        """Test: Vollständige Serialisierung/Deserialisierung."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path)

        # Lade Default-Config
        original_config = manager.load_config()

        # Speichere und lade erneut
        manager.save_config(original_config)
        loaded_config = manager.load_config()

        # Vergleiche alle Layer
        for layer_name in ["conv1", "layer1", "layer2", "layer3", "layer4"]:
            assert layer_name in loaded_config.presets
            original_layer = original_config.presets[layer_name]
            loaded_layer = loaded_config.presets[layer_name]

            assert loaded_layer.layer_name == original_layer.layer_name
            assert loaded_layer.active_preset_id == original_layer.active_preset_id
            assert len(loaded_layer.presets) == len(original_layer.presets)

            # Vergleiche Presets
            for i, (orig_preset, loaded_preset) in enumerate(
                zip(original_layer.presets, loaded_layer.presets)
            ):
                assert loaded_preset.preset_id == orig_preset.preset_id
                assert loaded_preset.name == orig_preset.name
                assert loaded_preset.channels == orig_preset.channels
                assert loaded_preset.colormap == orig_preset.colormap
                assert loaded_preset.normalize == orig_preset.normalize
                assert loaded_preset.blend_mode == orig_preset.blend_mode

    def test_config_persistence_without_ui_layout(self, tmp_path):
        """Test: Config kann ohne ui_layout gespeichert und geladen werden."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path)

        config = manager.load_config()

        # Config sollte kein ui_layout haben
        assert not hasattr(config, 'ui_layout')
        assert config.presets is not None
        assert len(config.presets) == 5

    def test_preset_validation(self):
        """Test: Preset-Validierung bei ungültigen Daten."""
        # Ungültige preset_id
        with pytest.raises(ValueError):
            PresetConfig(
                preset_id=5,  # Ungültig
                name="Test",
                channels=[0]
            )

        # Keine Channels
        with pytest.raises(ValueError):
            PresetConfig(
                preset_id=0,
                name="Test",
                channels=[]  # Leer
            )

        # Ungültiger blend_mode
        with pytest.raises(ValueError):
            PresetConfig(
                preset_id=0,
                name="Test",
                channels=[0],
                blend_mode="invalid"
            )

    def test_layer_presets_validation(self):
        """Test: LayerPresets-Validierung."""
        # Zu viele Presets
        with pytest.raises(ValueError):
            LayerPresets(
                layer_name="layer1",
                presets=[
                    PresetConfig(preset_id=0, name="P1", channels=[0]),
                    PresetConfig(preset_id=1, name="P2", channels=[0]),
                    PresetConfig(preset_id=2, name="P3", channels=[0]),
                    PresetConfig(preset_id=0, name="P4", channels=[0]),  # 4. Preset
                ]
            )

        # Ungültige active_preset_id
        with pytest.raises(ValueError):
            LayerPresets(
                layer_name="layer1",
                presets=[],
                active_preset_id=5  # Ungültig
            )

    def test_atomic_save(self, tmp_path):
        """Test: Atomares Speichern verhindert korrupte Dateien."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path)

        # Erstelle initiale Config
        config = manager.load_config()

        # Simuliere mehrfaches Speichern
        for i in range(5):
            config.version = f"1.{i}"
            manager.save_config(config)

            # Prüfe dass Datei nach jedem Speichern valide ist
            with open(config_path, 'r', encoding='utf-8') as f:
                json.load(f)  # Sollte nicht fehlschlagen


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

