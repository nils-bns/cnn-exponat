"""Main Entry Point - CNN-Visualisierung Museum-Projekt.

Dieses Modul initialisiert alle Services und startet die Anwendung.
"""

import sys
import logging
from pathlib import Path

# Core Services
from core.services.camera_service import CameraService
from core.services.model_service import ModelService
from core.services.visualization_service import VisualizationService
from core.services import PresetService

# Storage
from storage.config_manager import ConfigManager

# Facade
from core import ApplicationFacade

# Constants
DEFAULT_CONFIG_PATH = "config.json"


def setup_logging(level: int = logging.INFO) -> None:
    """Konfiguriert Logging für die Anwendung.

    Args:
        level: Logging-Level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('museum_cnn.log')
        ]
    )


def create_application_facade() -> ApplicationFacade:
    """Factory-Funktion für ApplicationFacade mit Dependency Injection.

    Returns:
        Vollständig konfigurierte ApplicationFacade-Instanz

    Raises:
        Exception: Wenn Services nicht initialisiert werden können
    """
    logger = logging.getLogger(__name__)
    logger.info("Erstelle ApplicationFacade mit Dependency Injection...")

    # 1. Storage Layer
    logger.info("Initialisiere Storage Layer...")
    config_manager = ConfigManager(config_path=Path(DEFAULT_CONFIG_PATH))

    # 2. Core Services
    logger.info("Initialisiere Core Services...")

    # Camera Service
    camera_service = CameraService(camera_index=CameraService.DEFAULT_CAMERA_INDEX)
    logger.info(f"CameraService erstellt (Index: {CameraService.DEFAULT_CAMERA_INDEX})")

    # Model Service
    model_service = ModelService()
    logger.info("ModelService erstellt")

    # Visualization Service
    visualization_service = VisualizationService()
    logger.info("VisualizationService erstellt")

    # Preset Service (mit ConfigManager)
    preset_service = PresetService(config_manager=config_manager)
    logger.info("PresetService erstellt")

    # 3. Application Facade
    logger.info("Erstelle ApplicationFacade...")
    facade = ApplicationFacade(
        camera=camera_service,
        model=model_service,
        visualization=visualization_service,
        presets=preset_service
    )

    logger.info("ApplicationFacade erfolgreich erstellt")
    return facade


def main() -> int:
    """Haupteinstiegspunkt der Anwendung.

    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    # Setup Logging
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("CNN-Visualisierung Museum-Projekt")
    logger.info("=" * 60)

    try:
        # Erstelle ApplicationFacade mit DI
        facade = create_application_facade()
        config_manager = ConfigManager(config_path=Path(DEFAULT_CONFIG_PATH))

        # Initialisiere Services (Modell laden, Kamera starten)
        logger.info("Initialisiere Services...")
        facade.initialize()

        logger.info("=" * 60)
        logger.info("ApplicationFacade erfolgreich initialisiert!")
        logger.info("Verfügbare Layer:")
        for layer_name in facade.get_layer_names():
            logger.info(f"  - {layer_name}")
        logger.info("=" * 60)

        # View Layer starten (Phase 4)
        logger.info("Starte PyQt6 Anwendung...")
        from PyQt6.QtWidgets import QApplication
        from view.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("CNN Visualisierung Museum")

        # Globales Stylesheet laden (base.qss mit Platzhalter-Ersetzung)
        from view.styles import StyleManager
        app.setStyleSheet(StyleManager.get_stylesheet())

        # MainWindow erstellen
        window = MainWindow(facade)

        # Im Visitor Mode starten
        window.switch_to_visitor_mode()

        # Vollbild-Modus
        window.showFullScreen()

        logger.info("MainWindow gestartet (Vollbild, Visitor Mode)")
        logger.info("Tastaturkürzel:")
        logger.info("  - F11: Vollbild umschalten")
        logger.info("  - Ctrl+A: Admin Mode")
        logger.info("  - Ctrl+V: Visitor Mode")
        logger.info("  - ESC: Zurück zu Visitor Mode")

        # Event Loop starten
        exit_code = app.exec()

        # Shutdown nach Event Loop
        logger.info("\nFahre Services herunter...")
        facade.shutdown()

        logger.info("=" * 60)
        logger.info("Anwendung erfolgreich beendet")
        logger.info("=" * 60)

        return exit_code

    except KeyboardInterrupt:
        logger.info("\nAnwendung durch Benutzer abgebrochen")
        return 0

    except Exception as e:
        logger.error(f"Fehler beim Starten der Anwendung: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

