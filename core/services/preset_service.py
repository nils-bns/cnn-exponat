"""PresetService - Verwaltung und Bereitstellung von Presets."""

import logging
from storage.interfaces import IConfigStorage
from core.models import PresetConfig
from core.exceptions import InvalidPresetError


logger = logging.getLogger(__name__)


class PresetService:
    """Verwaltet Presets für Layer-Visualisierung.

    Lädt Presets aus der Konfiguration, stellt aktive Presets bereit
    und speichert Änderungen persistent.
    """

    def __init__(self, config_manager: IConfigStorage):
        """Initialisiert PresetService.

        Args:
            config_manager: ConfigManager für Datenpersistierung
        """
        self._config_manager = config_manager
        self._config_data = self._config_manager.load_config()
        logger.info("PresetService initialisiert")

    def get_preset(self, layer_name: str, preset_id: int) -> PresetConfig:
        """Holt spezifisches Preset für Layer.

        Args:
            layer_name: Name des Layers
            preset_id: ID des Presets (0-2)

        Returns:
            PresetConfig

        Raises:
            ValueError: Wenn layer_name oder preset_id ungültig
        """
        self._validate_layer_name(layer_name)
        self._validate_preset_id(preset_id)

        layer_presets = self._config_data.presets.get(layer_name)
        if layer_presets is None:
            raise ValueError(f"Layer '{layer_name}' nicht in Konfiguration gefunden")

        # Suche Preset mit entsprechender ID
        for preset in layer_presets.presets:
            if preset.preset_id == preset_id:
                return preset

        raise InvalidPresetError(
            f"Preset {preset_id} für Layer '{layer_name}' nicht gefunden"
        )

    def get_active_preset(self, layer_name: str) -> PresetConfig:
        """Holt aktuell aktives Preset für Layer.

        Args:
            layer_name: Name des Layers

        Returns:
            PresetConfig des aktiven Presets

        Raises:
            ValueError: Wenn layer_name ungültig
        """
        self._validate_layer_name(layer_name)

        layer_presets = self._config_data.presets.get(layer_name)
        if layer_presets is None:
            raise ValueError(f"Layer '{layer_name}' nicht in Konfiguration gefunden")

        active_id = layer_presets.active_preset_id

        return self.get_preset(layer_name, active_id)

    def set_active_preset(self, layer_name: str, preset_id: int) -> None:
        """Setzt aktives Preset für Layer.

        Args:
            layer_name: Name des Layers
            preset_id: ID des Presets (0-2)

        Raises:
            ValueError: Wenn layer_name oder preset_id ungültig
        """
        self._validate_layer_name(layer_name)
        self._validate_preset_id(preset_id)

        # Prüfe, ob Preset existiert
        self.get_preset(layer_name, preset_id)

        # Setze aktives Preset
        layer_presets = self._config_data.presets.get(layer_name)
        if layer_presets is not None:
            layer_presets.active_preset_id = preset_id
            logger.info(
                f"Aktives Preset für Layer '{layer_name}' auf {preset_id} gesetzt"
            )

            # Speichere Änderung
            self._config_manager.save_config(self._config_data)

    def save_preset(
        self,
        layer_name: str,
        preset_id: int,
        preset: PresetConfig
    ) -> None:
        """Speichert Preset-Konfiguration persistent.

        Args:
            layer_name: Name des Layers
            preset_id: ID des Presets (0-2)
            preset: PresetConfig-Objekt

        Raises:
            ValueError: Wenn layer_name oder preset_id ungültig
        """
        self._validate_layer_name(layer_name)
        self._validate_preset_id(preset_id)

        # Stelle sicher, dass preset_id konsistent ist
        if preset.preset_id != preset_id:
            logger.warning(
                f"preset_id in PresetConfig ({preset.preset_id}) "
                f"stimmt nicht mit Argument ({preset_id}) überein. "
                f"Verwende Argument-Wert."
            )
            preset.preset_id = preset_id

        layer_presets = self._config_data.presets.get(layer_name)
        if layer_presets is None:
            raise ValueError(f"Layer '{layer_name}' nicht in Konfiguration gefunden")

        # Suche existierendes Preset und aktualisiere oder füge hinzu
        found = False
        for i, existing_preset in enumerate(layer_presets.presets):
            if existing_preset.preset_id == preset_id:
                layer_presets.presets[i] = preset
                found = True
                break

        if not found:
            # Neues Preset hinzufügen
            if len(layer_presets.presets) >= 3:
                raise InvalidPresetError(
                    f"Layer '{layer_name}' hat bereits 3 Presets. "
                    f"Lösche erst ein bestehendes Preset."
                )
            layer_presets.presets.append(preset)

        # Speichere Änderungen
        self._config_manager.save_config(self._config_data)
        logger.info(
            f"Preset {preset_id} für Layer '{layer_name}' gespeichert: {preset.name}"
        )

    def get_all_presets_for_layer(self, layer_name: str) -> list[PresetConfig]:
        """Gibt alle Presets eines Layers zurück (max. 3).

        Args:
            layer_name: Name des Layers

        Returns:
            Liste von PresetConfig-Objekten

        Raises:
            ValueError: Wenn layer_name ungültig
        """
        self._validate_layer_name(layer_name)

        layer_presets = self._config_data.presets.get(layer_name)
        if layer_presets is None:
            raise ValueError(f"Layer '{layer_name}' nicht in Konfiguration gefunden")

        return layer_presets.presets.copy()

    def _validate_layer_name(self, layer_name: str) -> None:
        """Validiert Layer-Namen.

        Args:
            layer_name: Name des Layers

        Raises:
            ValueError: Wenn layer_name ungültig
        """
        if layer_name not in self._config_data.presets:
            available = list(self._config_data.presets.keys())
            raise ValueError(
                f"Ungültiger Layer '{layer_name}'. "
                f"Verfügbare Layer: {available}"
            )

    def _validate_preset_id(self, preset_id: int) -> None:
        """Validiert Preset-ID.

        Args:
            preset_id: ID des Presets

        Raises:
            ValueError: Wenn preset_id ungültig
        """
        if preset_id not in [0, 1, 2]:
            raise ValueError(f"preset_id muss 0, 1 oder 2 sein, nicht {preset_id}")

