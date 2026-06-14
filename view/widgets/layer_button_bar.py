"""LayerButtonBar Widget fuer Visitor Mode.

Horizontale Button-Leiste mit Layer-Auswahl-Buttons.
"""

import logging
from PyQt6.QtWidgets import QHBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal, QTimer, Qt

from view.widgets.base_overlay import BaseOverlayWidget
from view.widgets.layer_button import LayerButton
from view.widgets.helpers import ArchLayerButton
from view.styles import OVERLAY_DIMS

logger = logging.getLogger(__name__)


class LayerButtonBar(BaseOverlayWidget):
    """Button-Leiste fuer Layer-Auswahl im Visitor Mode.

    Features:
    - Erstellt LayerButton-Instanzen aus Layer-Namen
    - Verwaltet aktiven Button-Status (Radio-Button-Verhalten)
    - Emittiert layer_selected Signal bei Klick

    Signals:
        layer_selected(str): Emittiert wenn Layer gewaehlt wurde (Layer-Name)

    Usage:
        layer_names = ['layer1.0', 'layer2.0', 'layer3.0']
        button_labels = {'de': {'layer1.0': 'Layer 1', ...}, 'en': {...}}
        bar = LayerButtonBar(layer_names, button_labels)
        bar.layer_selected.connect(on_layer_selected)
        bar.set_active_layer('layer1.0')
    """

    # Signals
    layer_selected = pyqtSignal(str)
    layout_ready = pyqtSignal()

    # Knoten-Anzahl pro Layer fuer die Architektur-Visualisierung.
    # Entspricht ResNet18 AVAILABLE_LAYERS: conv1, layer1..layer4
    DEFAULT_NODE_COUNTS: dict[str, int] = {
        "conv1": 12,
        "layer1": 8,
        "layer2": 6,
        "layer3": 4,
        "layer4": 1,
    }

    def __init__(self, layer_names: list[str], button_labels: dict[str, dict[str, str]], parent=None):
        """Initialisiert LayerButtonBar.

        Args:
            layer_names: Liste der Layer-Namen (z.B. ['layer1.0', 'layer2.0'])
            button_labels: Bilinguale Labels {"de": {layer: label}, "en": {layer: label}}
            parent: Parent-Widget
        """
        super().__init__(parent)

        self._buttons: dict[str, LayerButton] = {}
        self._all_labels = button_labels

        # Pulse-Animation State
        self._layer_order: list[str] = []
        self._pulsing_button: LayerButton | None = None
        self._pulse_ready: bool = False
        self._pending_active: str | None = None

        self._init_ui(layer_names, button_labels.get("de", {}))

        # Deferred: Basisgroessen erfassen nach Layout-Finalisierung
        QTimer.singleShot(0, self._init_pulse_system)

        logger.debug(f"LayerButtonBar mit {len(layer_names)} Buttons erstellt")

    def _init_ui(self, layer_names: list[str], labels: dict[str, str]) -> None:
        """Erstellt UI mit Container-wrapped Button-Layout.

        Jeder LayerButton wird in einen Fixed-Size QWidget-Container
        gewrapped. Der aeussere QHBoxLayout verwaltet nur die Container,
        deren Groesse sich NICHT aendert. Die Pulse-Animation des Buttons
        findet innerhalb des Containers statt (layout-neutral).

        Args:
            layer_names: Liste der Layer-Namen
            labels: Dict von Layer-Namen zu Anzeigetexten (eine Sprache)
        """
        layout = QHBoxLayout(self)
        m = OVERLAY_DIMS.button_bar_margin_inner
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(OVERLAY_DIMS.button_spacing)

        self._layer_order = list(layer_names)

        for layer_name in layer_names:
            button_text = labels.get(layer_name, layer_name)
            num_nodes = self.DEFAULT_NODE_COUNTS.get(layer_name, 4)
            button = ArchLayerButton(layer_name, button_text, num_nodes)
            button.clicked.connect(lambda checked, l=layer_name: self._on_button_clicked(l))
            self._buttons[layer_name] = button

            # Container-Wrapper: Button wird in einen Fixed-Size Container
            # eingebettet. Container-Groesse wird in _init_pulse_system()
            # gesetzt, nachdem Qt die Layout-Groessen finalisiert hat.
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(button)
            layout.addWidget(container)

        logger.debug(f"{len(self._buttons)} Layer-Buttons in Containern erstellt")

    def _init_pulse_system(self) -> None:
        """Initialisiert das Pulse-System nach Layout-Finalisierung.

        Wird per QTimer.singleShot(0, ...) deferred aufgerufen, damit
        button.size() die korrekte, vom Layout zugewiesene Groesse liefert.
        Setzt Container-Groessen auf base * 1.05 + 2px und erfasst
        die Basisgroessen aller Buttons.
        """
        for button in self._buttons.values():
            base_size = button.capture_base_size()

            # Container-Groesse: Platz fuer maximale Pulse-Groesse (110%) + 2px Puffer
            container_width = int(base_size.width() * 1.1) + 6
            container_height = int(base_size.height() * 1.1) + 6
            container = button.parentWidget()
            if container is not None:
                container.setFixedSize(container_width, container_height)

        self._pulse_ready = True
        self.layout_ready.emit()
        logger.debug("Pulse-System initialisiert, Container-Groessen gesetzt")

        # Pending-State konsumieren (falls set_active_layer vor Pulse-System aufgerufen wurde)
        if self._pending_active is not None:
            self._start_pulse_on_next(self._pending_active)
            self._pending_active = None

    def _start_pulse_on_next(self, active_layer: str) -> None:
        """Startet Pulse auf dem naechsten Button nach dem aktiven Layer.

        Args:
            active_layer: Name des aktuell aktiven Layers
        """
        if active_layer not in self._layer_order:
            return

        # Aktuellen Pulse stoppen
        if self._pulsing_button is not None:
            self._pulsing_button.stop_pulse()
            self._pulsing_button = None

        # Naechsten Button bestimmen (Wrap-Around via Modulo)
        current_index = self._layer_order.index(active_layer)
        next_index = (current_index + 1) % len(self._layer_order)
        next_layer = self._layer_order[next_index]

        # Pulse auf naechstem Button starten
        next_button = self._buttons[next_layer]
        next_button.start_pulse()
        self._pulsing_button = next_button

        logger.debug(f"Pulse auf naechstem Button: {next_layer} (nach {active_layer})")

    def _on_button_clicked(self, layer_name: str) -> None:
        """Handler fuer Button-Klick.

        Args:
            layer_name: Name des geklickten Layers
        """
        logger.debug(f"Layer-Button geklickt: {layer_name}")
        self.set_active_layer(layer_name)
        self.layer_selected.emit(layer_name)

    def set_active_layer(self, layer_name: str) -> None:
        """Setzt den aktiven Layer und startet Pulse auf dem naechsten Button.

        Falls das Pulse-System noch nicht initialisiert ist (Layout nicht
        finalisiert), wird der Layer-Name gepuffert und der Pulse nach
        Initialisierung gestartet.

        Args:
            layer_name: Name des aktiven Layers
        """
        for name, button in self._buttons.items():
            button.setChecked(name == layer_name)

        # Pulse-Orchestrierung
        if self._pulse_ready:
            self._start_pulse_on_next(layer_name)
        else:
            self._pending_active = layer_name

        logger.debug(f"Aktiver Layer gesetzt: {layer_name}")

    def get_active_layer(self) -> str | None:
        """Gibt den aktuell aktiven Layer zurueck.

        Returns:
            Name des aktiven Layers oder None
        """
        for name, button in self._buttons.items():
            if button.isChecked():
                return name
        return None

    def update_language(self, language: str) -> None:
        """Aktualisiert Button-Texte fuer die angegebene Sprache.

        Args:
            language: Sprach-Code ("de" oder "en")
        """
        labels = self._all_labels.get(language, {})
        for layer_name, button in self._buttons.items():
            button.setText(labels.get(layer_name, layer_name))

        logger.debug(f"LayerButtonBar Sprache aktualisiert: {language}")
