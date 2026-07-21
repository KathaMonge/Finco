import flet as ft

from services.account_service import account_service
from ui.components.empty_state import EmptyState
from ui.components.dialogs import AccountDialog
from ui.theme import AppTheme
from utils.helpers import format_currency

ACCOUNT_ICONS = {
    "cash": ft.Icons.PAYMENTS,
    "debit": ft.Icons.CREDIT_CARD,
    "credit": ft.Icons.CREDIT_SCORE,
}

ACCOUNT_LABELS = {
    "cash": "Efectivo",
    "debit": "Débito",
    "credit": "Crédito",
}


def accounts_view(page: ft.Page) -> ft.Control:
    accounts = account_service.list_all()

    if not accounts:
        return EmptyState(
            icon=ft.Icons.ACCOUNT_BALANCE,
            title="Sin cuentas",
            subtitle="Crea tu primera cuenta (efectivo, débito o crédito)",
            action_text="Nueva Cuenta",
            on_action=lambda _: _open_new_dialog(page),
        )

    cards = ft.Row(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ACCOUNT_ICONS.get(acc.type, ft.Icons.ACCOUNT_BALANCE),
                                    size=28,
                                    color=AppTheme.PRIMARY,
                                ),
                                ft.Text(
                                    acc.name,
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=AppTheme.ON_SURFACE,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_size=16,
                                    icon_color=AppTheme.TEXT_SECONDARY,
                                    on_click=lambda _, a=acc: _open_edit_dialog(page, a),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            ACCOUNT_LABELS.get(acc.type, acc.type),
                            size=12,
                            color=AppTheme.TEXT_SECONDARY,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            format_currency(acc.balance),
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=AppTheme.PRIMARY,
                        ),
                    ],
                    spacing=2,
                ),
                bgcolor=AppTheme.CARD_COLOR,
                border_radius=12,
                padding=20,
                expand=True,
                ink=True,
            )
            for acc in accounts
        ],
        spacing=16,
        wrap=True,
    )

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Cuentas", size=22, weight=ft.FontWeight.BOLD, color=AppTheme.ON_BACKGROUND, expand=True),
                    ft.FilledButton(
                        content="Nueva",
                        icon=ft.Icons.ADD,
                        on_click=lambda _: _open_new_dialog(page),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(height=24),
            cards,
        ],
        expand=True,
    )


def _open_new_dialog(page: ft.Page):
    dlg = AccountDialog(page=page, on_saved=lambda: _refresh(page))
    page.show_dialog(dlg)


def _open_edit_dialog(page: ft.Page, acc):
    dlg = AccountDialog(page=page, on_saved=lambda: _refresh(page), account=acc)
    page.show_dialog(dlg)


def _refresh(page: ft.Page):
    if hasattr(page, '_navigate'):
        page._navigate(4)
