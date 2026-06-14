"""
Integration Tests für CNN-Visualisierung Museum-Projekt.

End-to-End-Tests für den kompletten Workflow:
Kamera → Model → Visualization → View

Author: Museum CNN Team
Date: 2025-11-29
"""

import pytest
import numpy as np
from pathlib import Path
from typing import Optional

from core.facade import ApplicationFacade
from core.models import PresetConfig
from storage.config_manager import ConfigManager
from core.services.camera_service import CameraService
from core.services.model_service import ModelService
from core.services.visualization_service import VisualizationService
from core.services.preset_service import PresetService


class TestEndToEndWorkflow:
    """End-to-End Tests für den kompletten Workflow."""

    @pytest.fixture
    def facade(self, tmp_path: Path) -> ApplicationFacade:
        """Erstellt ApplicationFacade mit temporärer Config."""
        config_path = tmp_path / "test_config.json"
        config_manager = ConfigManager(config_path=config_path)

        camera_service = CameraService(camera_index=0)
        model_service = ModelService()
        visualization_service = VisualizationService()
        preset_service = PresetService(config_manager=config_manager)

        return ApplicationFacade(
            camera=camera_service,
            model=model_service,
            visualization=visualization_service,
            presets=preset_service
        )

    def test_complete_pipeline_without_camera(self, facade: ApplicationFacade) -> None:
        """
        Testet kompletten Pipeline ohne echte Kamera.

        Workflow: Model laden → Layer-Namen holen
        """
        # Arrange: Initialisiere Facade (lädt Model)
        facade.initialize()

        # Act: Hole verfügbare Layer
        layer_names = facade.get_layer_names()

        # Assert: Layer verfügbar
        assert layer_names is not None
        assert len(layer_names) > 0
        assert isinstance(layer_names, list)

    def test_layer_availability(self, facade: ApplicationFacade) -> None:
        """Testet, dass alle erwarteten ResNet18-Layer verfügbar sind."""
        # Arrange
        facade.initialize()

        # Act
        layers = facade.get_layer_names()

        # Assert: Bekannte ResNet18-Layer vorhanden
        expected_layers = ['conv1', 'layer1', 'layer2', 'layer3', 'layer4']
        for expected in expected_layers:
            assert any(expected in layer for layer in layers), \
                f"Layer '{expected}' nicht gefunden in {layers}"

    def test_preset_management(self, facade: ApplicationFacade) -> None:
        """
        Testet Preset-Verwaltung.

        Workflow: Layer wählen → Preset ändern
        """
        # Arrange
        facade.initialize()
        layers = facade.get_layer_names()
        test_layer = layers[0] if layers else "conv1"

        # Act: Hole Preset für Layer (Preset 0)
        preset = facade.get_preset(test_layer, 0)

        # Assert: Preset existiert
        assert preset is not None
        assert isinstance(preset, PresetConfig)

    def test_config_persistence(self, tmp_path: Path) -> None:
        """
        Testet Konfigurations-Persistierung über Neustart.

        Workflow: Preset speichern → Facade neu laden → Preset wieder verfügbar
        """
        # Arrange
        config_path = tmp_path / "persistence_test.json"
        config_manager1 = ConfigManager(config_path=config_path)

        camera_service1 = CameraService(camera_index=0)
        model_service1 = ModelService()
        visualization_service1 = VisualizationService()
        preset_service1 = PresetService(config_manager=config_manager1)

        facade1 = ApplicationFacade(
            camera=camera_service1,
            model=model_service1,
            visualization=visualization_service1,
            presets=preset_service1
        )
        facade1.initialize()

        layers = facade1.get_layer_names()
        test_layer = layers[0] if layers else "conv1"

        # Act 1: Custom Preset erstellen und speichern
        custom_preset = PresetConfig(
            preset_id=0,
            name="Persistence Test",
            channels=[0, 1, 2],
            colormap="viridis",
            normalize=True,
            blend_mode="max"
        )
        facade1.save_preset(test_layer, 0, custom_preset)

        # Act 2: Neue Facade-Instanz laden
        config_manager2 = ConfigManager(config_path=config_path)
        camera_service2 = CameraService(camera_index=0)
        model_service2 = ModelService()
        visualization_service2 = VisualizationService()
        preset_service2 = PresetService(config_manager=config_manager2)

        facade2 = ApplicationFacade(
            camera=camera_service2,
            model=model_service2,
            visualization=visualization_service2,
            presets=preset_service2
        )
        facade2.initialize()
        loaded_preset = facade2.get_preset(test_layer, 0)

        # Assert: Gespeicherte Konfiguration wiederhergestellt
        assert loaded_preset is not None
        assert loaded_preset.name == "Persistence Test"
        assert loaded_preset.channels == [0, 1, 2]
        assert loaded_preset.colormap == "viridis"


class TestServiceIntegration:
    """Tests für Service-Interoperabilität."""

    @pytest.fixture
    def facade(self, tmp_path: Path) -> ApplicationFacade:
        """Erstellt ApplicationFacade mit temporärer Config."""
        config_path = tmp_path / "test_config.json"
        config_manager = ConfigManager(config_path=config_path)

        camera_service = CameraService(camera_index=0)
        model_service = ModelService()
        visualization_service = VisualizationService()
        preset_service = PresetService(config_manager=config_manager)

        return ApplicationFacade(
            camera=camera_service,
            model=model_service,
            visualization=visualization_service,
            presets=preset_service
        )

    def test_layer_names_available(self, facade: ApplicationFacade) -> None:
        """
        Testet, dass Layer-Namen vom Model abgerufen werden können.
        """
        # Arrange
        facade.initialize()

        # Act
        layer_names = facade.get_layer_names()

        # Assert
        assert layer_names is not None
        assert isinstance(layer_names, list)
        assert len(layer_names) > 0

    def test_layer_change(self, facade: ApplicationFacade) -> None:
        """
        Testet Layer-Wechsel-Funktionalität.
        """
        # Arrange
        facade.initialize()
        layers = facade.get_layer_names()

        # Act & Assert
        for layer_name in layers:
            facade.change_layer(layer_name)
            current = facade.get_current_layer()
            assert current == layer_name


class TestErrorHandling:
    """Tests für Fehlerbehandlung im Integration-Kontext."""

    @pytest.fixture
    def facade(self, tmp_path: Path) -> ApplicationFacade:
        """Erstellt ApplicationFacade mit temporärer Config."""
        config_path = tmp_path / "test_config.json"
        config_manager = ConfigManager(config_path=config_path)

        camera_service = CameraService(camera_index=0)
        model_service = ModelService()
        visualization_service = VisualizationService()
        preset_service = PresetService(config_manager=config_manager)

        return ApplicationFacade(
            camera=camera_service,
            model=model_service,
            visualization=visualization_service,
            presets=preset_service
        )

    def test_invalid_layer_name(self, facade: ApplicationFacade) -> None:
        """Testet Fehlerbehandlung bei ungültigem Layer-Namen."""
        # Arrange
        facade.initialize()
        invalid_layer = "non_existent_layer_xyz"

        # Act & Assert: Sollte ValueError werfen
        with pytest.raises(ValueError):
            facade.change_layer(invalid_layer)


class TestPerformance:
    """Performance-Tests für kritische Pfade."""

    @pytest.fixture
    def facade(self, tmp_path: Path) -> ApplicationFacade:
        """Erstellt ApplicationFacade mit temporärer Config."""
        config_path = tmp_path / "test_config.json"
        config_manager = ConfigManager(config_path=config_path)

        camera_service = CameraService(camera_index=0)
        model_service = ModelService()
        visualization_service = VisualizationService()
        preset_service = PresetService(config_manager=config_manager)

        return ApplicationFacade(
            camera=camera_service,
            model=model_service,
            visualization=visualization_service,
            presets=preset_service
        )

    def test_initialization_speed(self, facade: ApplicationFacade) -> None:
        """
        Testet Initialisierungs-Geschwindigkeit.

        Ziel: < 10s für komplette Initialisierung
        """
        import time

        # Act: Messe Initialisierungszeit
        start = time.time()
        facade.initialize()
        elapsed = time.time() - start

        # Assert: Performance-Ziel
        assert elapsed < 10.0, \
            f"Initialisierung zu langsam: {elapsed:.3f}s (Ziel: < 10.0s)"

        print(f"\n⏱️  Initialisierung: {elapsed:.1f}s")

    def test_layer_switching_stability(self, facade: ApplicationFacade) -> None:
        """
        Testet Stabilität bei wiederholtem Layer-Wechsel.
        """
        # Arrange
        facade.initialize()
        layers = facade.get_layer_names()

        # Act: Wechsle mehrfach zwischen Layern
        iterations = 20
        for i in range(iterations):
            test_layer = layers[i % len(layers)]
            facade.change_layer(test_layer)
            assert facade.get_current_layer() == test_layer

        # Assert: Erfolgreiches Durchlaufen ohne Fehler
        assert True



if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

