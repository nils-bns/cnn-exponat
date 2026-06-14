"""Interface für Preset-Verwaltung."""

from typing import Protocol
from core.models import PresetConfig


class IPresetService(Protocol):
    """Interface für Preset-Verwaltung."""

    def get_preset(self, layer_name: str, preset_id: int) -> PresetConfig:
        """Holt spezifisches Preset für Layer.

        Raises:
            ValueError: Wenn layer_name oder preset_id ungültig
        """
        ...

    def get_active_preset(self, layer_name: str) -> PresetConfig:
        """Holt aktuell aktives Preset für Layer."""
        ...

    def set_active_preset(self, layer_name: str, preset_id: int) -> None:
        """Setzt aktives Preset für Layer."""
        ...

    def save_preset(
        self,
        layer_name: str,
        preset_id: int,
        preset: PresetConfig
    ) -> None:
        """Speichert Preset-Konfiguration persistent."""
        ...

    def get_all_presets_for_layer(self, layer_name: str) -> list[PresetConfig]:
        """Gibt alle Presets eines Layers zurück (max. 3)."""
        ...

