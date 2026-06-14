"""Vollbild-UI fuer Museumsbesucher.

Verantwortlichkeiten:
- Layer-Navigation-Buttons (via LayerButtonBar)
- Visualisierungs-Anzeige (via CameraDisplayWidget)
- Erklaerungstexte anzeigen (via InfoPanel)
- Touch-optimierte Bedienelemente
- Sprachwechsel (DE/EN) via Language-Toggle-Button
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSlot, pyqtSignal, QSize
from PyQt6.QtGui import QCursor, QPixmap, QIcon, QResizeEvent

from core.facade import ApplicationFacade
from view.camera_thread import CameraThread
from view.media.content.info_panel_content import LAYER_DESCRIPTIONS
from view.media.content.layer_button_bar_content import BUTTON_LABELS
from view.widgets import (
    CameraDisplayWidget, LayerButtonBar, InfoPanel, AboutWidget,
    OutputRankingWidget, GradCAMWidget, TitleTextWidget,
    GradCAMSubtitleWidget, IconBarBgWidget,
)
from view.styles import (
    CURSOR_DIMS, DISPLAY_DIMS, ABOUT_DIMS, OUTPUT_RANKING_DIMS, GRADCAM_DIMS,
    INFO_PANEL_DIMS, OVERLAY_DIMS, ICON_BAR_DIMS, TITLE_TEXT_DIMS,
    GRADCAM_SUBTITLE_DIMS,
)


logger = logging.getLogger(__name__)

_LANG_ICON_PATH = Path(__file__).parent / "media" / "icon" / "lang_flag.png"
_FRAME_PATH = Path(__file__).parent / "media" / "img" / "bg0.png"
_CURSOR_PATH = Path(__file__).parent / "media" / "icon" / "cursor.png"
_CURSOR_CLICKED_PATH = Path(__file__).parent / "media" / "icon" / "cursor_clicked.png"


class VisitorModeWidget(QWidget):
    """Widget fuer den Besuchermodus.

    Zeigt die Layer-Visualisierung mit grossen, touch-optimierten
    Buttons fuer die Layer-Navigation.

    Signals:
        language_changed(str): Emittiert bei Sprachwechsel ("de" oder "en")

    Attributes:
        _facade: ApplicationFacade fuer Business-Logik
        _camera_thread: Thread fuer Frame-Verarbeitung
        _current_layer: Aktuell angezeigter Layer
        _language: Aktuelle Sprache ("de" oder "en")
        _camera_display: CameraDisplayWidget fuer Kamera-Feed
        _button_bar: LayerButtonBar fuer Layer-Auswahl
        _info_panel: InfoPanel fuer Layer-Beschreibungen
        _about_widget: AboutWidget fuer About-Informationen
        _gradcam_widget: GradCAMWidget fuer GradCAM-Visualisierung
        _title_text: TitleTextWidget fuer bilingualen Titel-Text
        _gradcam_subtitle: GradCAMSubtitleWidget fuer GradCAM-Untertitel
        _lang_toggle: QPushButton fuer Sprachwechsel
    """

    language_changed = pyqtSignal(str)

    def __init__(self, facade: ApplicationFacade):
        """Initialisiert das VisitorModeWidget.

        Args:
            facade: ApplicationFacade-Instanz
        """
        super().__init__()

        self._facade = facade
        self._camera_thread: CameraThread | None = None

        # Dynamisch ersten Layer aus Facade holen (nicht hardcoded)
        layer_names = facade.get_layer_names()
        self._current_layer = layer_names[0] if layer_names else "layer1"
        logger.info(f"Initial Layer: {self._current_layer}")

        # Language-State
        self._language: str = "de"

        # Widgets (werden in _init_ui erstellt)
        self._camera_display: CameraDisplayWidget | None = None
        self._button_bar: LayerButtonBar | None = None
        self._info_panel: InfoPanel | None = None
        self._about_widget: AboutWidget | None = None
        self._output_ranking: OutputRankingWidget | None = None
        self._gradcam_widget: GradCAMWidget | None = None
        self._title_text: TitleTextWidget | None = None
        self._gradcam_subtitle: GradCAMSubtitleWidget | None = None
        self._lang_toggle: QPushButton | None = None
        self._frame_overlay: QLabel | None = None
        self._icon_bar_bg: IconBarBgWidget | None = None
        self._cursor_normal: QCursor | None = None
        self._cursor_clicked: QCursor | None = None
        self._cursor_visible: bool = False

        self._init_ui()

        logger.info("VisitorModeWidget initialisiert")

    def _init_ui(self) -> None:
        """Initialisiert das UI-Layout."""
        # Hauptlayout (randlos — Rahmen kommt via Frame-Overlay)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Kamera-Display Widget (fullscreen-faehig)
        self._camera_display = CameraDisplayWidget(self)
        self._camera_display.setMinimumSize(
            DISPLAY_DIMS.visitor_min_width,
            DISPLAY_DIMS.visitor_min_height
        )
        main_layout.addWidget(self._camera_display, stretch=1)

        # Layer-Button-Bar Widget (Overlay-Position wird in resizeEvent gesetzt)
        layer_names = self._facade.get_layer_names()

        self._button_bar = LayerButtonBar(layer_names, BUTTON_LABELS, self)
        self._button_bar.layer_selected.connect(self._on_layer_selected)
        self._button_bar.layout_ready.connect(self._position_overlays)
        self._button_bar.set_active_layer(self._current_layer)

        # Info-Panel Widget (Overlay-Position wird in resizeEvent gesetzt)
        self._info_panel = InfoPanel(self)

        # About-Widget (Overlay-Position wird in resizeEvent gesetzt)
        self._about_widget = AboutWidget(self)
        self._about_widget.expanded_changed.connect(self._on_about_expanded_changed)

        # Output-Ranking-Widget (Overlay-Position wird in resizeEvent gesetzt)
        self._output_ranking = OutputRankingWidget(self)

        # GradCAM-Widget (Overlay-Position wird in resizeEvent gesetzt)
        last_two_layers = self._facade.get_layer_names()[-2:]
        self._gradcam_widget = GradCAMWidget(
            visible_layers=last_two_layers, parent=self
        )

        # GradCAM-Subtitle-Widget (Overlay-Position wird in resizeEvent gesetzt)
        self._gradcam_subtitle = GradCAMSubtitleWidget(
            visible_layers=last_two_layers, parent=self
        )

        # Title-Text-Widget (Overlay-Position wird in resizeEvent gesetzt)
        self._title_text = TitleTextWidget(self)

        # Language-Toggle-Button
        self._lang_toggle = QPushButton(self)
        self._lang_toggle.setObjectName("about-icon-button")
        self._lang_toggle.clicked.connect(self._on_language_toggled)
        self._setup_lang_icon()

        # Custom-Cursor (PNG-basiert, Größe via CURSOR_DIMS in dimensions.py)
        self._setup_custom_cursor()

        # Icon-Bar-Hintergrund (dekorativ, hinter About + Language Icons)
        self._icon_bar_bg = IconBarBgWidget(self)
        logger.debug("IconBarBgWidget erstellt")

        # Frame-Overlay (dekorativer HUD-Rahmen ueber dem Kamera-Feed)
        self._frame_overlay = QLabel(self)
        self._frame_overlay.setScaledContents(True)
        self._frame_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        frame_pixmap = QPixmap(str(_FRAME_PATH))
        if not frame_pixmap.isNull():
            self._frame_overlay.setPixmap(frame_pixmap)
            logger.debug(f"Frame-Overlay geladen: {_FRAME_PATH}")
        else:
            logger.warning(f"Frame-Overlay nicht ladbar: {_FRAME_PATH}")

        # Initial: Layer-Info aktualisieren
        self._update_layer_info(self._current_layer)

        # Overlay-Positionierung
        self._position_overlays()

        logger.debug("UI erstellt")

    def _setup_custom_cursor(self) -> None:
        """Setzt PNG-Cursor auf das VisitorModeWidget.

        Fallback auf Standard-Cursor wenn eine oder beide PNGs nicht ladbar sind.
        """
        size = CURSOR_DIMS.size
        hotspot = size // 2

        pixmap = QPixmap(str(_CURSOR_PATH))
        pixmap_clicked = QPixmap(str(_CURSOR_CLICKED_PATH))

        if pixmap.isNull() or pixmap_clicked.isNull():
            logger.warning("Custom-Cursor PNGs nicht ladbar – Standard-Cursor wird verwendet")
            return

        self._cursor_normal = QCursor(
            pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            hotspot, hotspot,
        )
        self._cursor_clicked = QCursor(
            pixmap_clicked.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            hotspot, hotspot,
        )
        logger.debug(f"Custom-Cursor geladen (size={size}px)")

    def _setup_lang_icon(self) -> None:
        """Setzt Icon auf Language-Toggle-Button, mit Text-Fallback."""
        pixmap = QPixmap(str(_LANG_ICON_PATH))

        icon_size = ICON_BAR_DIMS.flag_icon_size
        button_size = icon_size + OVERLAY_DIMS.icon_button_padding

        if not pixmap.isNull():
            self._lang_toggle.setIcon(QIcon(pixmap))
            self._lang_toggle.setIconSize(QSize(icon_size, icon_size))
            self._lang_toggle.setFixedSize(button_size, button_size)
            logger.debug(f"Language-Icon geladen: {_LANG_ICON_PATH}")
        else:
            self._lang_toggle.setText("DE/EN")
            self._lang_toggle.setFixedSize(button_size, button_size)
            logger.warning(f"Language-Icon nicht ladbar, Text-Fallback: {_LANG_ICON_PATH}")

    def _position_overlays(self) -> None:
        """Positioniert Overlay-Widgets (Button-Bar, Info-Panel, About-Widget, Output-Ranking, GradCAM, Language-Toggle).

        Diese Methode wird bei resizeEvent() aufgerufen, um die Overlays
        korrekt ueber dem Kamera-Display zu positionieren.
        """
        if not self._button_bar or not self._info_panel:
            return

        # Frame-Overlay: Volle Fenstergroesse (unterhalb aller Overlays)
        if self._frame_overlay:
            self._frame_overlay.setGeometry(0, 0, self.width(), self.height())
            self._frame_overlay.raise_()

        # Title-Text: Oben zentriert
        if self._title_text:
            title_width = self.width() // 2
            title_height = 40
            title_x = (self.width() - title_width) // 2
            title_y = TITLE_TEXT_DIMS.margin_top
            self._title_text.setGeometry(title_x, title_y, title_width, title_height)
            self._title_text.raise_()

        # Button-Bar: Unten zentriert
        bar_width = self._button_bar.sizeHint().width()
        bar_height = self._button_bar.sizeHint().height()
        bar_x = (self.width() - bar_width) // 2
        bar_y = self.height() - bar_height - OVERLAY_DIMS.button_bar_margin
        self._button_bar.setGeometry(bar_x, bar_y, bar_width, bar_height)
        self._button_bar.raise_()

        # Info-Panel: Rechts oben
        panel_width = INFO_PANEL_DIMS.width
        panel_height = INFO_PANEL_DIMS.height
        x = self.width() - panel_width - INFO_PANEL_DIMS.margin_right
        y = INFO_PANEL_DIMS.margin_top
        self._info_panel.setGeometry(x, y, panel_width, panel_height)
        self._info_panel.raise_()

        # Icon-Bar-Hintergrund: Rechts oben
        bar_bg_x = self.width() - ICON_BAR_DIMS.width - ICON_BAR_DIMS.margin_right
        bar_bg_y = ICON_BAR_DIMS.margin_top
        if self._icon_bar_bg:
            self._icon_bar_bg.setGeometry(
                bar_bg_x, bar_bg_y,
                ICON_BAR_DIMS.width, ICON_BAR_DIMS.height,
            )
            self._icon_bar_bg.raise_()

        # About-Widget: Rechts in der Icon-Bar (Icon via AlignRight)
        # MUSS vor lang_toggle geraised werden, da AboutWidget 300px breit ist
        # und sonst den lang_toggle verdeckt
        if self._about_widget:
            button_size = ABOUT_DIMS.icon_size + OVERLAY_DIMS.icon_button_padding
            # About-Icon soll rechts in der Bar sitzen
            icon_right_x = bar_bg_x + ICON_BAR_DIMS.width - ICON_BAR_DIMS.padding
            # AboutWidget so positionieren, dass sein Icon (AlignRight) hier landet
            about_x = icon_right_x - ABOUT_DIMS.content_width
            about_y = bar_bg_y + (ICON_BAR_DIMS.height - button_size) // 2
            self._about_widget.move(about_x, about_y)
            self._about_widget.raise_()

        # Language-Toggle: Links in der Icon-Bar (NACH About, damit darüber)
        if self._lang_toggle:
            toggle_size = self._lang_toggle.size()
            toggle_x = bar_bg_x + ICON_BAR_DIMS.padding
            toggle_y = bar_bg_y + (ICON_BAR_DIMS.height - toggle_size.height()) // 2
            self._lang_toggle.move(toggle_x, toggle_y)
            self._lang_toggle.raise_()

        # Output-Ranking: Rechts neben der Button-Bar
        if self._output_ranking:
            ranking_width = OUTPUT_RANKING_DIMS.width
            ranking_height = OUTPUT_RANKING_DIMS.height
            ranking_x = bar_x + bar_width + OVERLAY_DIMS.output_ranking_gap
            ranking_y = bar_y + (bar_height - ranking_height) // 2
            self._output_ranking.setGeometry(
                ranking_x, ranking_y, ranking_width, ranking_height
            )
            self._output_ranking.raise_()

        # GradCAM-Widget: Links, vertikal zentriert
        if self._gradcam_widget:
            gradcam_x = GRADCAM_DIMS.margin_left
            gradcam_y = (self.height() - GRADCAM_DIMS.height) // 2
            self._gradcam_widget.setGeometry(
                gradcam_x, gradcam_y,
                GRADCAM_DIMS.width, GRADCAM_DIMS.height,
            )
            self._gradcam_widget.raise_()

        # GradCAM-Subtitle: Mittig unterhalb des GradCAM-Widgets
        if self._gradcam_subtitle:
            subtitle_width = self.width() // 3
            subtitle_height = 40
            gradcam_bottom_x = GRADCAM_DIMS.margin_left
            gradcam_bottom_y = (self.height() - GRADCAM_DIMS.height) // 2 + GRADCAM_DIMS.height
            subtitle_x = gradcam_bottom_x + (GRADCAM_DIMS.width - subtitle_width) // 2
            subtitle_y = gradcam_bottom_y + GRADCAM_SUBTITLE_DIMS.gap_to_gradcam
            self._gradcam_subtitle.setGeometry(
                subtitle_x, subtitle_y, subtitle_width, subtitle_height
            )
            self._gradcam_subtitle.raise_()

        logger.debug("Overlays positioniert")

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Event-Handler fuer Widget-Resize.

        Repositioniert Overlays bei Groessenaenderung (z.B. Fullscreen).

        Args:
            event: QResizeEvent
        """
        super().resizeEvent(event)
        self._position_overlays()

    @pyqtSlot(str)
    def _on_layer_selected(self, layer_name: str) -> None:
        """Behandelt Layer-Auswahl von LayerButtonBar.

        Args:
            layer_name: Ausgewaehlter Layer
        """
        logger.info(f"Layer ausgewaehlt: {layer_name}")

        if layer_name != self._current_layer:
            logger.info(f"Layer-Wechsel: {self._current_layer} -> {layer_name}")
            self._current_layer = layer_name
            self._facade.change_layer(layer_name)
            self._update_layer_info(layer_name)

            # GradCAM-Widget Visibility aktualisieren
            if self._gradcam_widget:
                self._gradcam_widget.set_current_layer(layer_name)

            # GradCAM-Subtitle Visibility aktualisieren
            if self._gradcam_subtitle:
                self._gradcam_subtitle.set_current_layer(layer_name)

            # Camera-Thread updaten
            if self._camera_thread and self._camera_thread.is_running:
                self._camera_thread.change_layer(layer_name)
        else:
            logger.debug(f"Layer bereits aktiv: {layer_name}")

    def _update_layer_info(self, layer_name: str) -> None:
        """Aktualisiert Beschreibungstext fuer Layer.

        Args:
            layer_name: Layer-Name
        """
        lang_descriptions = LAYER_DESCRIPTIONS.get(self._language, {})
        description_html = lang_descriptions.get(
            layer_name,
            "<p><i>Keine Beschreibung verfügbar</i></p>"
        )
        self._info_panel.set_content(description_html)

        logger.debug(f"Layer-Info aktualisiert: {layer_name} ({self._language})")

    def _on_about_expanded_changed(self, expanded: bool) -> None:
        """Blendet InfoPanel aus solange AboutWidget expanded ist.

        Args:
            expanded: True wenn AboutWidget geöffnet, False wenn geschlossen
        """
        if self._info_panel:
            self._info_panel.setVisible(not expanded)

    def _on_language_toggled(self) -> None:
        """Wechselt Sprache und aktualisiert alle Widgets."""
        self._language = "en" if self._language == "de" else "de"
        logger.info(f"Sprache gewechselt: {self._language}")

        # Alle Overlay-Widgets aktualisieren
        for widget in [
            self._button_bar, self._about_widget,
            self._output_ranking, self._gradcam_widget,
            self._title_text, self._gradcam_subtitle,
        ]:
            if widget:
                widget.update_language(self._language)

        # Layer-Info aktualisieren (InfoPanel wird via set_content gesteuert)
        self._update_layer_info(self._current_layer)

        # MainWindow benachrichtigen (App-Titel)
        self.language_changed.emit(self._language)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """App-Level EventFilter fuer Cursor-Klick-Feedback.

        Wechselt bei MouseButtonPress auf den geklickten Cursor und
        stellt bei MouseButtonRelease den normalen Cursor wieder her.
        Gibt immer False zurueck, damit Events nicht abgefangen werden.

        Args:
            obj: Empfaenger-Objekt des Events
            event: Qt-Event
        """
        if self._cursor_normal is not None:
            t = event.type()
            if t == QEvent.Type.MouseMove:
                if not self._cursor_visible:
                    QApplication.changeOverrideCursor(self._cursor_normal)
                    self._cursor_visible = True
            elif t == QEvent.Type.MouseButtonPress:
                QApplication.changeOverrideCursor(self._cursor_clicked)
                self._cursor_visible = True
            elif t == QEvent.Type.MouseButtonRelease:
                QApplication.changeOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
                self._cursor_visible = False
        return False

    @pyqtSlot(str)
    def _on_error_occurred(self, error_msg: str) -> None:
        """Behandelt Fehler vom CameraThread.

        Args:
            error_msg: Fehlermeldung
        """
        logger.error(f"Fehler in CameraThread: {error_msg}")
        self._camera_display.setText(f"Fehler:\n{error_msg}")

    def start(self) -> None:
        """Startet den Besuchermodus (CameraThread)."""
        if self._camera_thread and self._camera_thread.is_running:
            logger.debug("CameraThread laeuft bereits")
            return

        logger.info("Starte VisitorMode")
        if self._cursor_normal is not None:
            self._cursor_visible = False
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
            QApplication.instance().installEventFilter(self)

        self._camera_thread = CameraThread(self._facade, self._current_layer)
        self._camera_thread.frame_ready.connect(self._camera_display.update_frame)
        self._camera_thread.predictions_ready.connect(self._output_ranking.update_predictions)
        self._camera_thread.gradcam_ready.connect(self._gradcam_widget.update_frame)
        self._camera_thread.error_occurred.connect(self._on_error_occurred)
        self._camera_thread.set_gradcam_layers(self._facade.get_layer_names()[-2:])
        self._camera_thread.start()

    def stop(self) -> None:
        """Stoppt den Besuchermodus (CameraThread)."""
        if not self._camera_thread:
            return

        logger.info("Stoppe VisitorMode")
        if self._cursor_normal is not None:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
            self._cursor_visible = False
            QApplication.instance().removeEventFilter(self)

        if self._camera_thread.is_running:
            self._camera_thread.stop()

        self._camera_thread = None

        self._camera_display.clear()
        self._camera_display.setText("Kamera gestoppt")
