"""Frame-Konvertierung von NumPy zu PyQt6 Pixmaps.

Eliminiert Code-Duplikation aus visitor_mode.py und admin_mode.py.
"""

import logging
import numpy as np
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QSize

logger = logging.getLogger(__name__)


def numpy_to_qpixmap(
    frame: np.ndarray,
    target_size: QSize | None = None,
    keep_aspect_ratio: bool = True
) -> QPixmap:
    """Konvertiert NumPy RGB-Array zu QPixmap.

    Diese Funktion ersetzt die duplizierte _on_frame_ready() Logik
    aus visitor_mode.py und admin_mode.py.

    Args:
        frame: RGB-Bild als NumPy array (H, W, 3) mit dtype uint8
        target_size: Optionale Zielgröße für Skalierung
        keep_aspect_ratio: Seitenverhältnis beibehalten (default: True)

    Returns:
        QPixmap des Bildes, optional skaliert

    Raises:
        ValueError: Wenn frame falsches Format hat

    Example:
        >>> frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        >>> pixmap = numpy_to_qpixmap(frame)
        >>> pixmap = numpy_to_qpixmap(frame, QSize(320, 240))
    """
    # Validierung
    if frame.ndim != 3:
        raise ValueError(f"Frame muss 3D sein (H, W, 3), ist: {frame.ndim}D")

    if frame.shape[2] != 3:
        raise ValueError(f"Frame muss 3 Channels haben (RGB), hat: {frame.shape[2]}")

    if frame.dtype != np.uint8:
        logger.warning(f"Frame dtype ist {frame.dtype}, erwartet uint8")

    # Konvertierung
    height, width, channels = frame.shape
    bytes_per_line = 3 * width

    q_image = QImage(
        frame.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888
    )

    pixmap = QPixmap.fromImage(q_image)

    # Optionale Skalierung
    if target_size is not None:
        aspect_mode = (
            Qt.AspectRatioMode.KeepAspectRatioByExpanding
            if keep_aspect_ratio
            else Qt.AspectRatioMode.IgnoreAspectRatio
        )

        pixmap = pixmap.scaled(
            target_size,
            aspect_mode,
            Qt.TransformationMode.SmoothTransformation
        )

        # Zentriertes Cropping: KeepAspectRatioByExpanding erzeugt ein
        # Pixmap das groesser als target_size sein kann - auf exakte
        # Zielgroesse zuschneiden
        if keep_aspect_ratio and (
            pixmap.width() > target_size.width()
            or pixmap.height() > target_size.height()
        ):
            x_offset = (pixmap.width() - target_size.width()) // 2
            y_offset = (pixmap.height() - target_size.height()) // 2
            pixmap = pixmap.copy(
                x_offset, y_offset,
                target_size.width(), target_size.height(),
            )

    return pixmap
