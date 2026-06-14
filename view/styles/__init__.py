"""Zentrales Style-Management für alle View-Komponenten.

Dieses Package enthält:
- colors.py: Farbdefinitionen (Primärfarben, Akzente, etc.)
- dimensions.py: Dimensionen (Button-Größen, Display-Größen, etc.)
- base.qss: QSS-Stylesheet-Template
- style_manager.py: Zentrale Style-Verwaltung

Usage:
    from view.styles import StyleManager, PRIMARY, BUTTON_DIMS

    button.setStyleSheet(StyleManager.get_button_style("primary"))
    button.setMinimumSize(BUTTON_DIMS.min_width, BUTTON_DIMS.min_height)
"""

from .colors import *
from .dimensions import *
from .style_manager import StyleManager

__all__ = [
    'StyleManager',
    # Farben werden durch * aus colors.py exportiert
    # Dimensionen werden durch * aus dimensions.py exportiert
]
