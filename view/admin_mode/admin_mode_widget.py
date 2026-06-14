"""Admin-Modus für Preset-Konfiguration.

Verantwortlichkeiten:
- Layer-Auswahl
- Preset-Editor (bis zu 3 Presets pro Layer)
- Channel-Auswahl UI
- Visualisierungsparameter-Controls
- Live-Vorschau
- Speichern-Button
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QCheckBox, QGroupBox, QScrollArea, QMessageBox,
    QGridLayout, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from core.facade import ApplicationFacade
from view.camera_thread import CameraThread
from view.admin_mode.channel_manager import ChannelSpinBox, ChannelManager
from view.admin_mode.preset_builder import PresetBuilder
from view.widgets import CameraDisplayWidget
from view.styles import StyleManager, DISPLAY_DIMS
from view.styles.colors import DANGER, DANGER_HOVER, SUCCESS, SUCCESS_HOVER, TEXT_PRIMARY


# Maximaler Channel-Index eines ResNet18-Layers (512 Channels, 0-basiert)
MAX_CHANNEL_INDEX = 511

logger = logging.getLogger(__name__)


class AdminModeWidget(QWidget):
    """Widget für den Admin-Modus.

    Ermöglicht die Konfiguration von Presets für jeden Layer
    mit Live-Vorschau. Delegiert Channel-Verwaltung an ChannelManager
    und PresetConfig-Erstellung an PresetBuilder.

    Attributes:
        _facade: ApplicationFacade für Business-Logik
        _camera_thread: Thread für Frame-Verarbeitung
        _current_layer: Aktuell bearbeiteter Layer
        _current_preset_id: Aktuell bearbeitetes Preset
    """

    def __init__(self, facade: ApplicationFacade):
        """Initialisiert das AdminModeWidget.

        Args:
            facade: ApplicationFacade-Instanz
        """
        super().__init__()

        self._facade = facade
        self._camera_thread: CameraThread | None = None
        # Initialisiere _current_layer mit dem ersten Layer aus get_layer_names()
        # um Konsistenz mit UI (ComboBox) zu gewährleisten
        layer_names = facade.get_layer_names()
        self._current_layer = layer_names[0] if layer_names else "layer1"
        self._current_preset_id = 0

        # UI-Komponenten
        self._preview_display: CameraDisplayWidget | None = None
        self._layer_combo: QComboBox | None = None
        self._preset_combo: QComboBox | None = None
        self._preset_name_input: QLabel | None = None

        # Mode-Selection Radio-Buttons
        self._colormap_radio: QRadioButton | None = None
        self._rgb_radio: QRadioButton | None = None
        self._mode_button_group: QButtonGroup | None = None

        # Colormap-Mode UI
        self._colormap_mode_group: QGroupBox | None = None
        self._channel_inputs: list[ChannelSpinBox] = []
        self._channel_delete_buttons: list[QPushButton | None] = []  # "X" Buttons für Channel 2 & 3
        self._add_channel_button: QPushButton | None = None  # "+" Button
        self._channel_rows: list[QWidget] = []  # Container für Channel-Rows
        self._colormap_combo: QComboBox | None = None

        # RGB-Mode UI
        self._rgb_mode_group: QGroupBox | None = None
        self._rgb_channel_inputs: list[ChannelSpinBox] = []  # Genau 3: R, G, B

        # Common UI
        self._normalize_check: QCheckBox | None = None
        self._blend_mode_combo: QComboBox | None = None
        self._blend_mode_row: QWidget | None = None

        # Channel-Manager (wird in _init_ui nach UI-Erstellung initialisiert)
        self._channel_mgr: ChannelManager | None = None

        self._init_ui()

        # Initial Layer-Wechsel triggern um _current_layer mit UI zu synchronisieren
        # und alle Layer-abhängigen Komponenten korrekt zu initialisieren
        if self._layer_combo:
            self._on_layer_changed(self._layer_combo.currentText())

        logger.info("AdminModeWidget initialisiert")

    def _init_ui(self) -> None:
        """Initialisiert das UI-Layout."""
        # Hauptlayout (horizontal)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Linke Seite: Preset-Editor
        editor_layout = self._create_editor_panel()
        main_layout.addLayout(editor_layout, stretch=1)

        # Rechte Seite: Live-Vorschau
        preview_layout = self._create_preview_panel()
        main_layout.addLayout(preview_layout, stretch=2)

        # ChannelManager erstellen (alle UI-Elemente existieren jetzt)
        self._channel_mgr = ChannelManager(
            spinboxes=self._channel_inputs,
            rgb_spinboxes=self._rgb_channel_inputs,
            rows=self._channel_rows,
            delete_buttons=self._channel_delete_buttons,
            add_button=self._add_channel_button,
        )

        # Initial: Channel-Range für ersten Layer setzen
        self._update_channel_range(self._current_layer)

        # Initial: Preset laden
        self._load_current_preset()

        logger.debug("Admin UI erstellt")

    def _create_editor_panel(self) -> QVBoxLayout:
        """Erstellt das Preset-Editor-Panel.

        Returns:
            QVBoxLayout mit Editor-Controls
        """
        layout = QVBoxLayout()

        layout.addWidget(self._create_editor_title())
        layout.addWidget(self._create_layer_section())
        layout.addWidget(self._create_preset_section())
        layout.addWidget(self._create_params_section())
        layout.addWidget(self._create_save_button())
        layout.addWidget(self._create_set_active_button())

        return layout

    def _create_editor_title(self) -> QLabel:
        """Erstellt den Titel des Editor-Panels."""
        title_label = QLabel("Preset-Editor")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        return title_label

    def _create_layer_section(self) -> QGroupBox:
        """Erstellt die Layer-Auswahl-Section."""
        layer_group = QGroupBox("Layer auswählen")
        layer_layout = QVBoxLayout(layer_group)

        self._layer_combo = QComboBox()
        layer_names = self._facade.get_layer_names()
        self._layer_combo.addItems(layer_names)
        self._layer_combo.currentTextChanged.connect(self._on_layer_changed)
        layer_layout.addWidget(self._layer_combo)

        return layer_group

    def _create_preset_section(self) -> QGroupBox:
        """Erstellt die Preset-Auswahl-Section."""
        preset_group = QGroupBox("Preset auswählen")
        preset_layout = QVBoxLayout(preset_group)

        self._preset_combo = QComboBox()
        self._preset_combo.addItems(["Preset 1", "Preset 2", "Preset 3"])
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self._preset_combo)

        return preset_group

    def _create_params_section(self) -> QGroupBox:
        """Erstellt die scrollbare Parameter-Section.

        Enthält: Preset-Name, Modus-Auswahl, Colormap-Einstellungen,
        RGB-Einstellungen, Normalize und Blend-Mode.
        """
        params_group = QGroupBox("Parameter")
        params_scroll = QScrollArea()
        params_scroll.setWidgetResizable(True)
        params_scroll.setMinimumHeight(400)

        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)

        # Preset-Name (aktuell nur Anzeige)
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self._preset_name_input = QLabel()
        name_layout.addWidget(self._preset_name_input)
        params_layout.addLayout(name_layout)

        # Mode-Selection
        params_layout.addWidget(self._create_mode_section())

        # Colormap-Mode UI
        self._colormap_mode_group = self._create_colormap_section()
        params_layout.addWidget(self._colormap_mode_group)

        # RGB-Mode UI
        self._rgb_mode_group = self._create_rgb_section()
        params_layout.addWidget(self._rgb_mode_group)

        # Normalize
        self._normalize_check = QCheckBox("Normalisierung aktiviert")
        self._normalize_check.setChecked(True)
        self._normalize_check.stateChanged.connect(self._on_param_changed)
        params_layout.addWidget(self._normalize_check)

        # Blend Mode (in eigenes Widget gewrappt für Visibility-Control)
        self._blend_mode_row = QWidget()
        blend_layout = QHBoxLayout(self._blend_mode_row)
        blend_layout.setContentsMargins(0, 0, 0, 0)
        blend_layout.addWidget(QLabel("Blend-Modus:"))
        self._blend_mode_combo = QComboBox()
        self._blend_mode_combo.addItems(["max", "mean", "overlay"])
        self._blend_mode_combo.currentTextChanged.connect(self._on_param_changed)
        blend_layout.addWidget(self._blend_mode_combo)
        params_layout.addWidget(self._blend_mode_row)

        params_layout.addStretch()
        params_scroll.setWidget(params_widget)
        params_group.setLayout(QVBoxLayout())
        params_group.layout().addWidget(params_scroll)

        return params_group

    def _create_mode_section(self) -> QGroupBox:
        """Erstellt die Visualisierungsmodus-Auswahl (Colormap/RGB)."""
        mode_group = QGroupBox("Visualisierungsmodus")
        mode_layout = QHBoxLayout(mode_group)

        self._colormap_radio = QRadioButton("Colormap")
        self._colormap_radio.setChecked(True)
        self._rgb_radio = QRadioButton("RGB")

        self._mode_button_group = QButtonGroup()
        self._mode_button_group.addButton(self._colormap_radio)
        self._mode_button_group.addButton(self._rgb_radio)

        mode_layout.addWidget(self._colormap_radio)
        mode_layout.addWidget(self._rgb_radio)

        self._colormap_radio.toggled.connect(self._on_mode_changed)

        return mode_group

    def _create_colormap_section(self) -> QGroupBox:
        """Erstellt die Colormap-Einstellungen mit dynamischen Channels."""
        colormap_group = QGroupBox("Colormap-Einstellungen")
        colormap_layout = QVBoxLayout(colormap_group)

        # Channel-Auswahl (bis zu 3 Channels, dynamisch)
        channels_group_layout = QVBoxLayout()
        channels_group_layout.addWidget(QLabel("Channels:"))

        self._channels_container = QWidget()
        self._channels_grid = QGridLayout(self._channels_container)
        self._channels_grid.setContentsMargins(0, 0, 0, 0)

        for i in range(3):
            # Row-Container für jeden Channel
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)

            label = QLabel(f"Channel {i+1}:")
            label.setMinimumWidth(70)
            row_layout.addWidget(label)

            spinbox = ChannelSpinBox()
            spinbox.setRange(-1, MAX_CHANNEL_INDEX)  # -1 erlaubt für "nicht ausgewählt" (nur programmatisch)
            spinbox.setProgrammaticValue(i)  # Initial-Wert programmatisch setzen
            spinbox.setSpecialValueText("")  # -1 wird als leer angezeigt
            spinbox.valueChanged.connect(self._on_param_changed)
            row_layout.addWidget(spinbox)
            self._channel_inputs.append(spinbox)

            # Delete-Button nur für Channel 2 und 3 (Index 1 und 2)
            if i > 0:
                delete_btn = QPushButton("-")
                delete_btn.setFixedSize(30, 25)
                # Custom Style mit reduziertem Padding für kleine Icon-Buttons
                delete_style = f"""
                    QPushButton {{
                        background-color: {DANGER};
                        color: {TEXT_PRIMARY};
                        font-weight: bold;
                        font-size: 16px;
                        border-radius: 3px;
                        padding: 0px;
                        border: none;
                    }}
                    QPushButton:hover {{
                        background-color: {DANGER_HOVER};
                    }}
                """
                delete_btn.setStyleSheet(delete_style)
                delete_btn.clicked.connect(lambda checked, idx=i: self._on_delete_channel(idx))
                row_layout.addWidget(delete_btn)
                self._channel_delete_buttons.append(delete_btn)
            else:
                # Placeholder für Channel 1 (kein Delete)
                self._channel_delete_buttons.append(None)

            self._channels_grid.addWidget(row_widget, i, 0)
            self._channel_rows.append(row_widget)

        channels_group_layout.addWidget(self._channels_container)

        # "+" Button zum Hinzufügen
        self._add_channel_button = QPushButton("+")
        self._add_channel_button.setFixedSize(30, 25)
        # Custom Style mit reduziertem Padding für kleine Icon-Buttons
        add_style = f"""
            QPushButton {{
                background-color: {SUCCESS};
                color: {TEXT_PRIMARY};
                font-weight: bold;
                font-size: 16px;
                border-radius: 3px;
                padding: 0px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {SUCCESS_HOVER};
            }}
        """
        self._add_channel_button.setStyleSheet(add_style)
        self._add_channel_button.clicked.connect(self._on_add_channel)
        channels_group_layout.addWidget(
            self._add_channel_button, alignment=Qt.AlignmentFlag.AlignLeft
        )

        colormap_layout.addLayout(channels_group_layout)

        # Colormap-Combo
        colormap_combo_layout = QHBoxLayout()
        colormap_combo_layout.addWidget(QLabel("Colormap:"))
        self._colormap_combo = QComboBox()
        self._colormap_combo.addItems([
            "viridis", "plasma", "inferno", "magma", "jet", "hot"
        ])
        self._colormap_combo.currentTextChanged.connect(self._on_param_changed)
        colormap_combo_layout.addWidget(self._colormap_combo)
        colormap_layout.addLayout(colormap_combo_layout)

        return colormap_group

    def _create_rgb_section(self) -> QGroupBox:
        """Erstellt die RGB-Einstellungen (initial versteckt)."""
        rgb_group = QGroupBox("RGB-Einstellungen")
        rgb_group.setVisible(False)
        rgb_layout = QVBoxLayout(rgb_group)

        rgb_layout.addWidget(QLabel("Channel-Zuordnung:"))

        for i, color_name in enumerate(['Rot', 'Grün', 'Blau']):
            row_layout = QHBoxLayout()

            label = QLabel(f"{color_name}:")
            label.setMinimumWidth(70)
            row_layout.addWidget(label)

            spinbox = ChannelSpinBox()
            spinbox.setRange(0, MAX_CHANNEL_INDEX)
            spinbox.setValue(i)  # Initial: 0, 1, 2
            spinbox.valueChanged.connect(self._on_param_changed)
            row_layout.addWidget(spinbox)

            rgb_layout.addLayout(row_layout)
            self._rgb_channel_inputs.append(spinbox)

        return rgb_group

    def _create_save_button(self) -> QPushButton:
        """Erstellt den Speichern-Button."""
        save_button = QPushButton("Preset speichern")
        save_button.setMinimumHeight(50)
        save_button.setStyleSheet(StyleManager.get_button_style("success"))
        save_button.clicked.connect(self._save_current_preset)
        return save_button

    def _create_set_active_button(self) -> QPushButton:
        """Erstellt den 'Als aktiv markieren'-Button."""
        set_active_button = QPushButton("Als aktiv markieren")
        set_active_button.setMinimumHeight(40)
        set_active_button.clicked.connect(self._set_as_active_preset)
        return set_active_button

    def _create_preview_panel(self) -> QVBoxLayout:
        """Erstellt das Live-Vorschau-Panel.

        Returns:
            QVBoxLayout mit Vorschau-Display
        """
        layout = QVBoxLayout()

        # Titel
        title_label = QLabel("Live-Vorschau")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Preview-Display (CameraDisplayWidget statt QLabel)
        self._preview_display = CameraDisplayWidget()
        self._preview_display.setMinimumSize(
            DISPLAY_DIMS.admin_preview_width,
            DISPLAY_DIMS.admin_preview_height
        )
        layout.addWidget(self._preview_display, stretch=1)

        # Info-Text
        info_label = QLabel(
            "Änderungen werden live angezeigt.\n"
            "Drücken Sie 'Preset speichern' um die Einstellungen zu übernehmen."
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        return layout

    @pyqtSlot(str)
    def _on_layer_changed(self, layer_name: str) -> None:
        """Behandelt Layer-Wechsel.

        Args:
            layer_name: Neuer Layer
        """
        if layer_name == self._current_layer:
            return

        logger.info(f"Admin: Layer-Wechsel zu {layer_name}")
        self._current_layer = layer_name

        # Channel-Range für neuen Layer aktualisieren
        self._update_channel_range(layer_name)

        # Preset-Selector auf aktives Preset des neuen Layers synchronisieren
        try:
            active_preset = self._facade.get_active_preset(layer_name)
            active_id = active_preset.preset_id

            if active_id != self._current_preset_id:
                self._current_preset_id = active_id
                self._preset_combo.setCurrentIndex(active_id)
                logger.info(
                    f"Admin: Layer-Wechsel - Preset-Selector synchronisiert auf "
                    f"aktives Preset {active_id + 1}"
                )
        except Exception as e:
            logger.warning(f"Konnte aktives Preset nicht abfragen: {e}")

        # Preset laden
        self._load_current_preset()

        # Camera-Thread updaten
        if self._camera_thread and self._camera_thread.is_running:
            self._camera_thread.change_layer(layer_name)
            self._on_param_changed()

    def _update_channel_range(self, layer_name: str) -> None:
        """Aktualisiert SpinBox-Range basierend auf Layer-Channel-Anzahl.

        Args:
            layer_name: Name des Layers
        """
        try:
            channel_count = self._facade.get_layer_channel_count(layer_name)
            logger.debug(f"Layer '{layer_name}' hat {channel_count} Channels")
            self._channel_mgr.update_range(channel_count)
        except Exception as e:
            logger.warning(f"Konnte Channel-Count nicht ermitteln: {e}")

    @pyqtSlot(bool)
    def _on_mode_changed(self, checked: bool) -> None:
        """Behandelt Modus-Wechsel (Colormap <-> RGB).

        Args:
            checked: True wenn Colormap-Radio aktiviert, False wenn RGB
        """
        is_colormap_mode = self._colormap_radio.isChecked()
        logger.debug(f"Admin: Modus-Wechsel zu {'Colormap' if is_colormap_mode else 'RGB'}")

        # UI-Gruppen umschalten
        self._colormap_mode_group.setVisible(is_colormap_mode)
        self._rgb_mode_group.setVisible(not is_colormap_mode)

        # Normalisierung und Blend-Mode Controls ausblenden im RGB-Mode
        self._normalize_check.setVisible(is_colormap_mode)
        self._blend_mode_row.setVisible(is_colormap_mode)

        # Bei Wechsel zu RGB-Mode: Werte erzwingen
        if not is_colormap_mode:
            # Normalisierung auf True setzen
            self._normalize_check.setChecked(True)

            # Blend-Mode auf "max" setzen
            blend_index = self._blend_mode_combo.findText("max")
            if blend_index >= 0:
                self._blend_mode_combo.setCurrentIndex(blend_index)

            logger.debug("Admin: RGB-Mode - Normalisierung erzwungen (True), Blend-Mode erzwungen (max)")

        # Live-Vorschau aktualisieren
        self._on_param_changed()

    @pyqtSlot(int)
    def _on_preset_changed(self, preset_index: int) -> None:
        """Behandelt Preset-Wechsel.

        Args:
            preset_index: Neuer Preset-Index (0-2)
        """
        if preset_index == self._current_preset_id:
            return

        logger.info(f"Admin: Preset-Wechsel zu {preset_index}")
        self._current_preset_id = preset_index

        # Preset laden (aktualisiert UI)
        self._load_current_preset()

        # Live-Vorschau mit den neuen Preset-Werten aktualisieren
        self._on_param_changed()

    @pyqtSlot()
    def _on_param_changed(self) -> None:
        """Behandelt Parameter-Änderungen.

        Aktualisiert die Live-Vorschau ohne zu speichern.
        """
        logger.debug("Admin: Parameter geändert - Update Live-Vorschau")

        try:
            preset = PresetBuilder.build_from_ui(
                preset_id=self._current_preset_id,
                name=f"Live Preview (Preset {self._current_preset_id + 1})",
                is_rgb_mode=self._rgb_radio.isChecked(),
                channels=self._channel_mgr.get_channels(),
                rgb_channels=self._channel_mgr.get_rgb_channels(),
                colormap=self._colormap_combo.currentText(),
                normalize=self._normalize_check.isChecked(),
                blend_mode=self._blend_mode_combo.currentText(),
            )

            if self._camera_thread and self._camera_thread.is_running:
                self._camera_thread.set_temp_preset(preset)

        except Exception as e:
            logger.warning(f"Fehler beim Erstellen der Live-Vorschau: {e}")

    def _on_delete_channel(self, deleted_index: int) -> None:
        """Löscht Channel und lässt nachfolgende aufrücken.

        Args:
            deleted_index: Index des zu löschenden Channels (1 oder 2)
        """
        self._channel_mgr.delete_channel(deleted_index)
        self._on_param_changed()

    def _on_add_channel(self) -> None:
        """Aktiviert nächsten inaktiven Channel."""
        self._channel_mgr.add_channel()
        self._on_param_changed()

    def _load_current_preset(self) -> None:
        """Lädt aktuelles Preset in die UI."""
        try:
            preset = self._facade.get_preset(
                self._current_layer,
                self._current_preset_id
            )

            # UI aktualisieren
            self._preset_name_input.setText(preset.name)

            # Visualisierungsmodus setzen
            visualization_mode = getattr(preset, 'visualization_mode', 'colormap')
            is_rgb_mode = visualization_mode == 'rgb'

            # Radio-Buttons setzen
            if is_rgb_mode:
                self._rgb_radio.setChecked(True)
            else:
                self._colormap_radio.setChecked(True)

            # Controls-Visibility setzen je nach Modus
            is_colormap_mode = not is_rgb_mode
            self._normalize_check.setVisible(is_colormap_mode)
            self._blend_mode_row.setVisible(is_colormap_mode)

            # Channels je nach Modus laden
            if is_rgb_mode:
                self._channel_mgr.set_rgb_channels(preset.channels)
            else:
                self._channel_mgr.set_channels(preset.channels)
                self._channel_mgr.update_visibility()

            # Colormap (nur relevant im Colormap-Mode)
            index = self._colormap_combo.findText(preset.colormap)
            if index >= 0:
                self._colormap_combo.setCurrentIndex(index)

            # Normalize
            self._normalize_check.setChecked(preset.normalize)

            # Blend Mode
            index = self._blend_mode_combo.findText(preset.blend_mode)
            if index >= 0:
                self._blend_mode_combo.setCurrentIndex(index)

            logger.debug(f"Preset geladen: {preset.name}, mode={visualization_mode}")

        except Exception as e:
            logger.error(f"Fehler beim Laden des Presets: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Preset konnte nicht geladen werden:\n{e}"
            )

    @pyqtSlot()
    def _save_current_preset(self) -> None:
        """Speichert aktuelles Preset."""
        try:
            # Aktuellen Preset-Namen holen
            current_preset = self._facade.get_preset(
                self._current_layer,
                self._current_preset_id
            )

            preset = PresetBuilder.build_from_ui(
                preset_id=self._current_preset_id,
                name=current_preset.name,
                is_rgb_mode=self._rgb_radio.isChecked(),
                channels=self._channel_mgr.get_channels(),
                rgb_channels=self._channel_mgr.get_rgb_channels(),
                colormap=self._colormap_combo.currentText(),
                normalize=self._normalize_check.isChecked(),
                blend_mode=self._blend_mode_combo.currentText(),
            )

            # Speichern
            self._facade.save_preset(
                self._current_layer,
                self._current_preset_id,
                preset
            )

            logger.info(
                f"Preset gespeichert: {self._current_layer}/{preset.name} "
                f"(mode={preset.visualization_mode})"
            )

            QMessageBox.information(
                self,
                "Erfolg",
                f"Preset '{preset.name}' wurde gespeichert!"
            )

        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Preset konnte nicht gespeichert werden:\n{e}"
            )

    @pyqtSlot()
    def _set_as_active_preset(self) -> None:
        """Setzt aktuelles Preset als aktives Preset."""
        try:
            self._facade.set_active_preset(
                self._current_layer,
                self._current_preset_id
            )

            logger.info(
                f"Preset {self._current_preset_id} als aktiv markiert "
                f"für {self._current_layer}"
            )

            QMessageBox.information(
                self,
                "Erfolg",
                f"Preset {self._current_preset_id + 1} ist jetzt aktiv für {self._current_layer}!"
            )

        except Exception as e:
            logger.error(f"Fehler beim Setzen des aktiven Presets: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Aktives Preset konnte nicht gesetzt werden:\n{e}"
            )

    @pyqtSlot(str)
    def _on_error_occurred(self, error_msg: str) -> None:
        """Behandelt Fehler vom CameraThread.

        Args:
            error_msg: Fehlermeldung
        """
        logger.error(f"Fehler in AdminMode CameraThread: {error_msg}")
        self._preview_display.setText(f"❌ Fehler:\n{error_msg}")

    def start(self) -> None:
        """Startet den Admin-Modus."""
        if self._camera_thread and self._camera_thread.is_running:
            logger.debug("Admin CameraThread läuft bereits")
            return

        logger.info("Starte AdminMode")

        # Layer-Selector auf Facade-Layer synchronisieren (Visitor → Admin)
        facade_layer = self._facade.get_current_layer()
        if facade_layer and facade_layer != self._current_layer:
            combo_index = self._layer_combo.findText(facade_layer)
            if combo_index >= 0:
                self._layer_combo.setCurrentIndex(combo_index)

        # Preset-Selector auf aktives Preset synchronisieren
        try:
            active_preset = self._facade.get_active_preset(self._current_layer)
            active_id = active_preset.preset_id

            if active_id != self._current_preset_id:
                # _current_preset_id VOR setCurrentIndex setzen,
                # damit _on_preset_changed() per Guard (Zeile 498) early-returned
                self._current_preset_id = active_id
                self._preset_combo.setCurrentIndex(active_id)
                self._load_current_preset()
                logger.info(
                    f"Admin: Preset-Selector synchronisiert auf "
                    f"aktives Preset {active_id + 1}"
                )
        except Exception as e:
            logger.warning(f"Konnte aktives Preset nicht abfragen: {e}")

        # Camera-Thread erstellen und starten
        self._camera_thread = CameraThread(self._facade, self._current_layer)
        self._camera_thread.frame_ready.connect(self._preview_display.update_frame)
        self._camera_thread.error_occurred.connect(self._on_error_occurred)
        self._camera_thread.start()

        # Sofort temp_preset setzen, damit Kamera UI-Werte anzeigt
        self._on_param_changed()

    def stop(self) -> None:
        """Stoppt den Admin-Modus."""
        if not self._camera_thread:
            return

        logger.info("Stoppe AdminMode")

        if self._camera_thread.is_running:
            self._camera_thread.stop()

        self._camera_thread = None

        # Display zurücksetzen
        self._preview_display.clear()
        self._preview_display.setText("Vorschau gestoppt")

