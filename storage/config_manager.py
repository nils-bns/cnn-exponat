"""Configuration manager for JSON persistence.

This module implements the configuration storage using JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Any

from core.models import (
    ConfigData,
    LayerPresets,
    PresetConfig,
)
from core.exceptions import ConfigLoadError, ConfigSaveError
from storage.default_config import get_default_config


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manager für JSON-basierte Konfigurations-Persistierung.

    Verantwortlich für:
    - Laden und Speichern der config.json
    - Serialisierung/Deserialisierung von ConfigData
    - Validierung der JSON-Struktur
    - Automatisches Erstellen der Default-Config bei fehlendem File

    Attributes:
        _config_path: Pfad zur config.json
    """

    def __init__(self, config_path: Path | str = "config.json"):
        """Initialisiert den ConfigManager.

        Args:
            config_path: Pfad zur Konfigurations-Datei
        """
        self._config_path = Path(config_path)
        logger.info(f"ConfigManager initialisiert mit Pfad: {self._config_path}")

    def load_config(self) -> ConfigData:
        """Lädt die Konfiguration aus der JSON-Datei.

        Wenn die Datei nicht existiert, wird automatisch eine Default-Config erstellt.

        Returns:
            ConfigData-Objekt mit der geladenen Konfiguration

        Raises:
            ConfigLoadError: Bei Problemen beim Laden oder Parsen
        """
        if not self._config_path.exists():
            logger.warning(f"Config-Datei nicht gefunden: {self._config_path}")
            logger.info("Erstelle Default-Konfiguration...")
            config = self._create_default_config()
            return config

        try:
            logger.info(f"Lade Konfiguration von: {self._config_path}")
            with open(self._config_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            config = self._deserialize_config(json_data)
            logger.info("Konfiguration erfolgreich geladen")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"JSON-Parse-Fehler: {e}")
            raise ConfigLoadError(f"Ungültige JSON-Datei: {e}") from e
        except Exception as e:
            logger.error(f"Fehler beim Laden der Config: {e}")
            raise ConfigLoadError(f"Fehler beim Laden: {e}") from e

    def save_config(self, config: ConfigData) -> None:
        """Speichert die Konfiguration in die JSON-Datei.

        Args:
            config: ConfigData-Objekt zum Speichern

        Raises:
            ConfigSaveError: Bei Problemen beim Speichern
        """
        try:
            logger.info(f"Speichere Konfiguration nach: {self._config_path}")
            json_data = self._serialize_config(config)

            # Sicherstellen, dass das Verzeichnis existiert
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            # Temporäre Datei schreiben, dann atomar umbenennen
            temp_path = self._config_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            # Atomar umbenennen (ueberschreibt existierende Datei)
            temp_path.replace(self._config_path)

            logger.info("Konfiguration erfolgreich gespeichert")

        except Exception as e:
            logger.error(f"Fehler beim Speichern der Config: {e}")
            raise ConfigSaveError(f"Fehler beim Speichern: {e}") from e

    def _create_default_config(self) -> ConfigData:
        """Erstellt und speichert die Default-Konfiguration.

        Returns:
            Default ConfigData-Objekt
        """
        config = get_default_config()
        self.save_config(config)
        logger.info("Default-Konfiguration erstellt und gespeichert")
        return config

    def _serialize_config(self, config: ConfigData) -> dict[str, Any]:
        """Serialisiert ConfigData zu JSON-kompatiblem Dictionary.

        Args:
            config: ConfigData-Objekt

        Returns:
            JSON-kompatibles Dictionary
        """
        return {
            "version": config.version,
            "presets": {
                layer_name: self._serialize_layer_presets(layer_presets)
                for layer_name, layer_presets in config.presets.items()
            }
        }

    def _serialize_layer_presets(self, layer_presets: LayerPresets) -> dict[str, Any]:
        """Serialisiert LayerPresets zu Dictionary.

        Args:
            layer_presets: LayerPresets-Objekt

        Returns:
            Dictionary-Repräsentation
        """
        return {
            "layer_name": layer_presets.layer_name,
            "active_preset_id": layer_presets.active_preset_id,
            "presets": [
                self._serialize_preset(preset)
                for preset in layer_presets.presets
            ]
        }

    def _serialize_preset(self, preset: PresetConfig) -> dict[str, Any]:
        """Serialisiert PresetConfig zu Dictionary.

        Args:
            preset: PresetConfig-Objekt

        Returns:
            Dictionary-Repräsentation
        """
        return {
            "preset_id": preset.preset_id,
            "name": preset.name,
            "channels": preset.channels,
            "colormap": preset.colormap,
            "normalize": preset.normalize,
            "blend_mode": preset.blend_mode,
            "visualization_mode": preset.visualization_mode
        }

    def _deserialize_config(self, data: dict[str, Any]) -> ConfigData:
        """Deserialisiert JSON-Dictionary zu ConfigData.

        Args:
            data: JSON-Dictionary

        Returns:
            ConfigData-Objekt

        Raises:
            ValueError: Bei ungültigen Daten
        """
        presets_data = data.get("presets", {})
        presets = {}
        for layer_name, layer_data in presets_data.items():
            presets[layer_name] = self._deserialize_layer_presets(layer_data)

        return ConfigData(
            version=data.get("version", "1.0"),
            presets=presets
        )

    def _deserialize_layer_presets(self, data: dict[str, Any]) -> LayerPresets:
        """Deserialisiert Dictionary zu LayerPresets.

        Args:
            data: Dictionary mit Layer-Preset-Daten

        Returns:
            LayerPresets-Objekt
        """
        presets = [
            self._deserialize_preset(preset_data)
            for preset_data in data.get("presets", [])
        ]

        return LayerPresets(
            layer_name=data.get("layer_name", ""),
            presets=presets,
            active_preset_id=data.get("active_preset_id", 0)
        )

    def _deserialize_preset(self, data: dict[str, Any]) -> PresetConfig:
        """Deserialisiert Dictionary zu PresetConfig.

        Migration-Logik:
        - Alte Configs ohne visualization_mode: Default = "colormap"
        - Alte Configs mit colormap="custom": Migriere zu "viridis"

        Args:
            data: Dictionary mit Preset-Daten

        Returns:
            PresetConfig-Objekt
        """
        # Migration: Alte Configs ohne visualization_mode
        visualization_mode = data.get('visualization_mode', 'colormap')

        # Migration: Custom-Colormap entfernen
        colormap = data.get('colormap', 'viridis')
        if colormap == 'custom':
            logger.warning(
                f"Preset '{data.get('name', 'Unknown')}' verwendet deprecated 'custom' colormap. "
                "Migriere zu 'viridis'."
            )
            colormap = 'viridis'

        return PresetConfig(
            preset_id=data.get("preset_id", 0),
            name=data.get("name", ""),
            channels=data.get("channels", []),
            colormap=colormap,  # Migrierter Wert
            normalize=data.get("normalize", True),
            blend_mode=data.get("blend_mode", "max"),
            visualization_mode=visualization_mode
        )

