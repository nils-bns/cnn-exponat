"""VisualizationService - Feature-Map-Visualisierung."""

import logging
import numpy as np
import torch
import cv2
from matplotlib import cm
from core.models import PresetConfig


logger = logging.getLogger(__name__)


class VisualizationService:
    """Transformiert Feature Maps zu visualisierbaren Bildern.

    Wendet Preset-Parameter an: Channel-Auswahl, Normalisierung,
    Colormap-Anwendung und Blending.
    """

    # Display-Größe für Visualisierung
    DISPLAY_WIDTH = 800
    DISPLAY_HEIGHT = 600

    def __init__(self):
        """Initialisiert VisualizationService."""
        pass

    def visualize(
        self,
        activations: torch.Tensor,
        preset: PresetConfig
    ) -> np.ndarray:
        """Transformiert Aktivierungen in visualisierbares Bild.

        Args:
            activations: Aktivierungs-Tensor (C, H, W)
            preset: Preset-Konfiguration

        Returns:
            RGB-Bild (H, W, 3) ready for display
        """
        # Visualization Mode bestimmen
        visualization_mode = preset.visualization_mode

        logger.debug(
            f"Visualisiere mit Preset '{preset.name}', "
            f"Mode: {visualization_mode}, Channels: {preset.channels}"
        )

        # Modus-Routing
        if visualization_mode == 'rgb':
            return self._visualize_rgb_mode(activations, preset)
        else:
            return self._visualize_colormap_mode(activations, preset)

    def _visualize_colormap_mode(
        self,
        activations: torch.Tensor,
        preset: PresetConfig
    ) -> np.ndarray:
        """Visualisiert Aktivierung im Colormap-Mode.

        Dies ist die bestehende Visualisierungs-Logik (Channel-Auswahl,
        Blending, Colormap-Anwendung).

        Args:
            activations: Layer-Aktivierung (C, H, W)
            preset: Visualisierungseinstellungen

        Returns:
            RGB-Bild als NumPy-Array (H, W, 3)
        """
        logger.debug(
            f"Colormap-Mode: Channels={preset.channels}, "
            f"Colormap={preset.colormap}"
        )

        # 1. Channel-Auswahl
        selected = self._select_channels(activations, preset.channels)

        # 2. Channel-Blending
        blended = self._blend_channels(selected, preset.blend_mode)

        # 3. Normalisierung
        if preset.normalize:
            blended = self._normalize(blended)

        # 4. Zu NumPy konvertieren
        if isinstance(blended, torch.Tensor):
            blended = blended.cpu().numpy()

        # 5. Colormap anwenden
        colored = self._apply_colormap(blended, preset.colormap)

        # 6. Auf Display-Größe skalieren
        resized = self._resize_to_display(colored)

        return resized

    def _visualize_rgb_mode(
        self,
        activations: torch.Tensor,
        preset: PresetConfig
    ) -> np.ndarray:
        """Visualisiert Aktivierung im RGB-Mode.

        Im RGB-Mode werden 3 Channels direkt auf R, G, B Farbkanäle gemappt:
        - preset.channels[0] → Rot-Kanal
        - preset.channels[1] → Grün-Kanal
        - preset.channels[2] → Blau-Kanal

        Jeder Channel wird SEPARAT normalisiert und dann kombiniert.

        Args:
            activations: Layer-Aktivierung (C, H, W)
            preset: Visualisierungseinstellungen (visualization_mode="rgb")

        Returns:
            RGB-Bild als NumPy-Array (H, W, 3)

        Raises:
            ValueError: Wenn nicht genau 3 Channels angegeben
        """
        # Validierung (sollte bereits in PresetConfig.__post_init__ passiert sein)
        if len(preset.channels) != 3:
            raise ValueError(
                f"RGB-Mode benötigt genau 3 Channels, "
                f"hat: {len(preset.channels)}"
            )

        logger.debug(
            f"RGB-Mode: R=Ch{preset.channels[0]}, "
            f"G=Ch{preset.channels[1]}, "
            f"B=Ch{preset.channels[2]}"
        )

        # Channel-Auswahl mit Bounds-Check
        num_channels = activations.shape[0]
        r_channel_idx = min(preset.channels[0], num_channels - 1)
        g_channel_idx = min(preset.channels[1], num_channels - 1)
        b_channel_idx = min(preset.channels[2], num_channels - 1)

        r_channel = activations[r_channel_idx]  # (H, W)
        g_channel = activations[g_channel_idx]  # (H, W)
        b_channel = activations[b_channel_idx]  # (H, W)

        # Normalisierung (jeder Channel SEPARAT)
        if preset.normalize:
            logger.debug("Normalisiere RGB-Channels separat")

            # Für jeden Channel separat normalisieren (0-255)
            rgb_channels_normalized = []
            for i, channel in enumerate([r_channel, g_channel, b_channel]):
                # Zu NumPy
                channel_np = channel.detach().cpu().numpy()

                # Min-Max Normalisierung
                channel_min = channel_np.min()
                channel_max = channel_np.max()

                if channel_max - channel_min > 1e-6:  # Avoid division by zero
                    channel_normalized = (channel_np - channel_min) / (channel_max - channel_min)
                else:
                    channel_normalized = np.zeros_like(channel_np)

                # Skaliere auf 0-255
                channel_uint8 = (channel_normalized * 255).astype(np.uint8)
                rgb_channels_normalized.append(channel_uint8)

                logger.debug(
                    f"Channel {i} ({['R', 'G', 'B'][i]}): "
                    f"Min={channel_min:.2f}, Max={channel_max:.2f}"
                )
        else:
            # Ohne Normalisierung: Direkt auf 0-255 clippen
            logger.debug("Keine Normalisierung, clippe auf 0-255")
            rgb_channels_normalized = []
            for channel in [r_channel, g_channel, b_channel]:
                channel_np = channel.detach().cpu().numpy()
                channel_uint8 = np.clip(channel_np, 0, 255).astype(np.uint8)
                rgb_channels_normalized.append(channel_uint8)

        # Kombiniere zu RGB-Bild (H, W, 3)
        rgb_image = np.stack(rgb_channels_normalized, axis=-1)  # (H, W, 3)

        logger.debug(
            f"RGB-Bild erstellt: Shape={rgb_image.shape}, dtype={rgb_image.dtype}"
        )

        # Auf Display-Größe skalieren
        resized = self._resize_to_display(rgb_image)

        return resized

    def _select_channels(
        self,
        activations: torch.Tensor,
        channels: list[int]
    ) -> torch.Tensor:
        """Wählt spezifische Channels aus Tensor.

        Filtert automatisch -1 Werte (nicht ausgewählte Channels) und
        ungültige Indizes heraus.

        Args:
            activations: Tensor (C, H, W)
            channels: Liste der Channel-Indizes (-1 = nicht ausgewählt)

        Returns:
            Tensor mit ausgewählten Channels (len(valid_channels), H, W)
        """
        num_channels = activations.shape[0]

        # Filtere -1 (nicht ausgewählt) und ungültige Indizes
        valid_channels = [c for c in channels if c != -1 and 0 <= c < num_channels]

        if not valid_channels:
            logger.warning(
                f"Keine gültigen Channels in {channels} "
                f"(max: {num_channels-1}). Verwende Channel 0."
            )
            valid_channels = [0]

        # Selektiere Channels
        selected = activations[valid_channels]

        return selected

    def _blend_channels(
        self,
        channels: torch.Tensor,
        blend_mode: str
    ) -> torch.Tensor:
        """Kombiniert mehrere Channels zu einem Bild.

        Args:
            channels: Tensor (N, H, W)
            blend_mode: 'max', 'mean', oder 'overlay'

        Returns:
            Tensor (H, W)
        """
        if blend_mode == 'max':
            # Maximum über alle Channels
            blended, _ = torch.max(channels, dim=0)
        elif blend_mode == 'mean':
            # Durchschnitt über alle Channels
            blended = torch.mean(channels, dim=0)
        elif blend_mode == 'overlay':
            # Gewichtete Summe der ersten 3 Channels (RGB-ähnlich)
            if channels.shape[0] >= 3:
                # ITU-R BT.601 Luma-Koeffizienten fuer wahrnehmungsgewichtete Grauwert-Konvertierung
                weights = torch.tensor([0.299, 0.587, 0.114], device=channels.device)
                blended = torch.sum(channels[:3] * weights.view(-1, 1, 1), dim=0)
            else:
                blended = torch.mean(channels, dim=0)
        else:
            logger.warning(f"Unbekannter Blend-Mode '{blend_mode}', verwende 'max'")
            blended, _ = torch.max(channels, dim=0)

        return blended

    def _normalize(self, tensor: torch.Tensor) -> torch.Tensor:
        """Min-Max-Normalisierung auf [0, 1].

        Args:
            tensor: Tensor (H, W)

        Returns:
            Normalisierter Tensor (H, W)
        """
        min_val = tensor.min()
        max_val = tensor.max()

        if max_val - min_val > 1e-6:  # Avoid division by zero
            normalized = (tensor - min_val) / (max_val - min_val)
        else:
            normalized = torch.zeros_like(tensor)

        return normalized

    def _apply_colormap(
        self,
        grayscale: np.ndarray,
        colormap_name: str
    ) -> np.ndarray:
        """Wendet Matplotlib-Colormap an.

        Args:
            grayscale: Grayscale-Bild (H, W), Werte in [0, 1]
            colormap_name: Name der Colormap (z.B. 'viridis', 'plasma')

        Returns:
            RGB-Bild (H, W, 3), Werte in [0, 255]
        """
        # Hole Colormap
        try:
            cmap = cm.get_cmap(colormap_name)
        except ValueError:
            logger.warning(
                f"Unbekannte Colormap '{colormap_name}', verwende 'viridis'"
            )
            cmap = cm.get_cmap('viridis')

        # Apply colormap (gibt RGBA zurück)
        colored = cmap(grayscale)

        # Konvertiere zu RGB (ohne Alpha) und zu uint8
        rgb = (colored[:, :, :3] * 255).astype(np.uint8)

        return rgb


    def _resize_to_display(self, image: np.ndarray) -> np.ndarray:
        """Skaliert Bild auf Display-Größe.

        Args:
            image: RGB-Bild (H, W, 3)

        Returns:
            Skaliertes Bild (DISPLAY_HEIGHT, DISPLAY_WIDTH, 3)
        """
        resized = cv2.resize(
            image,
            (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT),
            interpolation=cv2.INTER_LINEAR
        )

        return resized

