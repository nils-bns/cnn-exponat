"""Tests fuer ModelService Predictions."""

import numpy as np
import torch
from torchvision.models import ResNet18_Weights

from core.services.model_service import ModelService


# Labels aus Weights fuer Test-Vergleiche
_TEST_LABELS = list(ResNet18_Weights.IMAGENET1K_V1.meta["categories"])


class TestModelServicePredictions:
    """Tests fuer ModelService.get_top_predictions()."""

    def _service_with_labels(self) -> ModelService:
        """Erstellt ModelService mit Labels (ohne volles Modell zu laden)."""
        service = ModelService()
        service._labels = _TEST_LABELS
        return service

    def test_get_top_predictions_returns_correct_top_k(self):
        """Test: get_top_predictions() gibt korrekte Top-K zurueck."""
        # Arrange
        service = self._service_with_labels()
        fake_output = torch.zeros(1, 1000)
        fake_output[0, 281] = 10.0  # hoechster
        fake_output[0, 282] = 8.0   # zweithoechster
        fake_output[0, 285] = 6.0   # dritthoechster
        service._last_output = fake_output

        # Act
        results = service.get_top_predictions(k=3)

        # Assert
        assert len(results) == 3
        assert results[0][0] == _TEST_LABELS[281]
        assert results[1][0] == _TEST_LABELS[282]
        assert results[2][0] == _TEST_LABELS[285]
        # Wahrscheinlichkeiten absteigend
        assert results[0][1] > results[1][1] > results[2][1]

    def test_get_top_predictions_returns_empty_without_forward_pass(self):
        """Test: get_top_predictions() gibt leere Liste ohne Forward Pass."""
        # Arrange
        service = ModelService()

        # Act
        results = service.get_top_predictions()

        # Assert
        assert results == []

    def test_get_top_predictions_returns_empty_without_labels(self):
        """Test: get_top_predictions() gibt leere Liste ohne geladene Labels."""
        # Arrange
        service = ModelService()
        service._last_output = torch.randn(1, 1000)

        # Act
        results = service.get_top_predictions()

        # Assert
        assert results == []

    def test_get_top_predictions_returns_probabilities_summing_near_one(self):
        """Test: Wahrscheinlichkeiten sind Softmax-normalisiert."""
        # Arrange
        service = self._service_with_labels()
        fake_output = torch.randn(1, 1000)
        service._last_output = fake_output

        # Act
        results = service.get_top_predictions(k=3)

        # Assert
        for name, prob in results:
            assert 0.0 <= prob <= 1.0


class TestImageNetLabelsFromWeights:
    """Tests fuer ImageNet Labels aus ResNet18 Weights."""

    def test_weights_provide_1000_labels(self):
        """Test: Weights liefern exakt 1000 Labels."""
        assert len(_TEST_LABELS) == 1000

    def test_weights_first_label_is_tench(self):
        """Test: Erster Eintrag ist 'tench' (Index 0)."""
        assert _TEST_LABELS[0] == "tench"

    def test_weights_labels_are_all_strings(self):
        """Test: Alle Labels sind nicht-leere Strings."""
        for label in _TEST_LABELS:
            assert isinstance(label, str)
            assert len(label) > 0


class TestModelServiceGradcamSmoothing:
    """Tests für die zeitliche GradCAM-Stabilisierung (EMA + Klassenstabilisierung)."""

    def test_smooth_cam_first_frame_returns_input(self):
        """Test: Erster Frame (kein Vorframe) gibt die Eingabe unverändert zurück."""
        # Arrange
        service = ModelService()
        cam = np.ones((7, 7), dtype=np.float32)

        # Act
        result = service._smooth_cam(cam)

        # Assert
        assert np.allclose(result, cam)
        assert service._gradcam_prev_cam is not None  # State gespeichert

    def test_smooth_cam_blends_with_previous(self):
        """Test: Zweiter Frame mischt per EMA mit dem Vorframe (alpha=0.3)."""
        # Arrange
        service = ModelService()
        service._gradcam_prev_cam = np.zeros((7, 7), dtype=np.float32)
        cam = np.ones((7, 7), dtype=np.float32)

        # Act
        result = service._smooth_cam(cam)

        # Assert: 0.3 * 1 + 0.7 * 0 = 0.3
        assert np.allclose(result, 0.3)

    def test_stabilize_target_class_first_frame_uses_argmax(self):
        """Test: Ohne Vorframe ist die Zielklasse das argmax der aktuellen Logits."""
        # Arrange
        service = ModelService()
        output = torch.zeros(1, 1000)
        output[0, 281] = 10.0

        # Act
        pred_class = service._stabilize_target_class(output)

        # Assert
        assert pred_class == 281

    def test_stabilize_target_class_resists_single_frame_flip(self):
        """Test: Ein knapper Ausreißer-Frame kippt die stabilisierte Klasse nicht."""
        # Arrange: Vorframe stark auf Klasse 281
        service = ModelService()
        prev = torch.zeros(1, 1000)
        prev[0, 281] = 10.0
        service._gradcam_smoothed_logits = prev
        # Aktueller Frame leicht zugunsten 282
        output = torch.zeros(1, 1000)
        output[0, 282] = 1.0

        # Act: 0.3*1=0.3 für 282 vs. 0.7*10=7.0 für 281
        pred_class = service._stabilize_target_class(output)

        # Assert
        assert pred_class == 281

    def test_reset_gradcam_state_clears_state(self):
        """Test: Reset löscht Vorframe/Logits und merkt sich den neuen Layer."""
        # Arrange
        service = ModelService()
        service._gradcam_prev_cam = np.ones((7, 7), dtype=np.float32)
        service._gradcam_smoothed_logits = torch.zeros(1, 1000)

        # Act
        service._reset_gradcam_state("layer4")

        # Assert
        assert service._gradcam_prev_cam is None
        assert service._gradcam_smoothed_logits is None
        assert service._gradcam_state_layer == "layer4"
