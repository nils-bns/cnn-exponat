"""Unit Tests für PresetService."""

import pytest
from unittest.mock import Mock, MagicMock
from core.services.preset_service import PresetService
from core.models import ConfigData, LayerPresets, PresetConfig
from core.exceptions import InvalidPresetError


class TestPresetService:
    """Tests für PresetService."""

    def create_test_config(self):
        """Erstellt Test-Konfiguration."""
        preset1 = PresetConfig(
            preset_id=0,
            name="Preset 1",
            channels=[0, 1, 2],
            colormap="viridis",
            normalize=True,
            blend_mode="max"
        )
        preset2 = PresetConfig(
            preset_id=1,
            name="Preset 2",
            channels=[3, 4, 5],
            colormap="plasma",
            normalize=True,
            blend_mode="mean"
        )

        layer_presets = LayerPresets(
            layer_name="layer1",
            presets=[preset1, preset2],
            active_preset_id=0
        )

        config = ConfigData(
            presets={"layer1": layer_presets}
        )

        return config

    def test_init(self):
        """Test: Initialisierung."""
        # Arrange
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = self.create_test_config()

        # Act
        service = PresetService(mock_config_manager)

        # Assert
        assert service._config_manager is mock_config_manager
        mock_config_manager.load_config.assert_called_once()

    def test_get_preset_valid(self):
        """Test: Hole gültiges Preset."""
        # Arrange
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = self.create_test_config()
        service = PresetService(mock_config_manager)

        # Act
        preset = service.get_preset("layer1", 0)

        # Assert
        assert preset.preset_id == 0
        assert preset.name == "Preset 1"
        assert preset.channels == [0, 1, 2]

    def test_get_preset_invalid_layer(self):
        """Test: Ungültiger Layer."""
        # Arrange
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = self.create_test_config()
        service = PresetService(mock_config_manager)

        # Act & Assert
        with pytest.raises(ValueError, match="Ungültiger Layer"):
            service.get_preset("invalid_layer", 0)

    def test_get_preset_invalid_id(self):
        """Test: Ungültige Preset-ID."""
        # Arrange
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = self.create_test_config()
        service = PresetService(mock_config_manager)

        # Act & Assert
        with pytest.raises(ValueError, match="preset_id muss 0, 1 oder 2 sein"):
            service.get_preset("layer1", 5)

    def test_get_preset_not_found(self):
        """Test: Preset existiert nicht."""
        # Arrange
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = self.create_test_config()
        service = PresetService(mock_config_manager)

        # Act & Assert
        with pytest.raises(InvalidPresetError):
            service.get_preset("layer1", 2)  # Nur 0 und 1 existieren

    def test_get_active_preset(self):
        """Test: Hole aktives Preset."""
        # Arrange
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = self.create_test_config()
        service = PresetService(mock_config_manager)

        # Act
        preset = service.get_active_preset("layer1")

        # Assert
        assert preset.preset_id == 0
        assert preset.name == "Preset 1"

    def test_set_active_preset(self):
        """Test: Setze aktives Preset."""
        # Arrange
        mock_config_manager = Mock()
        config = self.create_test_config()
        mock_config_manager.load_config.return_value = config
        service = PresetService(mock_config_manager)

        # Act
        service.set_active_preset("layer1", 1)

        # Assert
        assert config.presets["layer1"].active_preset_id == 1
        mock_config_manager.save_config.assert_called_once_with(config)

    def test_save_preset_update_existing(self):
        """Test: Aktualisiere existierendes Preset."""
        # Arrange
        mock_config_manager = Mock()
        config = self.create_test_config()
        mock_config_manager.load_config.return_value = config
        service = PresetService(mock_config_manager)

        new_preset = PresetConfig(
            preset_id=0,
            name="Updated Preset",
            channels=[10, 20],
            colormap="hot",
            normalize=False,
            blend_mode="overlay"
        )

        # Act
        service.save_preset("layer1", 0, new_preset)

        # Assert
        saved_preset = config.presets["layer1"].presets[0]
        assert saved_preset.name == "Updated Preset"
        assert saved_preset.channels == [10, 20]
        mock_config_manager.save_config.assert_called_once()

    def test_save_preset_add_new(self):
        """Test: Füge neues Preset hinzu."""
        # Arrange
        mock_config_manager = Mock()
        config = self.create_test_config()
        mock_config_manager.load_config.return_value = config
        service = PresetService(mock_config_manager)

        new_preset = PresetConfig(
            preset_id=2,
            name="New Preset",
            channels=[6, 7, 8],
            colormap="inferno",
            normalize=True,
            blend_mode="max"
        )

        # Act
        service.save_preset("layer1", 2, new_preset)

        # Assert
        assert len(config.presets["layer1"].presets) == 3
        assert config.presets["layer1"].presets[2].name == "New Preset"
        mock_config_manager.save_config.assert_called_once()

    def test_save_preset_max_limit(self):
        """Test: Maximale Anzahl Presets - preset_id wird validiert."""
        # Arrange
        mock_config_manager = Mock()
        config = self.create_test_config()

        # Füge drittes Preset hinzu (ID 2)
        preset3 = PresetConfig(
            preset_id=2,
            name="Preset 3",
            channels=[6, 7],
            colormap="hot"
        )
        config.presets["layer1"].presets.append(preset3)

        mock_config_manager.load_config.return_value = config
        service = PresetService(mock_config_manager)

        # Versuche, mit ungültiger preset_id zu speichern (3 ist ungültig, nur 0-2 erlaubt)
        # Act & Assert - Service sollte ValueError werfen bei ungültiger preset_id
        with pytest.raises(ValueError, match="preset_id muss 0, 1 oder 2 sein"):
            # Direkter Aufruf mit ungültiger ID - Service validiert die ID
            service.save_preset("layer1", 3, preset3)  # preset_id=3 ist ungültig

    def test_get_all_presets_for_layer(self):
        """Test: Hole alle Presets für Layer."""
        # Arrange
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = self.create_test_config()
        service = PresetService(mock_config_manager)

        # Act
        presets = service.get_all_presets_for_layer("layer1")

        # Assert
        assert len(presets) == 2
        assert presets[0].name == "Preset 1"
        assert presets[1].name == "Preset 2"

