from decimal import Decimal
from typing import Optional

import flet as ft

from ui.theme import AppTheme
from utils.helpers import format_currency
from utils.constants import OWNERSHIP_TYPES, OWNERSHIP_COLORS, OWNERSHIP_LABELS


class SplitExpenseCard(ft.Container):
    def __init__(
        self,
        total_expenses: Decimal,
        shared_expenses: Decimal,
        personal_expenses: Decimal,
        external_expenses: Decimal,
        shared_due: Decimal,
        split_50_total: Decimal,
        month_name: str = "",
        participants: Optional[list[dict]] = None,
    ):
        self._total_expenses = total_expenses
        self._shared_expenses = shared_expenses
        self._personal_expenses = personal_expenses
        self._external_expenses = external_expenses
        self._shared_due = shared_due
        self._split_50_total = split_50_total
        self._month_name = month_name
        self._participants = participants or []
        self._split_pct = Decimal("50")
        self._summary_text = ft.Text("", size=12, color=AppTheme.TEXT_SECONDARY)

        badge_text = f"{len(self._participants)} personas" if self._participants else "50%"
        header = ft.Row(
            [
                ft.Icon(name=ft.Icons.CALL_SPLIT, color=AppTheme.ACCENT, size=22),
                ft.Text("Rendicion de Gastos", size=16, weight=ft.FontWeight.W_600, color=AppTheme.ON_SURFACE),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(badge_text, size=11, color=AppTheme.PRIMARY, weight=ft.FontWeight.W_600),
                    bgcolor=AppTheme.SURFACE_VARIANT,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
            ],
            spacing=8,
        )

        self._total_value = ft.Text(
            format_currency(self._total_expenses),
            size=20,
            weight=ft.FontWeight.BOLD,
            color=AppTheme.ON_SURFACE,
        )

        self._shared_value = ft.Text(
            format_currency(self._shared_due),
            size=28,
            weight=ft.FontWeight.BOLD,
            color=AppTheme.PRIMARY,
        )

        if self._participants:
            blocks = [
                self._ownership_block(p["name"], p["total_owed"], p["color"])
                for p in self._participants
            ]
        else:
            blocks = [
                self._ownership_block(
                    "Compartido", self._shared_expenses, OWNERSHIP_COLORS["shared"]
                ),
                self._ownership_block(
                    "Personal", self._personal_expenses, OWNERSHIP_COLORS["personal"]
                ),
                self._ownership_block(
                    "Externo", self._external_expenses, OWNERSHIP_COLORS["external"]
                ),
            ]

        self._split_bar = ft.Container(
            content=ft.Row(blocks, spacing=8, wrap=True),
            bgcolor=AppTheme.SURFACE_VARIANT,
            border_radius=8,
            padding=12,
        )

        self._copy_btn = ft.FilledButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CONTENT_COPY, size=16, color=AppTheme.BACKGROUND),
                    ft.Text("Copiar Resumen", size=13, color=AppTheme.BACKGROUND),
                ],
                spacing=6,
            ),
            on_click=lambda _: None,
            bgcolor=AppTheme.ACCENT,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        totals_row_children = [
            ft.Column(
                [
                    ft.Text("Gastos del Mes", size=12, color=AppTheme.TEXT_SECONDARY),
                    self._total_value,
                ],
                spacing=2,
            ),
            ft.Container(expand=True),
        ]
        if not self._participants:
            totals_row_children.append(
                ft.Column(
                    [
                        ft.Text("A Pagar (50%)", size=12, color=AppTheme.TEXT_SECONDARY),
                        self._shared_value,
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                )
            )

        super().__init__(
            content=ft.Column(
                [
                    header,
                    ft.Container(height=12),
                    ft.Row(totals_row_children),
                    ft.Container(height=12),
                    self._split_bar,
                    ft.Container(height=8),
                    ft.Row(
                        [
                            self._summary_text,
                            ft.Container(expand=True),
                            self._copy_btn,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=AppTheme.CARD_COLOR,
            border_radius=12,
            padding=20,
        )

        self._build_summary()
        self._copy_btn.on_click = lambda _: self._copy_to_clipboard()

    def _ownership_block(self, label: str, amount: Decimal, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, size=11, color=AppTheme.TEXT_SECONDARY),
                    ft.Text(format_currency(amount), size=14, weight=ft.FontWeight.W_600, color=color),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
        )

    def _build_summary(self):
        month = self._month_name or "este mes"
        lines = [
            f"Resumen de Gastos - {month}",
            f"Total Gastos: {format_currency(self._total_expenses)}",
        ]
        if self._participants:
            for p in self._participants:
                lines.append(f"{p['name']}: {format_currency(p['total_owed'])}")
        else:
            lines.extend([
                f"Compartido: {format_currency(self._shared_expenses)}",
                f"Personal: {format_currency(self._personal_expenses)}",
                f"Externo: {format_currency(self._external_expenses)}",
                f"50% a Pagar: {format_currency(self._split_50_total)}",
            ])
            if self._shared_due != self._split_50_total:
                lines.append(f"Corresponde por compartidos: {format_currency(self._shared_due)}")
        self._summary = "\n".join(lines)
        self._summary_text.value = f"{len(lines)} lineas · click para copiar"

    def _copy_to_clipboard(self):
        if not self.page:
            return
        self.page.set_clipboard(self._summary)
        from ui.components.snack_undo import show_snackbar
        show_snackbar(
            self.page,
            ft.SnackBar(
                content=ft.Text("Resumen copiado al portapapeles"),
                bgcolor=AppTheme.SUCCESS,
                duration=2000,
            ),
        )
