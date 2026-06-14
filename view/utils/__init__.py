"""Utility-Funktionen für View-Komponenten.

Dieses Package enthält:
- frame_converter.py: NumPy-Array zu QPixmap Konvertierung
"""

from .frame_converter import numpy_to_qpixmap

__all__ = [
    'numpy_to_qpixmap',
]
