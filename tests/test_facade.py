"""Tests für ApplicationFacade."""

import pytest
import numpy as np
import torch
from unittest.mock import Mock

from core.facade import ApplicationFacade
from core.models import PresetConfig
from core.exceptions import CameraFrameError


class TestApplicationFacadeInitialization:
    """Tests für Facade-Initialisierung."""

    def test_facade_creation_with_dependencies(self):
        """Test: Facade wird mit allen Dependencies erstellt."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_visualization = Mock()
        mock_presets = Mock()

        # Act
        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Assert
        assert facade._camera == mock_camera
        assert facade._model == mock_model
        assert facade._visualization == mock_visualization
        assert facade._presets == mock_presets
        assert facade._current_layer is None

    def test_initialize_loads_model_and_starts_camera(self):
        """Test: initialize() lädt Modell und startet Kamera."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_model.get_layer_names.return_value = ['layer1', 'layer2']
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        facade.initialize()

        # Assert
        mock_model.load_model.assert_called_once()
        mock_camera.start.assert_called_once()
        assert facade._current_layer == 'layer1'

    def test_initialize_sets_first_layer_as_current(self):
        """Test: initialize() setzt ersten Layer als aktuell."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_model.get_layer_names.return_value = ['conv1', 'layer1', 'layer2']
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        facade.initialize()

        # Assert
        assert facade._current_layer == 'conv1'


class TestApplicationFacadeVisualizationWorkflow:
    """Tests für kompletten Visualisierungs-Workflow."""

    def test_get_visualization_for_layer_complete_workflow(self):
        """Test: get_visualization_for_layer() orchestriert alle Services."""
        # Arrange
        mock_camera = Mock()
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera.get_frame.return_value = mock_frame

        mock_model = Mock()
        mock_activations = torch.randn(64, 56, 56)
        mock_model.extract_layer_activations.return_value = mock_activations

        mock_preset = PresetConfig(
            preset_id=0,
            name="Test Preset",
            channels=[0, 1, 2],
            colormap="viridis",
            normalize=True,
            blend_mode="mean"
        )
        mock_presets = Mock()
        mock_presets.get_active_preset.return_value = mock_preset

        mock_visualization = Mock()
        mock_vis_result = np.zeros((600, 800, 3), dtype=np.uint8)
        mock_visualization.visualize.return_value = mock_vis_result

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        result = facade.get_visualization_for_layer('layer1')

        # Assert
        mock_camera.get_frame.assert_called_once()
        mock_model.extract_layer_activations.assert_called_once_with(mock_frame, 'layer1')
        mock_presets.get_active_preset.assert_called_once_with('layer1')
        mock_visualization.visualize.assert_called_once_with(mock_activations, mock_preset)
        assert np.array_equal(result, mock_vis_result)

    def test_get_visualization_for_layer_propagates_exceptions(self):
        """Test: get_visualization_for_layer() propagiert Exceptions."""
        # Arrange
        mock_camera = Mock()
        mock_camera.get_frame.side_effect = CameraFrameError("Kamera-Fehler")
        mock_model = Mock()
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act & Assert
        with pytest.raises(CameraFrameError):
            facade.get_visualization_for_layer('layer1')


class TestApplicationFacadeLayerManagement:
    """Tests für Layer-Management."""

    def test_change_layer_updates_current_layer(self):
        """Test: change_layer() aktualisiert aktuellen Layer."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_model.get_layer_names.return_value = ['layer1', 'layer2', 'layer3']
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        facade.change_layer('layer2')

        # Assert
        assert facade._current_layer == 'layer2'

    def test_change_layer_raises_error_for_invalid_layer(self):
        """Test: change_layer() wirft Fehler bei ungültigem Layer."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_model.get_layer_names.return_value = ['layer1', 'layer2']
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Ungültiger Layer"):
            facade.change_layer('invalid_layer')

    def test_get_current_layer_returns_current_layer(self):
        """Test: get_current_layer() gibt aktuellen Layer zurück."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_model.get_layer_names.return_value = ['layer1', 'layer2']
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        facade._current_layer = 'layer1'

        # Act
        result = facade.get_current_layer()

        # Assert
        assert result == 'layer1'

    def test_get_layer_names_delegates_to_model_service(self):
        """Test: get_layer_names() delegiert an ModelService."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_model.get_layer_names.return_value = ['conv1', 'layer1', 'layer2', 'layer3', 'layer4']
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        result = facade.get_layer_names()

        # Assert
        assert result == ['conv1', 'layer1', 'layer2', 'layer3', 'layer4']
        mock_model.get_layer_names.assert_called_once()


class TestApplicationFacadePresetManagement:
    """Tests für Preset-Delegationsmethoden."""

    def test_save_preset_delegates_to_preset_service(self):
        """Test: save_preset() delegiert an PresetService."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        preset = PresetConfig(
            preset_id=1,
            name="New Preset",
            channels=[0, 1],
            colormap="plasma",
            normalize=True,
            blend_mode="max"
        )

        # Act
        facade.save_preset('layer1', 1, preset)

        # Assert
        mock_presets.save_preset.assert_called_once_with('layer1', 1, preset)

    def test_get_all_presets_for_layer_delegates_to_preset_service(self):
        """Test: get_all_presets_for_layer() delegiert an PresetService."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_visualization = Mock()
        mock_presets = Mock()

        expected_presets = [
            PresetConfig(0, "Preset 0", [0], "viridis", True, "mean"),
            PresetConfig(1, "Preset 1", [1], "plasma", True, "max"),
            PresetConfig(2, "Preset 2", [2], "inferno", True, "overlay")
        ]
        mock_presets.get_all_presets_for_layer.return_value = expected_presets

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        result = facade.get_all_presets_for_layer('layer2')

        # Assert
        assert result == expected_presets
        mock_presets.get_all_presets_for_layer.assert_called_once_with('layer2')

    def test_set_active_preset_delegates_to_preset_service(self):
        """Test: set_active_preset() delegiert an PresetService."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        facade.set_active_preset('layer3', 2)

        # Assert
        mock_presets.set_active_preset.assert_called_once_with('layer3', 2)


class TestApplicationFacadePredictions:
    """Tests fuer Facade Predictions-Delegation."""

    def test_get_top_predictions_delegates_to_model_service(self):
        """Test: get_top_predictions() delegiert an ModelService."""
        # Arrange
        mock_model = Mock()
        expected = [("tabby", 0.85), ("tiger_cat", 0.10), ("Egyptian_cat", 0.03)]
        mock_model.get_top_predictions.return_value = expected

        facade = ApplicationFacade(
            camera=Mock(), model=mock_model,
            visualization=Mock(), presets=Mock()
        )

        # Act
        result = facade.get_top_predictions(k=3)

        # Assert
        assert result == expected
        mock_model.get_top_predictions.assert_called_once_with(3)

    def test_get_top_predictions_uses_default_k(self):
        """Test: get_top_predictions() nutzt Default k=3."""
        # Arrange
        mock_model = Mock()
        mock_model.get_top_predictions.return_value = []

        facade = ApplicationFacade(
            camera=Mock(), model=mock_model,
            visualization=Mock(), presets=Mock()
        )

        # Act
        facade.get_top_predictions()

        # Assert
        mock_model.get_top_predictions.assert_called_once_with(3)


class TestApplicationFacadeShutdown:
    """Tests für Shutdown-Prozess."""

    def test_shutdown_stops_camera(self):
        """Test: shutdown() stoppt Kamera."""
        # Arrange
        mock_camera = Mock()
        mock_model = Mock()
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        facade.shutdown()

        # Assert
        mock_camera.stop.assert_called_once()

    def test_shutdown_handles_camera_stop_errors_gracefully(self):
        """Test: shutdown() behandelt Kamera-Fehler graceful."""
        # Arrange
        mock_camera = Mock()
        mock_camera.stop.side_effect = Exception("Kamera-Fehler")
        mock_model = Mock()
        mock_visualization = Mock()
        mock_presets = Mock()

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act - sollte nicht crashen
        facade.shutdown()

        # Assert
        mock_camera.stop.assert_called_once()


class TestApplicationFacadeIntegration:
    """Integration-Tests mit realistischeren Szenarien."""

    def test_full_lifecycle_initialize_visualize_shutdown(self):
        """Test: Kompletter Lifecycle - Initialize → Visualize → Shutdown."""
        # Arrange
        mock_camera = Mock()
        mock_camera.get_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

        mock_model = Mock()
        mock_model.get_layer_names.return_value = ['layer1', 'layer2']
        mock_model.extract_layer_activations.return_value = torch.randn(64, 56, 56)

        mock_preset = PresetConfig(0, "Test", [0], "viridis", True, "mean")
        mock_presets = Mock()
        mock_presets.get_active_preset.return_value = mock_preset

        mock_visualization = Mock()
        mock_visualization.visualize.return_value = np.zeros((600, 800, 3), dtype=np.uint8)

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        facade.initialize()
        vis_result = facade.get_visualization_for_layer('layer1')
        facade.change_layer('layer2')
        vis_result2 = facade.get_visualization_for_layer('layer2')
        facade.shutdown()

        # Assert
        mock_model.load_model.assert_called_once()
        mock_camera.start.assert_called_once()
        assert mock_camera.get_frame.call_count == 2
        assert mock_model.extract_layer_activations.call_count == 2
        mock_camera.stop.assert_called_once()
        assert facade._current_layer == 'layer2'

    def test_multiple_visualizations_same_layer(self):
        """Test: Mehrere Visualisierungen für denselben Layer."""
        # Arrange
        mock_camera = Mock()
        mock_camera.get_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

        mock_model = Mock()
        mock_model.extract_layer_activations.return_value = torch.randn(64, 56, 56)

        mock_preset = PresetConfig(0, "Test", [0], "viridis", True, "mean")
        mock_presets = Mock()
        mock_presets.get_active_preset.return_value = mock_preset

        mock_visualization = Mock()
        mock_visualization.visualize.return_value = np.zeros((600, 800, 3), dtype=np.uint8)

        facade = ApplicationFacade(
            camera=mock_camera,
            model=mock_model,
            visualization=mock_visualization,
            presets=mock_presets
        )

        # Act
        for _ in range(5):
            facade.get_visualization_for_layer('layer1')

        # Assert
        assert mock_camera.get_frame.call_count == 5
        assert mock_model.extract_layer_activations.call_count == 5
        assert mock_presets.get_active_preset.call_count == 5
        assert mock_visualization.visualize.call_count == 5

