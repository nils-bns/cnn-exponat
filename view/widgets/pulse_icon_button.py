"""Pulsierender Icon-Button.

Ein QPushButton, dessen Icon (NICHT die Button-Box) kontinuierlich
sanft zoomt, um den Button als klickbar hervorzuheben. Die Mechanik
orientiert sich am Pulse-Effekt des LayerButton (view/widgets/layer_button.py),
skaliert aber ausschliesslich setIconSize - die Box-Groesse bleibt konstant,
wodurch der Effekt vollstaendig layout-neutral ist.
"""

import logging

from PyQt6.QtGui import QIcon, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QPushButton, QStyle, QStyleOptionButton
from PyQt6.QtCore import (
    QRectF, QSize, pyqtProperty, QPropertyAnimation,
    QSequentialAnimationGroup, QEasingCurve,
)

logger = logging.getLogger(__name__)

# Pulse-Parameter (konsistent zu LayerButton, leicht anpassbar)
_PULSE_GROW_FACTOR: float = 1.1     # 10 % Icon-Vergroesserung
_PULSE_DURATION_MS: int = 1000      # je Richtung (grow/shrink) -> 2 s Zyklus


class PulseIconButton(QPushButton):
    """QPushButton mit pulsierendem Icon-Zoom.

    Die Button-Box bleibt konstant; das Icon wird via sub-pixel-genauem
    paintEvent-Override kontinuierlich skaliert (kein setIconSize mehr).

    Usage:
        button = PulseIconButton(parent)
        button.setIcon(icon)
        button.setIconSize(QSize(36, 36))
        button.setFixedSize(48, 48)
        # nach Layout-Finalisierung (z. B. QTimer.singleShot(0, ...)):
        button.capture_base_size()
        button.start_pulse()
    """

    def __init__(self, parent=None):
        """Initialisiert den PulseIconButton.

        Args:
            parent: Parent-Widget
        """
        super().__init__(parent)

        self._svg_renderer: QSvgRenderer | None = None
        self._base_icon_size: QSize | None = None
        self._pulse_scale_value: float = 1.0
        self._pulse_animation: QSequentialAnimationGroup | None = None

    def set_svg_renderer(self, renderer: QSvgRenderer) -> None:
        """Injiziert den SVG-Renderer fuer das Icon (Dependency Injection).

        Der Renderer wird im paintEvent direkt in ein Float-QRectF gezeichnet
        (sub-pixel-genau, verlustfrei). Wird kein gueltiger Renderer gesetzt,
        bleibt der Button im Text-Fallback (kein Pulse).

        Args:
            renderer: Geladener QSvgRenderer der Icon-Quelle.
        """
        self._svg_renderer = renderer
        self.update()

    def capture_base_size(self) -> QSize | None:
        """Erfasst die aktuelle Icon-Groesse als Pulse-Basis.

        Sollte nach Layout-Finalisierung aufgerufen werden (z. B. via
        QTimer.singleShot). Ohne gueltigen SVG-Renderer (Text-Fallback)
        wird None zurueckgegeben und kein Pulse moeglich.

        Returns:
            Erfasste Basis-Icon-Groesse oder None (kein gueltiger Renderer).
        """
        # Guard auf den Renderer pruefen: iconSize() liefert auch ohne gesetzten
        # Renderer einen nicht-leeren Style-Default, waehrend ein fehlender/
        # ungueltiger Renderer den Text-Fallback zuverlaessig kennzeichnet.
        if self._svg_renderer is None or not self._svg_renderer.isValid():
            self._base_icon_size = None
            logger.debug("PulseIconButton: kein gueltiger Renderer, Pulse deaktiviert")
            return None

        icon_size = self.iconSize()
        self._base_icon_size = icon_size
        logger.debug(
            f"PulseIconButton Basis-Icon-Groesse erfasst: "
            f"{icon_size.width()}x{icon_size.height()}"
        )
        return self._base_icon_size

    def _get_pulse_scale(self) -> float:
        """Getter fuer pulse_scale Property."""
        return self._pulse_scale_value

    def _set_pulse_scale(self, scale: float) -> None:
        """Setter fuer pulse_scale Property: fordert Repaint an.

        Args:
            scale: Skalierungsfaktor (1.0 = Basisgroesse, 1.1 = 10 % groesser)
        """
        self._pulse_scale_value = scale
        if self._base_icon_size is not None:
            self.update()

    pulse_scale = pyqtProperty(float, fget=_get_pulse_scale, fset=_set_pulse_scale)

    def paintEvent(self, event) -> None:
        """Zeichnet Button-Rahmen und Icon mit sub-pixel-genauem Zoom.

        Der Button-Rahmen (Hover, Press, Focus) wird ueber QStyleOptionButton
        ohne Icon gerendert. Das Icon wird anschliessend mit QSvgRenderer.render
        direkt in ein QRectF mit Float-Koordinaten gezeichnet. Da der Vektor-
        Renderer keine native Aufloesung kennt, rastert er pro Frame verlustfrei
        in die exakte Float-Groesse - kein Rest-Stepping, keine Schaerfe-Obergrenze
        und keine per-Frame-Pixmap-Allokation.
        """
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.icon = QIcon()

        p = QPainter(self)
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, p, self)

        if (self._base_icon_size is None
                or self._svg_renderer is None
                or not self._svg_renderer.isValid()):
            return

        # Skalierungsfaktor des aktuellen Pulse-Frames.
        scale = self._pulse_scale_value

        # Aspect-Verhaeltnis aus der Vektor-Quelle (defaultSize = 325x165).
        # Breite ist width-anchored (Basis-Breite * scale), Hoehe folgt aspect-
        # treu -> keine Verzerrung, Icon bleibt im Button zentriert.
        default = self._svg_renderer.defaultSize()
        aspect = default.height() / default.width()
        draw_w = self._base_icon_size.width() * scale
        draw_h = draw_w * aspect
        x = (self.width() - draw_w) / 2
        y = (self.height() - draw_h) / 2

        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._svg_renderer.render(p, QRectF(x, y, draw_w, draw_h))

    def start_pulse(self) -> None:
        """Startet die Icon-Pulse-Animation (10 %, 2 s Zyklus, endlos).

        Voraussetzung: capture_base_size() lieferte eine gueltige Groesse.
        Idempotent - ein laufender Pulse wird zuvor gestoppt.
        """
        if self._base_icon_size is None:
            logger.warning("PulseIconButton.start_pulse ohne Basis-Icon-Groesse")
            return

        self.stop_pulse()

        grow = QPropertyAnimation(self, b"pulse_scale")
        grow.setDuration(_PULSE_DURATION_MS)
        grow.setStartValue(1.0)
        grow.setEndValue(_PULSE_GROW_FACTOR)
        grow.setEasingCurve(QEasingCurve.Type.InOutSine)

        shrink = QPropertyAnimation(self, b"pulse_scale")
        shrink.setDuration(_PULSE_DURATION_MS)
        shrink.setStartValue(_PULSE_GROW_FACTOR)
        shrink.setEndValue(1.0)
        shrink.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._pulse_animation = QSequentialAnimationGroup(self)
        self._pulse_animation.addAnimation(grow)
        self._pulse_animation.addAnimation(shrink)
        self._pulse_animation.setLoopCount(-1)
        self._pulse_animation.start()

        logger.debug("PulseIconButton Pulse gestartet")

    def stop_pulse(self) -> None:
        """Stoppt die Pulse-Animation und zeichnet das Icon in Basisgroesse."""
        if self._pulse_animation is not None:
            self._pulse_animation.stop()
            self._pulse_animation.deleteLater()
            self._pulse_animation = None

        self._pulse_scale_value = 1.0
        if self._base_icon_size is not None:
            self.update()

        logger.debug("PulseIconButton Pulse gestoppt")
