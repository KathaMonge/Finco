import flet as ft

from ui.theme import AppTheme


class EmptyState(ft.Column):
    """Reusable empty state with icon, message, and optional action button."""

    def __init__(
        self,
        icon: str = "inbox",
        title: str = "Sin datos",
        subtitle: str = "",
        action_text: str | None = None,
        on_action=None,
    ):
        self._icon = icon
        self._title = title
        self._subtitle = subtitle
        self._action_text = action_text
        self._on_action = on_action

        content = [
            ft.Icon(
                self._icon,
                size=64,
                color=AppTheme.TEXT_SECONDARY,
            ),
            ft.Text(
                self._title,
                size=20,
                weight=ft.FontWeight.W_500,
                color=AppTheme.ON_SURFACE,
                text_align=ft.TextAlign.CENTER,
            ),
        ]

        if self._subtitle:
            content.append(
                ft.Text(
                    self._subtitle,
                    size=14,
                    color=AppTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                )
            )

        if self._action_text and self._on_action:
            content.append(
                ft.Container(height=16)
            )
            content.append(
                ft.FilledButton(
                    self._action_text,
                    on_click=self._on_action,
                    icon=ft.Icons.ADD,
                )
            )

        super().__init__(
            controls=[
                ft.Container(
                    content=ft.Column(
                        content,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
