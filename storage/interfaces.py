"""Interface for configuration storage.

This module defines the protocol (interface) for configuration persistence.
"""

from typing import Protocol
from core.models import ConfigData


class IConfigStorage(Protocol):
    """Interface für Konfigurations-Speicherung.

    Definiert die Schnittstelle für das Laden und Speichern der Konfiguration.
    """

    def load_config(self) -> ConfigData:
        """Lädt die Konfiguration.

        Returns:
            ConfigData-Objekt mit der gesamten Konfiguration

        Raises:
            ConfigLoadError: Wenn Config nicht geladen werden kann
        """
        ...

    def save_config(self, config: ConfigData) -> None:
        """Speichert die Konfiguration.

        Args:
            config: ConfigData-Objekt zum Speichern

        Raises:
            ConfigSaveError: Wenn Config nicht gespeichert werden kann
        """
        ...

