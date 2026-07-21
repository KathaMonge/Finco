from datetime import date
from typing import Optional

import flet as ft

from core.models import Transaction
from ui.theme import AppTheme
from utils.helpers import format_currency, truncate_text
from utils.constants import OWNERSHIP_ICONS, OWNERSHIP_COLORS, OWNERSHIP_LABELS


class TransactionTable(ft.Column):
    """Reusable data table for transactions."""

    def __init__(
        self,
        transactions: list[Transaction],
        on_delete=None,
        on_edit=None,
    ):
        self._transactions = transactions
        self._on_delete = on_delete
        self._on_edit = on_edit

        rows = [self._build_row(tx) for tx in transactions]

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Fecha", size=12, color=AppTheme.TEXT_SECONDARY, width=90),
                    ft.Text("Descripcion", size=12, color=AppTheme.TEXT_SECONDARY, expand=True),
                    ft.Text("Categoria", size=12, color=AppTheme.TEXT_SECONDARY, width=90),
                    ft.Text("Tipo", size=12, color=AppTheme.TEXT_SECONDARY, width=70),
                    ft.Text("Monto", size=12, color=AppTheme.TEXT_SECONDARY, width=120, text_align=ft.TextAlign.END),
                    ft.Text("", width=80),
                ],
                spacing=8,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            bgcolor=AppTheme.SURFACE_VARIANT,
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
        )

        list_view = ft.Column(
            controls=rows if rows else [
                ft.Container(
                    content=ft.Text(
                        "No hay transacciones",
                        color=AppTheme.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=40,
                )
            ],
            spacing=1,
        )

        super().__init__(
            controls=[header, list_view],
            spacing=0,
        )

    def _build_row(self, tx: Transaction) -> ft.Container:
        type_color = AppTheme.SUCCESS if tx.type == "income" else AppTheme.ERROR
        type_prefix = "+" if tx.type == "income" else "-"

        own_icon = OWNERSHIP_ICONS.get(tx.ownership_type, "help")
        own_color = OWNERSHIP_COLORS.get(tx.ownership_type, AppTheme.TEXT_SECONDARY)
        own_label = OWNERSHIP_LABELS.get(tx.ownership_type, tx.ownership_type)
        if tx.type == "income":
            own_label = "Ingreso"
            own_color = AppTheme.SUCCESS
            own_icon = "arrow_downward"

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(tx.date.isoformat(), size=13, color=AppTheme.ON_SURFACE, width=90),
                    ft.Text(
                        truncate_text(tx.description, 35),
                        size=13,
                        color=AppTheme.ON_SURFACE,
                        expand=True,
                    ),
                    ft.Text(tx.category.name if tx.category else "-", size=13, color=AppTheme.TEXT_SECONDARY, width=90),
                    ft.Row(
                        [
                            ft.Icon(name=own_icon, size=14, color=own_color),
                            ft.Text(own_label, size=11, color=own_color),
                        ],
                        spacing=4,
                        width=70,
                    ),
                    ft.Text(
                        f"{type_prefix}{format_currency(tx.amount)}",
                        size=13,
                        color=type_color,
                        width=120,
                        weight=ft.FontWeight.W_600,
                        text_align=ft.TextAlign.END,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_size=16,
                                icon_color=AppTheme.TEXT_SECONDARY,
                                on_click=lambda e, t=tx: self._on_edit and self._on_edit(t),
                                tooltip="Editar",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=16,
                                icon_color=AppTheme.ERROR,
                                on_click=lambda e, t=tx: self._on_delete and self._on_delete(t),
                                tooltip="Eliminar",
                            ),
                        ],
                        spacing=0,
                        width=80,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=6),
            bgcolor=AppTheme.CARD_COLOR if self._transactions.index(tx) % 2 == 0 else AppTheme.SURFACE,
        )
