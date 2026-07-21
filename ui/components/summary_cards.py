from decimal import Decimal

import flet as ft

from ui.theme import AppTheme
from utils.helpers import format_currency


class SummaryCard(ft.Container):
    """Individual summary card with icon, label, value, and color."""

    def __init__(self, icon: str, label: str, value: Decimal, color: str, currency: str = "ARS"):
        self._icon = icon
        self._label = label
        self._value = value
        self._color = color
        self._currency = currency

        super().__init__(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                name=self._icon,
                                color=self._color,
                                size=24,
                            ),
                            ft.Text(
                                self._label,
                                size=14,
                                color=AppTheme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        format_currency(self._value, self._currency),
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=self._color,
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


class SummaryCards(ft.Row):
    """Row of summary cards for the dashboard."""

    def __init__(self, balance: Decimal, incomes: Decimal, expenses: Decimal, currency: str = "ARS"):
        super().__init__(
            controls=[
                SummaryCard(
                    icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                    label="Balance",
                    value=balance,
                    color=AppTheme.PRIMARY,
                    currency=currency,
                ),
                SummaryCard(
                    icon=ft.Icons.ARROW_DOWNWARD,
                    label="Ingresos",
                    value=incomes,
                    color=AppTheme.SUCCESS,
                    currency=currency,
                ),
                SummaryCard(
                    icon=ft.Icons.ARROW_UPWARD,
                    label="Gastos",
                    value=expenses,
                    color=AppTheme.ERROR,
                    currency=currency,
                ),
            ],
            spacing=16,
        )
