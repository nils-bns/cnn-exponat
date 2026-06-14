"""About-Widget fuer Visitor Mode.

Zeigt ein Info-Icon, das auf Klick einen scrollbaren Content-Bereich aufklappt.
Klick ausserhalb schliesst den Content wieder.
"""

import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QTextEdit, QVBoxLayout, QApplication,
    QStackedWidget, QLabel
)
from PyQt6.QtGui import QPixmap, QTextDocument
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QEvent, QObject, QSize, QTimer, QUrl, pyqtSignal

from view.media.content.about_widget_content import PAGE_CONTENTS
from view.widgets.base_overlay import BaseOverlayWidget
from view.widgets.pulse_icon_button import PulseIconButton
from view.styles import ABOUT_DIMS, FONT_SIZES

logger = logging.getLogger(__name__)

_SVG_PATH = Path(__file__).parent.parent / "media" / "icon" / "th-owl-logo_info-icon.svg"
_IMG_DIR = Path(__file__).parent.parent / "media" / "img"
_SWIPE_THRESHOLD: int = 50  # Pixel fuer Swipe-Erkennung
_INACTIVITY_TIMEOUT_MS: int = 30_000  # Auto-Close nach 30 s ohne Interaktion


class AboutWidget(BaseOverlayWidget):
    """About-Widget mit Icon-Toggle und scrollbarem Content.

    Signals:
        expanded_changed: Emittiert True bei Expand, False bei Collapse.

    Features:
    - Info-Icon Button (mit Text-Fallback falls Icon nicht ladbar)
    - Aufklappbarer Content-Bereich mit 3-Seiten-Slideshow
    - Navigationspfeile (< >) und Swipe-Geste
    - Seitenanzeige (1/3, 2/3, 3/3)
    - Click-Outside-to-Close via Application-Level eventFilter

    Usage:
        about = AboutWidget(parent)
    """

    expanded_changed = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None):
        """Initialisiert AboutWidget.

        Args:
            parent: Parent-Widget (VisitorModeWidget)
        """
        super().__init__(parent)

        self._is_expanded: bool = False
        self._svg_renderer: QSvgRenderer | None = None

        # Inaktivitaets-Timer: schliesst das Widget nach 30 s ohne
        # Interaktion automatisch (Kiosk-Tauglichkeit, siehe Analyse).
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.setInterval(_INACTIVITY_TIMEOUT_MS)
        self._inactivity_timer.timeout.connect(self._collapse)

        # Feste Breite (Hoehe wird durch Layout bestimmt)
        self.setFixedWidth(ABOUT_DIMS.content_width)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Icon Button (mit Icon-Zoom-Pulse zur Klick-Animation)
        self._icon_button = PulseIconButton(self)
        self._icon_button.setObjectName("about-icon-button")
        self._icon_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icon_button.clicked.connect(self._toggle)
        self._setup_icon()
        layout.addWidget(self._icon_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Content-Container (initial versteckt)
        self._content_container = QWidget(self)
        self._content_container.setObjectName("about-content-container")
        self._content_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._content_container.setFixedHeight(ABOUT_DIMS.content_height)
        self._content_container.setVisible(False)
        layout.addWidget(self._content_container)

        # Content-Container Layout
        container_layout = QVBoxLayout(self._content_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Bilinguale Content-Referenz speichern
        self._all_pages = PAGE_CONTENTS
        default_pages = PAGE_CONTENTS.get("de", [])

        # Page Indicator ("1/3")
        self._page_indicator = QLabel(
            f"1/{len(default_pages)}", self._content_container
        )
        self._page_indicator.setObjectName("about-page-indicator")
        self._page_indicator.setAlignment(Qt.AlignmentFlag.AlignRight)
        container_layout.addWidget(self._page_indicator)

        # Page Stack (3 Seiten)
        self._page_stack = QStackedWidget(self._content_container)
        self._page_stack.setObjectName("about-page-stack")

        for html in default_pages:
            page = QTextEdit(self._content_container)
            page.setObjectName("about-content")
            page.setReadOnly(True)
            page.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            page.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            page.document().setDefaultStyleSheet(
                f"body {{ font-family: {FONT_SIZES.font_family}; }}"
            )
            page.setHtml(html)
            self._page_stack.addWidget(page)

        # Logo-Bilder als Ressourcen auf allen QTextDocuments registrieren
        _logo_files = ["ki_akademie_logo.png",
                       "bmftr_en.jpg",
                       "bmftr_de.jpg",
                       "th-owl-qr.png",
                       "th-owl-en-qr.png",
                       "inIT_2020.svg"]
        for i in range(self._page_stack.count()):
            doc = self._page_stack.widget(i).document()
            for img_name in _logo_files:
                img_path = _IMG_DIR / img_name
                pixmap = QPixmap(str(img_path))
                if not pixmap.isNull():
                    doc.addResource(
                        QTextDocument.ResourceType.ImageResource,
                        QUrl(img_name),
                        pixmap,
                    )
                else:
                    logger.warning(f"Logo nicht ladbar: {img_path}")

        container_layout.addWidget(self._page_stack)

        # Navigationspfeile (Overlays auf dem Content-Container)
        self._prev_button = QPushButton("<", self._content_container)
        self._prev_button.setObjectName("about-nav-button")
        self._prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_button.setFixedSize(30, 40)
        self._prev_button.clicked.connect(self._go_previous)

        self._next_button = QPushButton(">", self._content_container)
        self._next_button.setObjectName("about-nav-button")
        self._next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_button.setFixedSize(30, 40)
        self._next_button.clicked.connect(self._go_next)

        # Swipe-Tracking
        self._swipe_start_x: float | None = None
        self._page_stack.installEventFilter(self)

        logger.debug("AboutWidget initialisiert")

        # Initiale Groessenberechnung erzwingen (verhindert Icon-Clipping)
        self.adjustSize()

        # Pulse erst nach Layout-Finalisierung starten (Basis-Icon-Groesse
        # erfassen, dann im collapsed-Zustand pulsen).
        QTimer.singleShot(0, self._init_pulse)

    def _setup_icon(self) -> None:
        """Laedt das SVG-Icon und injiziert den Renderer in den Button.

        Bei ungueltigem SVG (Renderer nicht valide) bleibt der Text-Fallback
        aktiv. Der Renderer wird als Instanz-Attribut gehalten, damit er ueber
        die Lebensdauer des Widgets erreichbar bleibt (DI in den Button).
        """
        renderer = QSvgRenderer(str(_SVG_PATH), self)

        icon_size = ABOUT_DIMS.icon_size
        button_size = icon_size + 12  # 6px Padding pro Seite

        if renderer.isValid():
            self._svg_renderer = renderer
            self._icon_button.set_svg_renderer(renderer)
            self._icon_button.setIconSize(QSize(icon_size, icon_size))
            self._icon_button.setFixedSize(button_size, button_size)
            logger.debug(f"SVG-Icon geladen: {_SVG_PATH}")
        else:
            self._icon_button.setText("about")
            self._icon_button.setFixedHeight(button_size)
            logger.warning(f"SVG nicht ladbar, Text-Fallback aktiv: {_SVG_PATH}")

    def _init_pulse(self) -> None:
        """Erfasst die Basis-Icon-Groesse und startet den Pulse (collapsed).

        Deferred via QTimer.singleShot aus __init__, damit das Layout
        finalisiert ist. Bei Text-Fallback (kein Icon) bleibt der Pulse
        wirkungslos (capture_base_size liefert None).
        """
        self._icon_button.capture_base_size()
        self._icon_button.start_pulse()

    def _toggle(self) -> None:
        """Togglet zwischen expanded und collapsed."""
        if self._is_expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self) -> None:
        """Zeigt den Content-Bereich und aktiviert Click-Outside-Filter.

        Stoppt den Icon-Pulse (waehrend geoeffnet: kein Pulsieren) und
        startet den Inaktivitaets-Timer, der das Widget nach Ablauf ohne
        Interaktion automatisch wieder schliesst.
        """
        self._is_expanded = True
        self._icon_button.stop_pulse()
        self._content_container.setVisible(True)
        self._position_nav_buttons()
        self.adjustSize()

        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        self._inactivity_timer.start()

        self.expanded_changed.emit(True)
        logger.debug("AboutWidget expanded")

    def _collapse(self) -> None:
        """Versteckt den Content-Bereich und deaktiviert Click-Outside-Filter.

        Stoppt den Inaktivitaets-Timer. Wird sowohl manuell (Icon-Klick,
        Klick ausserhalb) als auch automatisch durch den Timeout aufgerufen.
        """
        self._is_expanded = False
        self._inactivity_timer.stop()
        self._content_container.setVisible(False)
        self._page_stack.setCurrentIndex(0)
        self._update_page_indicator()
        self.adjustSize()

        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)

        self._icon_button.start_pulse()

        self.expanded_changed.emit(False)
        logger.debug("AboutWidget collapsed")

    def _position_nav_buttons(self) -> None:
        """Positioniert Navigationspfeile vertikal zentriert am linken/rechten Rand."""
        container_height = self._content_container.height()
        button_height = self._prev_button.height()
        y_center = (container_height - button_height) // 2

        self._prev_button.move(0, y_center)
        self._next_button.move(
            self._content_container.width() - self._next_button.width(), y_center
        )

    def _reset_inactivity_timer(self) -> None:
        """Setzt den Inaktivitaets-Timer zurueck (bei Widget-Interaktion).

        Wird an allen Interaktionspunkten des About-Widgets aufgerufen
        (Navigation, Swipe, Innen-Klick, Scrollen). Nur wirksam, solange
        das Widget expanded ist - im collapsed-Zustand darf der Timer
        nicht (re)starten.
        """
        if self._is_expanded:
            self._inactivity_timer.start()

    def _go_next(self) -> None:
        """Wechselt zur naechsten Seite (endlos: 3 -> 1)."""
        idx = (self._page_stack.currentIndex() + 1) % self._page_stack.count()
        self._page_stack.setCurrentIndex(idx)
        self._update_page_indicator()
        self._reset_inactivity_timer()
        logger.debug(f"AboutWidget Seite: {idx + 1}/{self._page_stack.count()}")

    def _go_previous(self) -> None:
        """Wechselt zur vorherigen Seite (endlos: 1 -> 3)."""
        idx = (self._page_stack.currentIndex() - 1) % self._page_stack.count()
        self._page_stack.setCurrentIndex(idx)
        self._update_page_indicator()
        self._reset_inactivity_timer()
        logger.debug(f"AboutWidget Seite: {idx + 1}/{self._page_stack.count()}")

    def _update_page_indicator(self) -> None:
        """Aktualisiert die Seitenanzeige (z.B. '2/3')."""
        current = self._page_stack.currentIndex() + 1
        total = self._page_stack.count()
        self._page_indicator.setText(f"{current}/{total}")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Behandelt Click-Outside-to-Close und Swipe-Geste.

        Click-Outside: Schliesst Content bei Klick ausserhalb des Widgets.
        Swipe: Erkennt horizontale Wischgeste auf dem Page-Stack fuer
        Seitenwechsel (Links-Swipe = naechste, Rechts-Swipe = vorherige).

        Args:
            watched: Beobachtetes Objekt
            event: Qt-Event

        Returns:
            True wenn Swipe erkannt (Event konsumiert), sonst False
        """
        # Swipe-Erkennung auf Page-Stack
        if watched is self._page_stack and self._is_expanded:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._swipe_start_x = event.position().x()
            elif (event.type() == QEvent.Type.MouseButtonRelease
                    and self._swipe_start_x is not None):
                dx = event.position().x() - self._swipe_start_x
                self._swipe_start_x = None
                if abs(dx) > _SWIPE_THRESHOLD:
                    if dx < 0:
                        self._go_next()
                    else:
                        self._go_previous()
                    return True

        # Click-Outside-to-Close + Interaktions-Reset (Application-Level).
        # Innen-Klick und Scrollen (Wheel) im Widget gelten als Interaktion
        # und setzen den Inaktivitaets-Timer zurueck (Option A / Q3).
        if self._is_expanded and event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.Wheel,
        ):
            global_pos = event.globalPosition().toPoint()
            local_pos = self.mapFromGlobal(global_pos)
            inside = self.rect().contains(local_pos)

            if (event.type() == QEvent.Type.MouseButtonPress
                    and not inside):
                self._collapse()
            elif inside:
                self._reset_inactivity_timer()

        return super().eventFilter(watched, event)

    def update_language(self, language: str) -> None:
        """Aktualisiert Seiteninhalte fuer die angegebene Sprache.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        pages = self._all_pages.get(language, [])
        for i in range(self._page_stack.count()):
            if i < len(pages):
                page_widget = self._page_stack.widget(i)
                page_widget.setHtml(pages[i])

        logger.debug(f"AboutWidget Sprache aktualisiert: {language}")
