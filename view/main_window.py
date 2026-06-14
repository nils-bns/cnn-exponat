"""Hauptfenster mit Modus-Verwaltung.

Verantwortlichkeiten:
- Wechsel zwischen Visitor Mode und Admin Mode
- Vollbild/Fenster-Umschaltung
- Tastaturkürzel für Admin-Zugang
- Application-Lifecycle-Management
"""

import logging
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QKeySequence, QShortcut, QCloseEvent

from core.facade import ApplicationFacade
from view.media.content.main_window_content import APP_TITLE
from view.visitor_mode import VisitorModeWidget
from view.admin_mode import AdminModeWidget


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung.

    Verwaltet den Wechsel zwischen Visitor Mode (für Museumsbesucher)
    und Admin Mode (für Preset-Konfiguration).

    Attributes:
        _facade: ApplicationFacade für Business-Logik-Zugriff
        _visitor_widget: Widget für Besuchermodus
        _admin_widget: Widget für Admin-Modus
        _stack: QStackedWidget für Modus-Wechsel
    """

    def __init__(self, facade: ApplicationFacade):
        """Initialisiert das Hauptfenster.

        Args:
            facade: ApplicationFacade-Instanz
        """
        super().__init__()

        self._facade = facade
        self._visitor_widget: VisitorModeWidget | None = None
        self._admin_widget: AdminModeWidget | None = None
        self._stack: QStackedWidget | None = None

        self._init_ui()
        self._init_shortcuts()

        logger.info("MainWindow initialisiert")

    def _init_ui(self) -> None:
        """Initialisiert das UI-Layout."""
        # Window-Eigenschaften
        self.setWindowTitle(APP_TITLE["de"])
        self.setMinimumSize(1024, 768)

        # Zentrales Widget mit StackedWidget für Modus-Wechsel
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # StackedWidget für Modus-Wechsel
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Visitor Mode Widget (Index 0)
        self._visitor_widget = VisitorModeWidget(self._facade)
        self._stack.addWidget(self._visitor_widget)

        # Admin Mode Widget (Index 1)
        self._admin_widget = AdminModeWidget(self._facade)
        self._stack.addWidget(self._admin_widget)

        # Standard: Visitor Mode
        self._stack.setCurrentIndex(0)

        # Language-Signal vom Visitor-Widget
        self._visitor_widget.language_changed.connect(self._on_language_changed)

        logger.debug("UI initialisiert")

    def _init_shortcuts(self) -> None:
        """Initialisiert Tastaturkürzel."""
        # F11: Vollbild-Toggle
        fullscreen_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F11), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

        # Ctrl+A: Admin Mode
        admin_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        admin_shortcut.activated.connect(self.switch_to_admin_mode)

        # Ctrl+V: Visitor Mode
        visitor_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        visitor_shortcut.activated.connect(self.switch_to_visitor_mode)

        # ESC: Zurück zu Visitor Mode (aus Admin Mode)
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self.switch_to_visitor_mode)

        logger.debug("Tastaturkürzel registriert")

    @pyqtSlot(str)
    def _on_language_changed(self, language: str) -> None:
        """Aktualisiert Window-Titel bei Sprachwechsel.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        self.setWindowTitle(APP_TITLE.get(language, APP_TITLE["de"]))
        logger.debug(f"Window-Titel aktualisiert: {language}")

    @pyqtSlot()
    def switch_to_visitor_mode(self) -> None:
        """Wechselt in den Besuchermodus.

        Stoppt den Admin Mode und startet den Visitor Mode.
        """
        logger.info("Wechsel zu Visitor Mode")

        # Admin Mode stoppen
        if self._admin_widget:
            self._admin_widget.stop()

        # Zu Visitor Mode wechseln
        self._stack.setCurrentIndex(0)

        # Visitor Mode starten (auch wenn bereits im Visitor Mode - für initialen Start)
        if self._visitor_widget:
            self._visitor_widget.start()

    @pyqtSlot()
    def switch_to_admin_mode(self) -> None:
        """Wechselt in den Admin-Modus.

        Stoppt den Visitor Mode und startet den Admin Mode.
        """
        if self._stack.currentIndex() == 1:
            # Bereits im Admin Mode
            return

        logger.info("Wechsel zu Admin Mode")

        # Visitor Mode stoppen
        if self._visitor_widget:
            self._visitor_widget.stop()

        # Zu Admin Mode wechseln
        self._stack.setCurrentIndex(1)

        # Admin Mode starten
        if self._admin_widget:
            self._admin_widget.start()

    @pyqtSlot()
    def toggle_fullscreen(self) -> None:
        """Wechselt zwischen Vollbild und Fenster-Modus."""
        if self.isFullScreen():
            logger.info("Verlasse Vollbild-Modus")
            self.showNormal()
        else:
            logger.info("Wechsel zu Vollbild-Modus")
            self.showFullScreen()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Behandelt das Schließen des Fensters.

        Args:
            event: QCloseEvent
        """
        logger.info("MainWindow wird geschlossen")

        # Beide Widgets stoppen
        if self._visitor_widget:
            self._visitor_widget.stop()

        if self._admin_widget:
            self._admin_widget.stop()

        # Event akzeptieren
        event.accept()

