"""Channel-Verwaltung fuer den Admin-Modus.

Enthaelt:
- ChannelSpinBox: Custom QSpinBox mit eingeschraenkter User-Eingabe
- ChannelManager: Logik fuer Channel Add/Delete/Visibility/Range
"""

import logging
from PyQt6.QtWidgets import QWidget, QSpinBox, QPushButton
from PyQt6.QtGui import QValidator


logger = logging.getLogger(__name__)


class ChannelSpinBox(QSpinBox):
    """SpinBox für Channel-Auswahl mit eingeschränkter User-Eingabe.

    Der Wert -1 kann nur programmatisch gesetzt werden (z.B. beim Löschen
    eines Channels), nicht aber durch User-Interaktion über Pfeiltasten
    oder Tastatureingabe.

    Attributes:
        _allow_negative: Flag für programmatisches Setzen von -1
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialisiert die ChannelSpinBox.

        Args:
            parent: Parent-Widget (optional)
        """
        super().__init__(parent)
        self._allow_negative = False

    def stepBy(self, steps: int) -> None:
        """Überschreibt Pfeiltasten-Verhalten.

        Verhindert, dass der User per Pfeiltasten unter 0 gehen kann.

        Args:
            steps: Anzahl der Schritte (+1 für hoch, -1 für runter)
        """
        new_value = self.value() + steps
        if new_value < 0:
            new_value = 0  # Nicht unter 0 per Pfeiltasten
        # Auch Maximum beachten
        if new_value > self.maximum():
            new_value = self.maximum()
        self.setValue(new_value)

    def validate(self, text: str, pos: int) -> tuple:
        """Validiert Keyboard-Eingaben.

        Verhindert, dass der User negative Werte eintippen kann.

        Args:
            text: Eingegebener Text
            pos: Cursor-Position

        Returns:
            Tuple aus (QValidator.State, text, pos)
        """
        # Prüfe ob negative Werte eingegeben werden
        if text.startswith('-'):
            return (QValidator.State.Invalid, text, pos)
        return super().validate(text, pos)

    def setProgrammaticValue(self, value: int) -> None:
        """Setzt Wert programmatisch (erlaubt -1).

        Diese Methode muss verwendet werden, wenn -1 gesetzt werden soll
        (z.B. beim Löschen eines Channels oder beim Laden eines Presets).

        Args:
            value: Zu setzender Wert (kann -1 sein)
        """
        self._allow_negative = True
        self.setValue(value)
        self._allow_negative = False


class ChannelManager:
    """Verwaltet Channel-SpinBoxen, Visibility und Add/Delete-Logik.

    Der ChannelManager erstellt KEINE UI-Elemente. Er erhält Referenzen
    auf bereits erstellte Widgets vom AdminModeWidget und steuert deren
    Werte und Sichtbarkeit.

    Attributes:
        _spinboxes: Colormap-Channel-SpinBoxen (bis zu 3)
        _rgb_spinboxes: RGB-Channel-SpinBoxen (genau 3: R, G, B)
        _rows: Channel-Row-Container-Widgets
        _delete_buttons: Delete-Buttons (None für Channel 1)
        _add_button: Add-Channel-Button
    """

    def __init__(
        self,
        spinboxes: list[ChannelSpinBox],
        rgb_spinboxes: list[ChannelSpinBox],
        rows: list[QWidget],
        delete_buttons: list[QPushButton | None],
        add_button: QPushButton,
    ):
        """Initialisiert den ChannelManager mit Widget-Referenzen.

        Args:
            spinboxes: Colormap-Channel-SpinBoxen
            rgb_spinboxes: RGB-Channel-SpinBoxen
            rows: Channel-Row-Container
            delete_buttons: Delete-Buttons (None für Channel 1)
            add_button: Add-Channel-Button
        """
        self._spinboxes = spinboxes
        self._rgb_spinboxes = rgb_spinboxes
        self._rows = rows
        self._delete_buttons = delete_buttons
        self._add_button = add_button

    def add_channel(self) -> None:
        """Aktiviert nächsten inaktiven Channel.

        Findet den ersten Channel mit Wert -1 und setzt ihn auf 0.
        Aktualisiert anschließend die Sichtbarkeit.
        """
        logger.debug("ChannelManager: Channel hinzufügen")

        for spinbox in self._spinboxes:
            if spinbox.value() == -1:
                spinbox.setValue(0)
                break

        self.update_visibility()

    def delete_channel(self, index: int) -> None:
        """Löscht Channel und lässt nachfolgende aufrücken.

        Wenn Channel 2 gelöscht wird und Channel 3 existiert,
        rückt Channel 3 auf Position 2. Am Ende wird -1 angefügt.

        Args:
            index: Index des zu löschenden Channels (1 oder 2)
        """
        logger.debug(f"ChannelManager: Channel {index + 1} löschen")

        channels = [spinbox.value() for spinbox in self._spinboxes]

        # Entferne den gelöschten Channel und füge -1 am Ende hinzu
        del channels[index]
        channels.append(-1)

        # UI aktualisieren (programmatisch, da -1 gesetzt werden kann)
        for i, value in enumerate(channels):
            self._spinboxes[i].setProgrammaticValue(value)

        self.update_visibility()

    def update_visibility(self) -> None:
        """Aktualisiert Sichtbarkeit von Channel-Rows und Add-Button.

        Regeln:
        - Channel 1 ist immer sichtbar (kein Delete-Button)
        - Channel 2 & 3 sichtbar wenn Wert != -1
        - Add-Button sichtbar wenn weniger als 3 Channels aktiv
        """
        active_count = 0

        for row, spinbox in zip(self._rows, self._spinboxes):
            is_active = spinbox.value() != -1
            row.setVisible(is_active)
            if is_active:
                active_count += 1

        self._add_button.setVisible(active_count < 3)

        logger.debug(
            f"ChannelManager: {active_count} aktive Channels, "
            f"Add-Button: {active_count < 3}"
        )

    def update_range(self, channel_count: int) -> None:
        """Aktualisiert SpinBox-Range basierend auf Layer-Channel-Anzahl.

        Args:
            channel_count: Anzahl der Channels im Layer
        """
        logger.debug(f"ChannelManager: Range update auf {channel_count} Channels")

        # Colormap-Mode SpinBox-Range (-1 bis channel_count - 1)
        for spinbox in self._spinboxes:
            spinbox.setRange(-1, channel_count - 1)
            if spinbox.value() >= channel_count:
                spinbox.setValue(0)

        # RGB-Mode SpinBox-Range (0 bis channel_count - 1)
        for spinbox in self._rgb_spinboxes:
            spinbox.setRange(0, channel_count - 1)
            if spinbox.value() >= channel_count:
                spinbox.setValue(0)

    def get_channels(self) -> list[int]:
        """Gibt aktuelle Colormap-Channel-Werte zurück.

        Returns:
            Liste der Channel-Werte (kann -1 enthalten für inaktive)
        """
        return [spinbox.value() for spinbox in self._spinboxes]

    def get_rgb_channels(self) -> list[int]:
        """Gibt aktuelle RGB-Channel-Werte zurück.

        Returns:
            Liste der 3 RGB-Channel-Werte
        """
        return [spinbox.value() for spinbox in self._rgb_spinboxes]

    def set_channels(self, channels: list[int]) -> None:
        """Setzt Colormap-Channel-Werte programmatisch.

        Fehlende Werte werden mit -1 aufgefüllt (inaktiv).

        Args:
            channels: Liste der Channel-Werte
        """
        for i, spinbox in enumerate(self._spinboxes):
            if i < len(channels):
                spinbox.setProgrammaticValue(channels[i])
            else:
                spinbox.setProgrammaticValue(-1)

    def set_rgb_channels(self, channels: list[int]) -> None:
        """Setzt RGB-Channel-Werte.

        Fehlende Werte werden mit Fallback (0, 1, 2) aufgefüllt.

        Args:
            channels: Liste der RGB-Channel-Werte
        """
        for i, spinbox in enumerate(self._rgb_spinboxes):
            if i < len(channels):
                spinbox.setValue(channels[i])
            else:
                spinbox.setValue(i)  # Fallback: 0, 1, 2
