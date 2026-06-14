"""Unit Tests für VisualizationService."""

import pytest
import numpy as np
import torch
from core.services.visualization_service import VisualizationService
from core.models import PresetConfig


class TestVisualizationService:
    """Tests für VisualizationService."""

    def test_init(self):
        """Test: Initialisierung."""
        service = VisualizationService()
        assert service is not None

    def test_visualize_basic(self):
        """Test: Basis-Visualisierung."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(64, 56, 56)  # (C, H, W)
        preset = PresetConfig(
            preset_id=0,
            name="Test",
            channels=[0, 1, 2],
            colormap="viridis",
            normalize=True,
            blend_mode="max"
        )

        # Act
        result = service.visualize(activations, preset)

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.shape == (service.DISPLAY_HEIGHT, service.DISPLAY_WIDTH, 3)
        assert result.dtype == np.uint8

    def test_select_channels_valid(self):
        """Test: Channel-Auswahl mit gültigen Channels."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(10, 56, 56)
        channels = [0, 3, 7]

        # Act
        result = service._select_channels(activations, channels)

        # Assert
        assert result.shape == (3, 56, 56)

    def test_select_channels_invalid(self):
        """Test: Channel-Auswahl mit ungültigen Channels."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(10, 56, 56)
        channels = [15, 20, 100]  # Alle > 10

        # Act
        result = service._select_channels(activations, channels)

        # Assert - Fallback auf Channel 0
        assert result.shape == (1, 56, 56)

    def test_blend_channels_max(self):
        """Test: Max-Blending."""
        # Arrange
        service = VisualizationService()
        channels = torch.tensor([
            [[1.0, 2.0], [3.0, 4.0]],
            [[5.0, 6.0], [7.0, 8.0]]
        ])

        # Act
        result = service._blend_channels(channels, "max")

        # Assert
        expected = torch.tensor([[5.0, 6.0], [7.0, 8.0]])
        assert torch.allclose(result, expected)

    def test_blend_channels_mean(self):
        """Test: Mean-Blending."""
        # Arrange
        service = VisualizationService()
        channels = torch.tensor([
            [[1.0, 2.0], [3.0, 4.0]],
            [[5.0, 6.0], [7.0, 8.0]]
        ])

        # Act
        result = service._blend_channels(channels, "mean")

        # Assert
        expected = torch.tensor([[3.0, 4.0], [5.0, 6.0]])
        assert torch.allclose(result, expected)

    def test_normalize(self):
        """Test: Normalisierung."""
        # Arrange
        service = VisualizationService()
        tensor = torch.tensor([[1.0, 5.0], [3.0, 9.0]])

        # Act
        result = service._normalize(tensor)

        # Assert
        assert result.min() == 0.0
        assert result.max() == 1.0
        assert torch.allclose(result, torch.tensor([[0.0, 0.5], [0.25, 1.0]]))

    def test_normalize_constant_tensor(self):
        """Test: Normalisierung eines konstanten Tensors."""
        # Arrange
        service = VisualizationService()
        tensor = torch.ones(3, 3) * 5.0

        # Act
        result = service._normalize(tensor)

        # Assert - Bei konstantem Tensor → Nullen
        assert torch.all(result == 0.0)

    def test_apply_colormap_viridis(self):
        """Test: Colormap-Anwendung."""
        # Arrange
        service = VisualizationService()
        grayscale = np.array([[0.0, 0.5], [0.7, 1.0]])

        # Act
        result = service._apply_colormap(grayscale, "viridis")

        # Assert
        assert result.shape == (2, 2, 3)
        assert result.dtype == np.uint8
        assert result.min() >= 0
        assert result.max() <= 255

    def test_apply_colormap_invalid(self):
        """Test: Ungültige Colormap → Fallback."""
        # Arrange
        service = VisualizationService()
        grayscale = np.array([[0.0, 1.0]])

        # Act
        result = service._apply_colormap(grayscale, "invalid_colormap_name")

        # Assert - Sollte trotzdem funktionieren (Fallback auf viridis)
        assert result.shape == (1, 2, 3)
        assert result.dtype == np.uint8

    def test_resize_to_display(self):
        """Test: Resize auf Display-Größe."""
        # Arrange
        service = VisualizationService()
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Act
        result = service._resize_to_display(image)

        # Assert
        assert result.shape == (service.DISPLAY_HEIGHT, service.DISPLAY_WIDTH, 3)

    def test_visualize_different_colormaps(self):
        """Test: Verschiedene Colormaps."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(10, 28, 28)

        colormaps = ['viridis', 'plasma', 'inferno', 'hot']

        for cmap in colormaps:
            preset = PresetConfig(
                preset_id=0,
                name="Test",
                channels=[0, 1],
                colormap=cmap,
                normalize=True,
                blend_mode="mean"
            )

            # Act
            result = service.visualize(activations, preset)

            # Assert
            assert result.shape == (service.DISPLAY_HEIGHT, service.DISPLAY_WIDTH, 3)
            assert result.dtype == np.uint8

    def test_visualize_different_blend_modes(self):
        """Test: Verschiedene Blend-Modi."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(10, 28, 28)

        blend_modes = ['max', 'mean', 'overlay']

        for mode in blend_modes:
            preset = PresetConfig(
                preset_id=0,
                name="Test",
                channels=[0, 1, 2],
                colormap="viridis",
                normalize=True,
                blend_mode=mode
            )

            # Act
            result = service.visualize(activations, preset)

            # Assert
            assert result.shape == (service.DISPLAY_HEIGHT, service.DISPLAY_WIDTH, 3)

    def test_select_channels_filters_minus_one(self):
        """Test: _select_channels filtert -1 Werte korrekt."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(64, 56, 56)  # 64 Channels

        # Act
        result = service._select_channels(activations, [0, 5, -1])

        # Assert - Nur 2 gültige Channels (0 und 5)
        assert result.shape[0] == 2

    def test_select_channels_filters_multiple_minus_one(self):
        """Test: _select_channels filtert mehrere -1 Werte."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(64, 56, 56)

        # Act
        result = service._select_channels(activations, [10, -1, -1])

        # Assert - Nur 1 gültiger Channel
        assert result.shape[0] == 1

    def test_select_channels_with_only_minus_one_fallback(self):
        """Test: _select_channels mit nur -1 (Fallback auf 0)."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(64, 56, 56)

        # Act - Normalerweise würde PresetConfig das verhindern,
        # aber _select_channels sollte robust sein
        result = service._select_channels(activations, [-1, -1, -1])

        # Assert - Fallback auf Channel 0
        assert result.shape[0] == 1

    def test_select_channels_preserves_order(self):
        """Test: _select_channels erhält Reihenfolge der gültigen Channels."""
        # Arrange
        service = VisualizationService()
        # Erstelle deterministischen Tensor
        activations = torch.zeros(64, 2, 2)
        activations[5] = torch.ones(2, 2) * 5.0
        activations[10] = torch.ones(2, 2) * 10.0

        # Act - -1 in der Mitte sollte herausgefiltert werden
        result = service._select_channels(activations, [5, -1, 10])

        # Assert
        assert result.shape[0] == 2
        assert torch.allclose(result[0], torch.ones(2, 2) * 5.0)
        assert torch.allclose(result[1], torch.ones(2, 2) * 10.0)

    def test_visualize_with_partial_channels(self):
        """Test: visualize funktioniert mit Preset das -1 Channels hat."""
        # Arrange
        service = VisualizationService()
        activations = torch.randn(64, 56, 56)
        preset = PresetConfig(
            preset_id=0,
            name="Partial",
            channels=[0, 5, -1],  # Nur 2 aktive Channels
            colormap="viridis",
            normalize=True,
            blend_mode="max"
        )

        # Act
        result = service.visualize(activations, preset)

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.shape == (service.DISPLAY_HEIGHT, service.DISPLAY_WIDTH, 3)
        assert result.dtype == np.uint8
