"""Touch-optimierter Layer-Button.

Ein spezialisierter QPushButton für die Layer-Navigation
mit großer Touch-Fläche und visuellen Feedback.
"""

import logging
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import (
    QSize, pyqtSignal, pyqtProperty, QPropertyAnimation,
    QSequentialAnimationGroup, QEasingCurve,
)
from PyQt6.QtGui import QFont

from view.styles import BUTTON_DIMS, FONT_SIZES


logger = logging.getLogger(__name__)


class LayerButton(QPushButton):
    """Touch-optimierter Button für Layer-Auswahl.

    Features:
    - Große Touch-Fläche (mindestens 150x80 px)
    - Klares visuelles Feedback bei Hover/Press/Active
    - Custom Styling für Museum-Kontext

    Signals:
        layer_selected: Emittiert beim Klick mit Layer-Name
    """

    # Custom Signal
    layer_selected = pyqtSignal(str)

    def __init__(
        self,
        layer_name: str,
        display_text: str | None = None,
        parent=None
    ):
        """Initialisiert den LayerButton.

        Args:
            layer_name: Interner Layer-Name (z.B. "layer1")
            display_text: Anzuzeigender Text (optional)
            parent: Parent Widget
        """
        super().__init__(parent)

        self._layer_name = layer_name

        # Display-Text
        if display_text:
            self.setText(display_text)
        else:
            self.setText(layer_name.upper())

        # Button-Eigenschaften - Dimensionen aus StyleManager
        self.setMinimumSize(QSize(BUTTON_DIMS.min_width, BUTTON_DIMS.min_height))
        self.setCheckable(True)

        # Font - Größe aus StyleManager
        button_font = QFont(FONT_SIZES.font_family, FONT_SIZES.large, QFont.Weight.Bold)
        self.setFont(button_font)

        # Styling via base.qss (Selektor: QPushButton.layer-button)
        self.setObjectName("layer-button")

        # Signal-Verbindung
        self.clicked.connect(self._on_clicked)

        # Pulse-Animation State
        self._base_size: QSize | None = None
        self._pulse_scale_value: float = 1.0
        self._pulse_animation: QSequentialAnimationGroup | None = None

        logger.debug(f"LayerButton erstellt: {layer_name}")

    def _on_clicked(self) -> None:
        """Behandelt Button-Klick."""
        logger.debug(f"LayerButton geklickt: {self._layer_name}")
        self.layer_selected.emit(self._layer_name)

    @property
    def layer_name(self) -> str:
        """Gibt den Layer-Namen zurück."""
        return self._layer_name

    def set_active(self, active: bool) -> None:
        """Setzt den Button als aktiv/inaktiv.

        Args:
            active: True wenn Button aktiv sein soll
        """
        self.setChecked(active)

    def capture_base_size(self) -> QSize:
        """Erfasst aktuelle Groesse als Basis fuer Pulse-Animation.

        Muss NACH Layout-Finalisierung aufgerufen werden (z.B. via
        QTimer.singleShot). Gibt die erfasste Groesse zurueck.

        Returns:
            Erfasste Basisgroesse
        """
        self._base_size = self.size()
        logger.debug(
            f"Basisgroesse erfasst fuer {self._layer_name}: "
            f"{self._base_size.width()}x{self._base_size.height()}"
        )
        return self._base_size

    def _get_pulse_scale(self) -> float:
        """Getter fuer pulse_scale Property."""
        return self._pulse_scale_value

    def _set_pulse_scale(self, scale: float) -> None:
        """Setter fuer pulse_scale Property.

        Skaliert den Button relativ zur Basisgroesse.

        Args:
            scale: Skalierungsfaktor (1.0 = Basisgroesse, 1.05 = 5% groesser)
        """
        self._pulse_scale_value = scale
        if self._base_size is not None:
            new_width = int(self._base_size.width() * scale)
            new_height = int(self._base_size.height() * scale)
            self.setFixedSize(QSize(new_width, new_height))

    pulse_scale = pyqtProperty(float, fget=_get_pulse_scale, fset=_set_pulse_scale)

    def start_pulse(self) -> None:
        """Startet Pulse-Animation (5% Groessenaenderung, 2s Zyklus).

        Voraussetzung: capture_base_size() wurde vorher aufgerufen.
        Falls keine Basisgroesse vorhanden, wird nicht gestartet.
        """
        if self._base_size is None:
            logger.warning(f"start_pulse ohne Basisgroesse: {self._layer_name}")
            return

        self.stop_pulse()

        grow = QPropertyAnimation(self, b"pulse_scale")
        grow.setDuration(1000)
        grow.setStartValue(1.0)
        grow.setEndValue(1.1)
        grow.setEasingCurve(QEasingCurve.Type.InOutSine)

        shrink = QPropertyAnimation(self, b"pulse_scale")
        shrink.setDuration(1000)
        shrink.setStartValue(1.1)
        shrink.setEndValue(1.0)
        shrink.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._pulse_animation = QSequentialAnimationGroup(self)
        self._pulse_animation.addAnimation(grow)
        self._pulse_animation.addAnimation(shrink)
        self._pulse_animation.setLoopCount(-1)
        self._pulse_animation.start()

        logger.debug(f"Pulse gestartet: {self._layer_name}")

    def stop_pulse(self) -> None:
        """Stoppt Pulse-Animation und stellt Basisgroesse wieder her."""
        if self._pulse_animation is not None:
            self._pulse_animation.stop()
            self._pulse_animation.deleteLater()
            self._pulse_animation = None

        self._pulse_scale_value = 1.0
        if self._base_size is not None:
            self.setFixedSize(self._base_size)

        logger.debug(f"Pulse gestoppt: {self._layer_name}")

