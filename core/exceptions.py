"""Custom exceptions for CNN Visualization application.

This module defines all custom exceptions used throughout the application.
"""


class CNNVisualizationError(Exception):
    """Basis-Exception für alle Projekt-Fehler."""
    pass


# Camera-Errors
class CameraError(CNNVisualizationError):
    """Basis für Kamera-Fehler."""
    pass


class CameraNotAvailableError(CameraError):
    """Kamera nicht verfügbar oder nicht verbunden."""
    pass


class CameraFrameError(CameraError):
    """Fehler beim Frame-Abruf."""
    pass


# Model-Errors
class ModelError(CNNVisualizationError):
    """Basis für Model-Fehler."""
    pass


class ModelLoadError(ModelError):
    """Model konnte nicht geladen werden."""
    pass


class InvalidLayerError(ModelError):
    """Layer-Name ungültig."""
    pass


# Config-Errors
class ConfigError(CNNVisualizationError):
    """Basis für Konfigurations-Fehler."""
    pass


class InvalidPresetError(ConfigError):
    """Preset-Konfiguration ungültig."""
    pass


class ConfigLoadError(ConfigError):
    """Config konnte nicht geladen werden."""
    pass


class ConfigSaveError(ConfigError):
    """Config konnte nicht gespeichert werden."""
    pass

