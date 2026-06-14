"""Storage Layer - Data Persistence.

This package handles all data persistence operations.
"""

from storage.config_manager import ConfigManager
from storage.interfaces import IConfigStorage
from storage.default_config import get_default_config

__all__ = [
    'ConfigManager',
    'IConfigStorage',
    'get_default_config',
]

