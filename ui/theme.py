"""Dark theme and high contrast theme for Finco."""

import flet as ft


class AppTheme:
    PRIMARY = "#4ECDC4"
    SECONDARY = "#45B7D1"
    ACCENT = "#FFD93D"
    ERROR = "#FF6B6B"
    SUCCESS = "#5FD068"
    WARNING = "#FFD93D"
    SURFACE = "#1E1E2E"
    BACKGROUND = "#16162A"
    ON_SURFACE = "#E0E0E0"
    ON_BACKGROUND = "#FFFFFF"
    SURFACE_VARIANT = "#2A2A3D"
    CARD_COLOR = "#252540"
    BORDER_COLOR = "#3A3A50"
    TEXT_SECONDARY = "#9E9E9E"
    TEXT_PRIMARY = "#FFFFFF"

    CHART_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98A2FF", "#FF9FF3",
    ]


class HighContrastTheme:
    PRIMARY = "#00FFCC"
    SECONDARY = "#66D9FF"
    ACCENT = "#FFFF00"
    ERROR = "#FF4444"
    SUCCESS = "#00FF66"
    WARNING = "#FFDD00"
    SURFACE = "#000000"
    BACKGROUND = "#000000"
    ON_SURFACE = "#FFFFFF"
    ON_BACKGROUND = "#FFFFFF"
    SURFACE_VARIANT = "#1A1A1A"
    CARD_COLOR = "#0A0A0A"
    BORDER_COLOR = "#FFFFFF"
    TEXT_SECONDARY = "#CCCCCC"
    TEXT_PRIMARY = "#FFFFFF"

    CHART_COLORS = [
        "#FF4444", "#00FFCC", "#66D9FF", "#00CC88",
        "#FFDD00", "#FF88FF", "#8888FF", "#FF66CC",
    ]


class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32


class Radius:
    SM = 8
    MD = 12
    LG = 16


class Elevation:
    @staticmethod
    def card() -> list[ft.BoxShadow]:
        return [
            ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color="#20000000",
                offset=ft.Offset(0, 4),
            )
        ]

    @staticmethod
    def raised() -> list[ft.BoxShadow]:
        return [
            ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color="#30000000",
                offset=ft.Offset(0, 8),
            )
        ]


def build_theme(high_contrast: bool = False) -> ft.Theme:
    t = HighContrastTheme if high_contrast else AppTheme

    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=t.PRIMARY,
            on_primary=t.BACKGROUND,
            secondary=t.SECONDARY,
            error=t.ERROR,
            surface=t.SURFACE,
            on_surface=t.ON_SURFACE,
            surface_tint=t.PRIMARY,
        ),
        font_family="Segoe UI",
        use_material3=True,
    )


def page_styles(page: ft.Page, high_contrast: bool = False):
    t = HighContrastTheme if high_contrast else AppTheme
    page.bgcolor = t.BACKGROUND
    page.theme = build_theme(high_contrast)
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
