from datetime import date

import flet as ft

from services.transaction_service import transaction_service
from ui.components.data_table import TransactionTable
from ui.components.dialogs import TransactionDialog
from ui.components.empty_state import EmptyState
from ui.components.snack_undo import show_snackbar, show_undo_snackbar
from ui.theme import AppTheme


def transactions_view(page: ft.Page) -> ft.Control:
    search_query = getattr(page, '_search_query', None)
    tx_list = transaction_service.list_active(search=search_query, limit=200)

    if not tx_list and not search_query:
        return EmptyState(
            icon=ft.Icons.RECEIPT_LONG,
            title="No hay transacciones",
            subtitle="Registra tu primer gasto o ingreso para comenzar",
            action_text="Nueva Transacción",
            on_action=lambda _: _open_new_tx_dialog(page),
        )

    table = TransactionTable(
        transactions=tx_list,
        on_delete=lambda tx: _delete_tx(page, tx),
        on_edit=lambda tx: _open_edit_tx_dialog(page, tx),
    )

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text(
                        "Transacciones",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=AppTheme.ON_BACKGROUND,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            ft.OutlinedButton(
                                "Exportar CSV",
                                icon=ft.Icons.DOWNLOAD,
                                on_click=lambda _: _export_csv(page),
                            ),
                            ft.OutlinedButton(
                                "Exportar Excel",
                                icon=ft.Icons.TABLE_CHART,
                                on_click=lambda _: _export_excel(page),
                            ),
                            ft.FilledButton(
                                "Nueva",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: _open_new_tx_dialog(page),
                                tooltip="Ctrl+N",
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(height=16),
            ft.TextField(
                hint_text="Buscar transacciones...",
                prefix_icon=ft.Icons.SEARCH,
                border_color=AppTheme.BORDER_COLOR,
                on_change=lambda e: _search_tx(page, e.control.value),
                expand=True,
            ),
            ft.Container(height=16),
            ft.Container(
                content=table,
                expand=True,
                border_radius=8,
            ),
        ],
        expand=True,
    )


def _open_new_tx_dialog(page: ft.Page):
    dialog = TransactionDialog(
        page=page,
        on_saved=lambda: _refresh(page),
    )
    page.show_dialog(dialog)


def _open_edit_tx_dialog(page: ft.Page, tx):
    dialog = TransactionDialog(
        page=page,
        on_saved=lambda: _refresh(page),
        transaction=tx,
    )
    page.show_dialog(dialog)


def _delete_tx(page: ft.Page, tx):
    transaction_service.soft_delete(tx.id)

    def undo():
        transaction_service.restore(tx.id)
        _refresh(page)

    show_undo_snackbar(
        page,
        f"Transacción '{tx.description}' eliminada",
        undo_callback=undo,
    )
    _refresh(page)


def _search_tx(page: ft.Page, query: str):
    page._search_query = query if query.strip() else None
    if hasattr(page, '_navigate'):
        page._navigate(1)


def _refresh(page: ft.Page):
    if hasattr(page, '_navigate'):
        page._navigate(1)


def _export_csv(page: ft.Page):
    from pathlib import Path

    from services.backup_service import backup_service
    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        downloads = Path.home()
    out_path = backup_service.export_csv(downloads)
    show_snackbar(page,
        ft.SnackBar(
            content=ft.Text(f"Transacciones exportadas a: {out_path.name}"),
            action="OK",
        )
    )


def _export_excel(page: ft.Page):
    from pathlib import Path

    from services.backup_service import backup_service
    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        downloads = Path.home()
    today = date.today()
    out_path = backup_service.export_excel(downloads, today.year, today.month)
    show_snackbar(page,
        ft.SnackBar(
            content=ft.Text(f"Reporte Excel exportado a: {out_path.name}"),
            action="OK",
        )
    )
