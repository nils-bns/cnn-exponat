"""Basis-Klasse für transparente Overlay-Widgets.

Verwendet für InfoPanel und LayerButtonBar in Visitor Mode.
"""

import logging
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal

logger = logging.getLogger(__name__)


class BaseOverlayWidget(QWidget):
    """Basis-Klasse für transparente Overlay-Widgets.

    Features:
    - Transparenter Hintergrund
    - Fade-In/Fade-Out Animationen
    - Event-Handling konfigurierbar

    Verwendung:
        class MyOverlay(BaseOverlayWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                # Custom initialization
    """

    # Signals
    fade_finished = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        """Initialisiert Base-Overlay-Widget.

        Args:
            parent: Parent-Widget (meist das Hauptfenster)
        """
        super().__init__(parent)

        # Transparenter Hintergrund
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Mouse-Events durchlassen (kann von Subklassen überschrieben werden)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Opacity-Effect für Fade-Animationen
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        # Animation
        self._fade_animation: QPropertyAnimation | None = None

        logger.debug(f"{self.__class__.__name__} initialisiert")

    def fade_in(self, duration: int = 300) -> None:
        """Fade-In Animation.

        Args:
            duration: Dauer der Animation in Millisekunden
        """
        self._animate_opacity(0.0, 1.0, duration)

    def fade_out(self, duration: int = 300) -> None:
        """Fade-Out Animation.

        Args:
            duration: Dauer der Animation in Millisekunden
        """
        self._animate_opacity(1.0, 0.0, duration)

    def _animate_opacity(self, start: float, end: float, duration: int) -> None:
        """Animiert Opacity von start zu end.

        Args:
            start: Start-Opacity (0.0 - 1.0)
            end: End-Opacity (0.0 - 1.0)
            duration: Dauer in Millisekunden
        """
        # Stoppe bestehende Animation
        if self._fade_animation is not None:
            self._fade_animation.stop()

        # Neue Animation
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(duration)
        self._fade_animation.setStartValue(start)
        self._fade_animation.setEndValue(end)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Signal bei Abschluss
        self._fade_animation.finished.connect(self.fade_finished.emit)

        self._fade_animation.start()
        logger.debug(f"Fade-Animation gestartet: {start} → {end} ({duration}ms)")

    def set_transparent_for_mouse(self, transparent: bool) -> None:
        """Setzt ob Mouse-Events durchgelassen werden.

        Args:
            transparent: True = Events durchlassen, False = Events fangen
        """
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, transparent)

    def update_language(self, language: str) -> None:
        """Aktualisiert Widget-Inhalte fuer die angegebene Sprache.

        Subklassen ueberschreiben diese Methode, um sprachspezifische
        Inhalte aus ihren Content-Dateien zu laden.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        pass
