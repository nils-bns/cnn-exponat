"""View Layer - PyQt6 UI Komponenten.

Dieses Package enthält alle UI-bezogenen Komponenten für die
CNN-Visualisierungs-Anwendung.

Exports:
    MainWindow: Hauptfenster mit Modus-Verwaltung
    CameraThread: QThread für asynchrone Frame-Verarbeitung
    VisitorModeWidget: Vollbild-UI für Museumsbesucher
    AdminModeWidget: Preset-Editor UI
"""

from view.main_window import MainWindow
from view.camera_thread import CameraThread
from view.visitor_mode import VisitorModeWidget
from view.admin_mode import AdminModeWidget

__all__ = [
    "MainWindow",
    "CameraThread",
    "VisitorModeWidget",
    "AdminModeWidget",
]

