"""Chart components using Flet fl_chart."""

from decimal import Decimal
import flet as ft

from ui.theme import AppTheme
from utils.helpers import format_currency


class CategoryPieChart(ft.Container):
    """Simple visual representation of expenses by category.

    Uses colored bars since fl_chart is complex to embed.
    In a production app, this would use ft.Canvas or fl_chart.
    """

    def __init__(self, data: list[dict], total: Decimal):
        self._data = data
        self._total = total

        bars = []
        for item in data:
            percentage = (item["total"] / total * 100) if total > 0 else 0
            bars.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    width=12,
                                    height=12,
                                    bgcolor=item["color"],
                                    border_radius=2,
                                ),
                                ft.Text(
                                    item["name"],
                                    size=13,
                                    color=AppTheme.ON_SURFACE,
                                    expand=True,
                                ),
                                ft.Text(
                                    f"{percentage:.1f}%",
                                    size=13,
                                    color=AppTheme.TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    format_currency(item["total"]),
                                    size=13,
                                    color=AppTheme.ON_SURFACE,
                                    weight=ft.FontWeight.W_600,
                                    width=100,
                                    text_align=ft.TextAlign.END,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            content=ft.Container(
                                height=6,
                                bgcolor=item["color"],
                                border_radius=3,
                            ),
                            width=f"{percentage:.1f}%",
                            alignment=ft.Alignment(-1, 0),
                        ),
                    ],
                    spacing=4,
                )
            )
            bars.append(ft.Container(height=8))

        super().__init__(
            content=ft.Column(
                [
                    ft.Text(
                        "Gastos por Categoría",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=AppTheme.ON_SURFACE,
                    ),
                    ft.Container(height=12),
                    *bars,
                ],
                spacing=0,
            ),
            bgcolor=AppTheme.CARD_COLOR,
            border_radius=12,
            padding=20,
        )
