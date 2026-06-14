"""Unit Tests für CameraService."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from core.services.camera_service import CameraService
from core.exceptions import CameraNotAvailableError, CameraFrameError


class TestCameraService:
    """Tests für CameraService."""

    def test_init_with_default_index(self):
        """Test: Initialisierung mit Default-Index."""
        service = CameraService()
        assert service._camera_index == CameraService.DEFAULT_CAMERA_INDEX
        assert service._running is False
        assert service._camera is None

    def test_init_with_custom_index(self):
        """Test: Initialisierung mit Custom-Index."""
        service = CameraService(camera_index=1)
        assert service._camera_index == 1
        assert service._running is False

    @patch('cv2.VideoCapture')
    def test_start_success(self, mock_video_capture):
        """Test: Erfolgreicher Kamera-Start."""
        # Arrange
        mock_camera = MagicMock()
        mock_camera.isOpened.return_value = True
        mock_video_capture.return_value = mock_camera

        service = CameraService()

        # Act
        service.start()

        # Assert
        assert service._running is True
        mock_video_capture.assert_called_once_with(CameraService.DEFAULT_CAMERA_INDEX)
        mock_camera.isOpened.assert_called_once()

    @patch('cv2.VideoCapture')
    def test_start_camera_not_available(self, mock_video_capture):
        """Test: Kamera nicht verfügbar."""
        # Arrange
        mock_camera = MagicMock()
        mock_camera.isOpened.return_value = False
        mock_video_capture.return_value = mock_camera

        service = CameraService()

        # Act & Assert
        with pytest.raises(CameraNotAvailableError):
            service.start()

        assert service._running is False

    @patch('cv2.VideoCapture')
    def test_start_already_running(self, mock_video_capture):
        """Test: Start wenn Kamera bereits läuft."""
        # Arrange
        mock_camera = MagicMock()
        mock_camera.isOpened.return_value = True
        mock_video_capture.return_value = mock_camera

        service = CameraService()
        service.start()

        # Act
        service.start()  # Zweiter Start

        # Assert
        assert service._running is True
        assert mock_video_capture.call_count == 1  # Nur einmal aufgerufen

    def test_stop_when_running(self):
        """Test: Stop einer laufenden Kamera."""
        # Arrange
        service = CameraService()
        service._running = True
        mock_camera = MagicMock()
        service._camera = mock_camera

        # Act
        service.stop()

        # Assert
        assert service._running is False
        assert service._camera is None
        mock_camera.release.assert_called_once()

    def test_stop_when_not_running(self):
        """Test: Stop wenn Kamera nicht läuft."""
        # Arrange
        service = CameraService()

        # Act
        service.stop()

        # Assert
        assert service._running is False

    @patch('cv2.cvtColor')
    def test_get_frame_success(self, mock_cvtColor):
        """Test: Erfolgreicher Frame-Abruf."""
        # Arrange
        service = CameraService()
        service._running = True

        mock_camera = MagicMock()
        dummy_frame_bgr = np.zeros((480, 640, 3), dtype=np.uint8)
        dummy_frame_rgb = np.ones((480, 640, 3), dtype=np.uint8)

        mock_camera.read.return_value = (True, dummy_frame_bgr)
        mock_cvtColor.return_value = dummy_frame_rgb
        service._camera = mock_camera

        # Act
        frame = service.get_frame()

        # Assert
        assert frame is dummy_frame_rgb
        mock_camera.read.assert_called_once()
        mock_cvtColor.assert_called_once()

    def test_get_frame_not_running(self):
        """Test: Frame-Abruf wenn Kamera nicht läuft."""
        # Arrange
        service = CameraService()

        # Act & Assert
        with pytest.raises(CameraNotAvailableError):
            service.get_frame()

    def test_get_frame_read_failed(self):
        """Test: Frame-Abruf fehlgeschlagen."""
        # Arrange
        service = CameraService()
        service._running = True

        mock_camera = MagicMock()
        mock_camera.read.return_value = (False, None)
        service._camera = mock_camera

        # Act & Assert
        with pytest.raises(CameraFrameError):
            service.get_frame()

    def test_is_running(self):
        """Test: Status-Prüfung."""
        # Arrange
        service = CameraService()

        # Assert
        assert service.is_running() is False

        service._running = True
        assert service.is_running() is True

