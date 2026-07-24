from typing import Optional

import flet as ft

from ui.theme import AppTheme, Elevation, Radius, Spacing


class AppCard(ft.Container):
    def __init__(
        self,
        content: ft.Control,
        title: Optional[str] = None,
        title_icon: Optional[str] = None,
        **kwargs,
    ):
        body: ft.Control = content
        if title:
            header = ft.Row(
                [
                    ft.Icon(name=title_icon, color=AppTheme.ACCENT, size=22) if title_icon else ft.Container(),
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=AppTheme.ON_SURFACE),
                ],
                spacing=8,
            )
            body = ft.Column([header, ft.Container(height=Spacing.MD), content], spacing=0)

        super().__init__(
            content=body,
            bgcolor=AppTheme.CARD_COLOR,
            border_radius=Radius.MD,
            padding=Spacing.LG,
            shadow=Elevation.card(),
            **kwargs,
        )
