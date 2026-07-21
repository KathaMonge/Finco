import flet as ft

from ui.theme import AppTheme


class LoadingOverlay(ft.Stack):
    """Overlay with spinner and message, shown during async operations."""

    def __init__(self, message: str = "Procesando..."):
        super().__init__()
        self.message = message
        self.visible = False

        self.spinner = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(
                        width=48,
                        height=48,
                        color=AppTheme.PRIMARY,
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        self.message,
                        size=16,
                        color=AppTheme.ON_SURFACE,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

        self.overlay_bg = ft.Container(
            content=self.spinner,
            bgcolor=ft.Colors.with_opacity(0.7, AppTheme.BACKGROUND),
            expand=True,
        )

        self.controls = [self.overlay_bg]

    def show(self, message: str | None = None):
        if message:
            self.message = message
            column = self.overlay_bg.content.content  # type: ignore
            if len(column.controls) > 2:  # type: ignore
                column.controls[2].value = message  # type: ignore
        self.visible = True
        self.update()

    def hide(self):
        self.visible = False
        self.update()
