"""ModelService - ResNet18-Inferenz und Layer-Extraktion."""

import logging
import numpy as np
import cv2
import torch
import torch.nn.functional as F
from torchvision.models import resnet18, ResNet18_Weights
import torchvision.transforms as transforms
from core.exceptions import ModelLoadError, InvalidLayerError


logger = logging.getLogger(__name__)


class ModelService:
    """ResNet18-Model für CNN-Visualisierung.

    Lädt pre-trained ResNet18, registriert Hooks für Layer-Extraktion
    und führt Inferenz durch.
    """

    # Verfügbare Layer in ResNet18
    AVAILABLE_LAYERS = ['conv1', 'layer1', 'layer2', 'layer3', 'layer4']

    # GradCAM zeitliche Glättung (EMA): höher = reaktiver, niedriger = ruhiger.
    # 1.0 deaktiviert die Glättung (Verhalten wie ohne Stabilisierung).
    GRADCAM_CAM_EMA_ALPHA = 0.3      # Glättung der normierten Heatmap-Karte
    GRADCAM_LOGIT_EMA_ALPHA = 0.3    # Glättung der Logits (stabilisiert Zielklasse)

    def __init__(self):
        """Initialisiert ModelService."""
        self._model: torch.nn.Module | None = None
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._activations: dict[str, torch.Tensor] = {}
        self._hooks = []
        self._last_output: torch.Tensor | None = None
        self._labels: list[str] = []

        # GradCAM-Glättungs-State (über Frames gehalten, an Layer gekoppelt)
        self._gradcam_prev_cam: np.ndarray | None = None
        self._gradcam_smoothed_logits: torch.Tensor | None = None
        self._gradcam_state_layer: str | None = None

        # Transform für ResNet18 Input
        self._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def load_model(self) -> None:
        """Lädt ResNet18-Modell (pre-trained).

        Raises:
            ModelLoadError: Wenn Modell nicht geladen werden kann
        """
        try:
            logger.info(f"Lade ResNet18-Modell auf {self._device}")
            weights = ResNet18_Weights.IMAGENET1K_V1
            self._model = resnet18(weights=weights)
            self._model.to(self._device)
            self._model.eval()

            self._labels = list(weights.meta["categories"])

            self._register_hooks()
            logger.info("ResNet18-Modell erfolgreich geladen")

        except Exception as e:
            raise ModelLoadError(f"Fehler beim Laden des Modells: {e}")

    def get_layer_names(self) -> list[str]:
        """Gibt Liste aller verfügbaren Layer-Namen zurück.

        Returns:
            Liste der Layer-Namen
        """
        return self.AVAILABLE_LAYERS.copy()

    def get_layer_channel_count(self, layer_name: str) -> int:
        """Gibt die Anzahl der Channels für einen Layer zurück.

        Args:
            layer_name: Name des Layers (z.B. 'layer1', 'layer2')

        Returns:
            Anzahl der Channels im Layer

        Raises:
            InvalidLayerError: Wenn layer_name ungültig
        """
        if layer_name not in self.AVAILABLE_LAYERS:
            raise InvalidLayerError(
                f"Ungültiger Layer '{layer_name}'. "
                f"Verfügbare Layer: {self.AVAILABLE_LAYERS}"
            )

        # Feste Channel-Anzahlen der ResNet18-Architektur (conv1=64, dann Verdopplung pro Stage)
        channel_counts = {
            'conv1': 64,
            'layer1': 64,
            'layer2': 128,
            'layer3': 256,
            'layer4': 512
        }

        return channel_counts[layer_name]

    def extract_layer_activations(
        self,
        image: np.ndarray,
        layer_name: str
    ) -> torch.Tensor:
        """Extrahiert Aktivierungen eines spezifischen Layers.

        Args:
            image: RGB-Bild (H, W, 3)
            layer_name: Name des Layers (z.B. 'layer1', 'layer2')

        Returns:
            Aktivierungs-Tensor (C, H, W) für gewählten Layer

        Raises:
            ValueError: Wenn layer_name ungültig
            ModelLoadError: Wenn Modell nicht geladen
        """
        if self._model is None:
            raise ModelLoadError("Modell ist nicht geladen. Rufe load_model() auf.")

        if layer_name not in self.AVAILABLE_LAYERS:
            raise InvalidLayerError(
                f"Ungültiger Layer '{layer_name}'. "
                f"Verfügbare Layer: {self.AVAILABLE_LAYERS}"
            )

        # Reset activations
        self._activations.clear()

        # Preprocess image
        input_tensor = self._preprocess_image(image)

        # Forward pass (Hooks werden automatisch aufgerufen)
        with torch.no_grad():
            self._last_output = self._model(input_tensor)

        # Hole Aktivierung für gewünschten Layer
        if layer_name not in self._activations:
            raise InvalidLayerError(
                f"Aktivierung für Layer '{layer_name}' nicht verfügbar"
            )

        activation = self._activations[layer_name]

        # Entferne Batch-Dimension: (1, C, H, W) → (C, H, W)
        activation = activation.squeeze(0)

        return activation

    def get_top_predictions(self, k: int = 3) -> list[tuple[str, float]]:
        """Gibt Top-K Predictions des letzten Forward Pass zurueck.

        Liest gecachte Logits aus dem letzten `extract_layer_activations()`-Aufruf,
        wendet Softmax an und gibt die K wahrscheinlichsten Klassen zurueck.

        Args:
            k: Anzahl der Top-Predictions

        Returns:
            Liste von (Klassenname, Wahrscheinlichkeit) Tupeln,
            sortiert nach Wahrscheinlichkeit absteigend.
            Leere Liste wenn kein Forward Pass durchgefuehrt wurde.
        """
        if self._last_output is None or not self._labels:
            return []

        probabilities = F.softmax(self._last_output, dim=1)
        top_probs, top_indices = torch.topk(probabilities, k, dim=1)

        results: list[tuple[str, float]] = []
        for i in range(k):
            class_idx = top_indices[0, i].item()
            prob = top_probs[0, i].item()
            class_name = self._labels[class_idx]
            results.append((class_name, prob))

        return results

    def compute_gradcam(self, image: np.ndarray, layer_name: str) -> np.ndarray:
        """Berechnet GradCAM-Heatmap fuer einen Layer.

        Fuehrt separaten Forward+Backward Pass MIT Gradienten durch.
        Bestehende extract_layer_activations() wird NICHT beeinflusst.

        Args:
            image: RGB-Bild (H, W, 3)
            layer_name: Ziel-Layer fuer GradCAM (z.B. 'layer3', 'layer4')

        Returns:
            RGB-Overlay-Bild (H, W, 3) mit dtype uint8

        Raises:
            ModelLoadError: Wenn Modell nicht geladen
            InvalidLayerError: Wenn layer_name ungueltig
        """
        if self._model is None:
            raise ModelLoadError("Modell ist nicht geladen. Rufe load_model() auf.")

        if layer_name not in self.AVAILABLE_LAYERS:
            raise InvalidLayerError(
                f"Ungueltiger Layer '{layer_name}'. "
                f"Verfuegbare Layer: {self.AVAILABLE_LAYERS}"
            )

        # State bei Layer-Wechsel zurücksetzen (kein Blenden über Layer hinweg)
        if layer_name != self._gradcam_state_layer:
            self._reset_gradcam_state(layer_name)

        target_activation = None
        target_gradient = None

        def forward_hook(module, inp, out):
            nonlocal target_activation
            target_activation = out

        def backward_hook(module, grad_in, grad_out):
            nonlocal target_gradient
            target_gradient = grad_out[0]

        # Ziel-Modul im Modell finden
        target_module = getattr(self._model, layer_name)
        fwd_handle = target_module.register_forward_hook(forward_hook)
        bwd_handle = target_module.register_full_backward_hook(backward_hook)

        try:
            input_tensor = self._preprocess_image(image)
            input_tensor.requires_grad_(True)

            # Forward Pass OHNE no_grad (Gradienten muessen fliessen)
            output = self._model(input_tensor)

            # Zielklasse zeitlich stabilisieren (Logit-EMA, DANN argmax)
            pred_class = self._stabilize_target_class(output)

            # Backward Pass
            self._model.zero_grad()
            output[0, pred_class].backward()

            # GradCAM berechnen: Gewichtete Kombination der Aktivierungen
            weights = target_gradient.mean(dim=[2, 3], keepdim=True)
            cam = (weights * target_activation).sum(dim=1, keepdim=True)
            cam = F.relu(cam)

            # Normalisieren
            cam = cam.squeeze()
            if cam.max() > 0:
                cam = cam / cam.max()
            cam_np = cam.detach().cpu().numpy()

            # Zeitliche Glättung der CAM-Karte (EMA mit Vorframe)
            cam_np = self._smooth_cam(cam_np)

            # Heatmap-Overlay erstellen
            return self._build_gradcam_overlay(cam_np, image)

        finally:
            fwd_handle.remove()
            bwd_handle.remove()

    def _reset_gradcam_state(self, layer_name: str) -> None:
        """Setzt den GradCAM-Glättungs-State zurück (z.B. bei Layer-Wechsel).

        Args:
            layer_name: Layer, für den der frische State ab jetzt gilt
        """
        self._gradcam_prev_cam = None
        self._gradcam_smoothed_logits = None
        self._gradcam_state_layer = layer_name
        logger.debug("GradCAM-State zurückgesetzt für Layer '%s'", layer_name)

    def _stabilize_target_class(self, output: torch.Tensor) -> int:
        """Glättet Logits zeitlich (EMA) und gibt die stabilisierte Zielklasse zurück.

        Verhindert das Umspringen der vorhergesagten Klasse bei knappen
        Entscheidungen zwischen Frames. Der gespeicherte State ist detached,
        damit kein Berechnungsgraph über Frames hinweg gehalten wird.

        Args:
            output: Roh-Logits des aktuellen Forward Pass (1, num_classes)

        Returns:
            Index der zeitlich stabilisierten vorhergesagten Klasse
        """
        current = output.detach()
        if self._gradcam_smoothed_logits is None:
            smoothed = current
        else:
            alpha = self.GRADCAM_LOGIT_EMA_ALPHA
            smoothed = alpha * current + (1.0 - alpha) * self._gradcam_smoothed_logits

        self._gradcam_smoothed_logits = smoothed
        return int(smoothed.argmax(dim=1).item())

    def _smooth_cam(self, cam_np: np.ndarray) -> np.ndarray:
        """Glättet die normierte CAM-Karte zeitlich per EMA mit dem Vorframe.

        Args:
            cam_np: Normierte CAM-Karte des aktuellen Frames (H, W), Werte in [0, 1]

        Returns:
            Zeitlich geglättete CAM-Karte (H, W), Werte in [0, 1]
        """
        if self._gradcam_prev_cam is None:
            smoothed = cam_np
        else:
            alpha = self.GRADCAM_CAM_EMA_ALPHA
            smoothed = alpha * cam_np + (1.0 - alpha) * self._gradcam_prev_cam

        self._gradcam_prev_cam = smoothed
        return smoothed

    def _build_gradcam_overlay(self, cam_np: np.ndarray, image: np.ndarray) -> np.ndarray:
        """Erstellt das RGB-Overlay aus einer normierten CAM-Karte und dem Originalbild.

        Args:
            cam_np: Normierte CAM-Karte (H, W), Werte in [0, 1]
            image: RGB-Originalbild (H, W, 3)

        Returns:
            RGB-Overlay-Bild (H, W, 3) mit dtype uint8
        """
        cam_uint8 = (cam_np * 255).astype(np.uint8)
        cam_resized = cv2.resize(cam_uint8, (image.shape[1], image.shape[0]))
        heatmap = cv2.applyColorMap(cam_resized, cv2.COLORMAP_JET)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        # Overlay: Heatmap + Originalbild (overlay_alpha ist die Misch-Stärke,
        # nicht zu verwechseln mit der EMA-Glättung)
        overlay_alpha = 0.4
        overlay = (overlay_alpha * heatmap_rgb + (1 - overlay_alpha) * image).astype(np.uint8)
        return overlay

    def _register_hooks(self) -> None:
        """Registriert Forward-Hooks für Layer-Extraktion."""
        if self._model is None:
            return

        # Hook-Funktion
        def create_hook(name: str):
            def hook(module, input, output):
                self._activations[name] = output.detach()
            return hook

        # Registriere Hooks für alle Layer
        self._hooks.append(
            self._model.conv1.register_forward_hook(create_hook('conv1'))
        )
        self._hooks.append(
            self._model.layer1.register_forward_hook(create_hook('layer1'))
        )
        self._hooks.append(
            self._model.layer2.register_forward_hook(create_hook('layer2'))
        )
        self._hooks.append(
            self._model.layer3.register_forward_hook(create_hook('layer3'))
        )
        self._hooks.append(
            self._model.layer4.register_forward_hook(create_hook('layer4'))
        )

        logger.debug(f"Hooks für {len(self._hooks)} Layer registriert")

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocesst Bild für ResNet18.

        Args:
            image: RGB NumPy-Array (H, W, 3)

        Returns:
            Preprocessed Tensor (1, 3, 224, 224)
        """
        # Konvertiere zu uint8 falls nötig
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)

        # Apply transforms
        tensor = self._transform(image)

        # Add batch dimension: (3, 224, 224) → (1, 3, 224, 224)
        tensor = tensor.unsqueeze(0)

        # Move to device
        tensor = tensor.to(self._device)

        return tensor

