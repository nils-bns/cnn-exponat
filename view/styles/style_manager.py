"""StyleManager für zentrale Verwaltung aller View-Styles.

Lädt QSS-Templates und ersetzt Platzhalter durch Werte aus colors.py und dimensions.py.
"""

import logging
from pathlib import Path
from . import colors
from . import dimensions

logger = logging.getLogger(__name__)


class StyleManager:
    """Zentrale Verwaltung aller Styles.

    Features:
    - Lädt base.qss und ersetzt Platzhalter
    - Caching für Performance
    - Einzelne Button-Styles abrufbar
    - Reload-Funktion für Entwicklung

    Usage:
        stylesheet = StyleManager.get_stylesheet()
        app.setStyleSheet(stylesheet)

        # Oder für einzelne Buttons
        button.setStyleSheet(StyleManager.get_button_style("primary"))
    """

    _cached_stylesheet: str | None = None
    _base_qss_path = Path(__file__).parent / "base.qss"

    @classmethod
    def get_stylesheet(cls) -> str:
        """Lädt und cached das komplette Stylesheet.

        Returns:
            QSS-String mit ersetzten Platzhaltern

        Raises:
            FileNotFoundError: Wenn base.qss nicht gefunden wird
        """
        if cls._cached_stylesheet is not None:
            logger.debug("Stylesheet aus Cache geladen")
            return cls._cached_stylesheet

        logger.info(f"Lade Stylesheet von {cls._base_qss_path}")

        if not cls._base_qss_path.exists():
            raise FileNotFoundError(f"base.qss nicht gefunden: {cls._base_qss_path}")

        # Lade Template
        with open(cls._base_qss_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Ersetze Platzhalter
        stylesheet = cls._replace_placeholders(template)

        # Cache
        cls._cached_stylesheet = stylesheet
        logger.info("Stylesheet erfolgreich geladen und gecached")

        return stylesheet

    @classmethod
    def get_button_style(cls, button_type: str) -> str:
        """Gibt Style für bestimmten Button-Typ zurück.

        Args:
            button_type: "primary", "success", "danger"

        Returns:
            QSS-String für den Button-Typ

        Raises:
            ValueError: Bei unbekanntem button_type
        """
        if button_type == "primary":
            return cls._get_primary_button_style()
        elif button_type == "success":
            return cls._get_success_button_style()
        elif button_type == "danger":
            return cls._get_danger_button_style()
        else:
            raise ValueError(f"Unbekannter button_type: {button_type}")

    @classmethod
    def get_display_style(cls) -> str:
        """Gibt Style für Kamera-Display zurück.

        Returns:
            QSS-String für Camera-Display
        """
        return f"""
            QLabel {{
                background-color: {colors.BACKGROUND_DARK};
                color: {colors.TEXT_PRIMARY};
                border: 2px solid {colors.BORDER_DEFAULT};
                font-size: {dimensions.FONT_SIZES.large}px;
            }}
        """

    @classmethod
    def reload_stylesheet(cls) -> str:
        """Löscht Cache und lädt Stylesheet neu.

        Nützlich für Entwicklung.

        Returns:
            Neu geladenes Stylesheet
        """
        logger.info("Stylesheet-Cache wird geleert")
        cls._cached_stylesheet = None
        return cls.get_stylesheet()

    @classmethod
    def _replace_placeholders(cls, template: str) -> str:
        """Ersetzt alle Platzhalter im Template.

        Args:
            template: QSS-Template-String mit {placeholder}

        Returns:
            QSS-String mit ersetzten Platzhaltern
        """
        replacements = {
            # Colors
            'primary': colors.PRIMARY,
            'primary_hover': colors.PRIMARY_HOVER,
            'primary_pressed': colors.PRIMARY_PRESSED,
            'primary_border': colors.PRIMARY_BORDER,
            'active': colors.ACTIVE,
            'active_hover': colors.ACTIVE_HOVER,
            'active_border': colors.ACTIVE_BORDER,
            'success': colors.SUCCESS,
            'success_hover': colors.SUCCESS_HOVER,
            'danger': colors.DANGER,
            'danger_hover': colors.DANGER_HOVER,
            'warning': colors.WARNING,
            'warning_hover': colors.WARNING_HOVER,
            'background_dark': colors.BACKGROUND_DARK,
            'background_light': colors.BACKGROUND_LIGHT,
            'background_medium': colors.BACKGROUND_MEDIUM,
            'border_default': colors.BORDER_DEFAULT,
            'border_light': colors.BORDER_LIGHT,
            'border_dark': colors.BORDER_DARK,
            'text_primary': colors.TEXT_PRIMARY,
            'text_secondary': colors.TEXT_SECONDARY,
            'text_dark': colors.TEXT_DARK,

            # Dimensions
            'button_radius': str(dimensions.BUTTON_DIMS.border_radius),
            'button_padding': str(dimensions.BUTTON_DIMS.padding),
            'button_border_width': str(dimensions.BUTTON_DIMS.border_width),

            # Font Sizes
            'font_small': str(dimensions.FONT_SIZES.small),
            'font_medium': str(dimensions.FONT_SIZES.medium),
            'font_large': str(dimensions.FONT_SIZES.large),
            'font_xlarge': str(dimensions.FONT_SIZES.xlarge),
            'font_family': dimensions.FONT_SIZES.font_family,

            # Overlay Styling (InfoPanel, AboutWidget)
            'overlay_bg_rgba': colors.OVERLAY_BG_RGBA,
            'overlay_border_glow_rgba': colors.OVERLAY_BORDER_GLOW_RGBA,
            'info_panel_border_radius': str(dimensions.INFO_PANEL_DIMS.border_radius),
            'about_border_radius': str(dimensions.ABOUT_DIMS.border_radius),
            'about_border_width': str(dimensions.ABOUT_DIMS.border_width),
            # AboutWidget – weißes Styling
            'about_bg_rgba': colors.ABOUT_BG_WHITE_RGBA,
            'about_text_color': colors.ABOUT_TEXT_COLOR,

            # Title-Text-Widget
            'title_text_color': colors.ARCH_LAYER_MAGENTA,
            'title_text_font_size': str(dimensions.TITLE_TEXT_DIMS.font_size),

            # GradCAM-Subtitle-Widget
            'gradcam_subtitle_font_size': str(dimensions.GRADCAM_SUBTITLE_DIMS.font_size),
        }

        result = template
        for placeholder, value in replacements.items():
            result = result.replace(f'{{{placeholder}}}', value)

        logger.debug(f"Platzhalter ersetzt: {len(replacements)} Ersetzungen")
        return result

    @classmethod
    def _get_primary_button_style(cls) -> str:
        """Primärer Button-Style (Layer-Buttons)."""
        return f"""
            QPushButton {{
                background-color: {colors.PRIMARY};
                color: {colors.TEXT_PRIMARY};
                border: {dimensions.BUTTON_DIMS.border_width}px solid {colors.PRIMARY_BORDER};
                border-radius: {dimensions.BUTTON_DIMS.border_radius}px;
                padding: {dimensions.BUTTON_DIMS.padding}px;
                font-size: {dimensions.FONT_SIZES.large}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {colors.PRIMARY_PRESSED};
            }}
            QPushButton:checked {{
                background-color: {colors.ACTIVE};
                border-color: {colors.ACTIVE_BORDER};
            }}
            QPushButton:checked:hover {{
                background-color: {colors.ACTIVE_HOVER};
            }}
        """

    @classmethod
    def _get_success_button_style(cls) -> str:
        """Success Button-Style (Save, Add)."""
        return f"""
            QPushButton {{
                background-color: {colors.SUCCESS};
                color: {colors.TEXT_PRIMARY};
                font-weight: bold;
                border-radius: 3px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {colors.SUCCESS_HOVER};
            }}
        """

    @classmethod
    def _get_danger_button_style(cls) -> str:
        """Danger Button-Style (Delete)."""
        return f"""
            QPushButton {{
                background-color: {colors.DANGER};
                color: {colors.TEXT_PRIMARY};
                font-weight: bold;
                border-radius: 3px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {colors.DANGER_HOVER};
            }}
        """
