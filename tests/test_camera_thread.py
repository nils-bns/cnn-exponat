"""Integrationstests für CameraThread-Reconnect-Verhalten."""

from unittest.mock import Mock

from core.exceptions import CameraFrameError


class _FakeSignal:
    """Minimaler Ersatz für ein pyqtSignal (nur emit-Zählung)."""

    def __init__(self):
        self.emit_count = 0
        self.emitted_args = []

    def emit(self, *args):
        self.emit_count += 1
        self.emitted_args.append(args)


def _make_thread(facade):
    """Erstellt einen CameraThread ohne QThread-Initialisierung.

    Vermeidet den Qt-Event-Loop, indem der Thread über __new__ instanziiert
    und nur die für den Reconnect nötigen Felder gesetzt werden.
    """
    from view.camera_thread import CameraThread

    thread = CameraThread.__new__(CameraThread)
    thread._facade = facade
    thread._running = True
    thread.camera_restored = _FakeSignal()
    thread.RECONNECT_INTERVAL_S = 0.0  # keine reale Pause im Test
    return thread


def test_reconnect_blocking_retries_until_success():
    """Test: Reconnect-Schleife gibt nicht auf und meldet Wiederherstellung."""
    facade = Mock()
    # Erst zweimal fehlschlagen, dann erfolgreich
    facade.reconnect_camera.side_effect = [False, False, True]

    thread = _make_thread(facade)
    thread._reconnect_camera_blocking()

    assert facade.reconnect_camera.call_count == 3
    assert thread.camera_restored.emit_count == 1
    assert thread._running is True


def test_reconnect_blocking_stops_when_thread_stopped():
    """Test: Reconnect-Schleife bricht ab, wenn der Thread gestoppt wird."""
    facade = Mock()

    thread = _make_thread(facade)

    # reconnect schlägt fehl und stoppt dabei den Thread (simuliert stop())
    def fail_and_stop():
        thread._running = False
        return False

    facade.reconnect_camera.side_effect = fail_and_stop

    thread._reconnect_camera_blocking()

    # Genau ein Versuch, danach bricht die while-Schleife ab
    assert facade.reconnect_camera.call_count == 1
    assert thread.camera_restored.emit_count == 0


def test_interruptible_sleep_returns_immediately_when_stopped():
    """Test: Unterbrechbarer Sleep kehrt bei _running=False sofort zurück."""
    facade = Mock()
    thread = _make_thread(facade)
    thread._running = False

    # Darf nicht blockieren (kein reales time.sleep von 1s)
    thread._interruptible_sleep(1.0)
