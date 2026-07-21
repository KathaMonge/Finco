import flet as ft

from ui.theme import AppTheme


def show_snackbar(page: ft.Page, snackbar: ft.SnackBar):
    """Show a SnackBar using the traditional page.snack_bar pattern."""
    page.snack_bar = snackbar
    page.snack_bar.open = True
    page.update()


def show_undo_snackbar(
    page: ft.Page,
    message: str,
    undo_callback,
    action_label: str = "Deshacer",
    duration: int = 4000,
):
    """Show a SnackBar with an Undo action button."""

    def on_action(e):
        undo_callback()
        show_snackbar(
            page,
            ft.SnackBar(
                content=ft.Text("Acción deshecha"),
                bgcolor=AppTheme.SUCCESS,
                duration=2000,
            ),
        )

    show_snackbar(
        page,
        ft.SnackBar(
            content=ft.Text(message),
            action=action_label,
            action_color=AppTheme.ACCENT,
            on_action=on_action,
            bgcolor=AppTheme.SURFACE_VARIANT,
            duration=duration,
            behavior=ft.SnackBarBehavior.FLOATING,
        ),
    )
