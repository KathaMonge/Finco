from datetime import date

import flet as ft

from services.dashboard_service import dashboard_service
from services.category_service import category_service
from ui.components.empty_state import EmptyState
from ui.components.summary_cards import SummaryCards
from ui.components.charts import CategoryPieChart
from ui.components.split_expense_card import SplitExpenseCard
from ui.components.card import AppCard
from ui.theme import AppTheme
from utils.helpers import format_currency


MONTHS_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _build_budget_alerts(year: int, month: int) -> list[ft.Control]:
    report = category_service.get_budget_report(year, month)
    alerts = []
    for item in report:
        if not item["percentage"]:
            continue
        pct = item["percentage"]
        if pct >= 100:
            color = AppTheme.ERROR
            icon = ft.Icons.WARNING
            label = f"{item['category'].name}: {format_currency(item['spent'])} / {format_currency(item['budget'])} ({pct:.0f}%)"
        elif pct >= 80:
            color = AppTheme.WARNING
            icon = ft.Icons.INFO
            label = f"{item['category'].name}: {format_currency(item['spent'])} / {format_currency(item['budget'])} ({pct:.0f}%)"
        else:
            continue
        alerts.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(name=icon, color=color, size=18),
                        ft.Text(label, size=13, color=color, expand=True),
                    ],
                    spacing=8,
                ),
                bgcolor=AppTheme.SURFACE_VARIANT,
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            )
        )
    return alerts


def _build_top_merchants(year: int, month: int) -> ft.Control | None:
    merchants = dashboard_service.get_top_merchants(year, month, limit=5)
    if not merchants:
        return None
    rows = []
    for i, m in enumerate(merchants):
        rows.append(
            ft.Row(
                [
                    ft.Text(f"{i + 1}.", size=13, color=AppTheme.TEXT_SECONDARY, width=24),
                    ft.Text(m["merchant"], size=13, color=AppTheme.ON_SURFACE, expand=True),
                    ft.Text(
                        f"{m['count']}x",
                        size=12,
                        color=AppTheme.TEXT_SECONDARY,
                        width=36,
                        text_align=ft.TextAlign.END,
                    ),
                    ft.Text(
                        format_currency(m["total"]),
                        size=13,
                        color=AppTheme.ON_SURFACE,
                        weight=ft.FontWeight.W_600,
                        width=100,
                        text_align=ft.TextAlign.END,
                    ),
                ],
                spacing=4,
            )
        )
    return AppCard(
        title="Top 5 Comercios",
        content=ft.Column(rows, spacing=4),
    )


def dashboard_view(page: ft.Page) -> ft.Control:
    today = date.today()

    selected_month = ft.Text(
        f"{MONTHS_ES[today.month]} {today.year}",
        size=22,
        weight=ft.FontWeight.BOLD,
        color=AppTheme.ON_BACKGROUND,
    )

    month_options = []
    for m in range(1, 13):
        month_options.append(ft.dropdown.Option(key=f"{today.year}-{m:02d}", text=f"{MONTHS_ES[m]} {today.year}"))
    for y in [today.year - 1]:
        for m in range(1, 13):
            month_options.append(ft.dropdown.Option(key=f"{y}-{m:02d}", text=f"{MONTHS_ES[m]} {y}"))

    current_key = f"{today.year}-{today.month:02d}"

    def refresh_dashboard(e):
        key = period_dropdown.value
        if not key:
            return
        y, m = int(key.split("-")[0]), int(key.split("-")[1])
        _reload(y, m)

    period_dropdown = ft.Dropdown(
        value=current_key,
        options=month_options,
        on_select=refresh_dashboard,
        width=200,
        text_size=14,
        text_style=ft.TextStyle(color=AppTheme.ON_SURFACE),
        bgcolor=AppTheme.SURFACE_VARIANT,
        border_color=AppTheme.BORDER_COLOR,
        focused_border_color=AppTheme.PRIMARY,
    )

    content_column = ft.Column(spacing=0, expand=True)

    def _reload(year: int, month: int):
        summary = dashboard_service.get_month_summary(year, month)
        expenses_by_cat = dashboard_service.get_expenses_by_category(year, month)
        recent = dashboard_service.get_recent_transactions(5)
        has_data = summary["transaction_count"] > 0

        content_column.controls.clear()
        selected_month.value = f"{MONTHS_ES[month]} {year}"

        if not has_data:
            content_column.controls.append(
                EmptyState(
                    icon=ft.Icons.DASHBOARD,
                    title="Sin datos este mes",
                    subtitle="Comienza registrando tus transacciones desde la seccion 'Transacciones'",
                    action_text="Ir a Transacciones",
                    on_action=lambda _: page._navigate(1) if hasattr(page, '_navigate') else None,
                )
            )
        else:
            cards = SummaryCards(
                balance=summary["balance"],
                incomes=summary["incomes"],
                expenses=summary["expenses"],
            )

            participant_summary = dashboard_service.get_participant_summary(year, month)
            split_card = SplitExpenseCard(
                total_expenses=summary["expenses"],
                shared_expenses=summary["shared_expenses"],
                personal_expenses=summary["personal_expenses"],
                external_expenses=summary["external_expenses"],
                shared_due=summary["shared_due"],
                split_50_total=summary["split_50_total"],
                month_name=f"{MONTHS_ES[month]} {year}",
                participants=participant_summary if len(participant_summary) >= 2 else None,
            )

            budget_alerts = _build_budget_alerts(year, month)
            budget_section = None
            if budget_alerts:
                budget_section = AppCard(
                    title="Alertas de Presupuesto",
                    title_icon=ft.Icons.NOTIFICATIONS_ACTIVE,
                    content=ft.Column(budget_alerts, spacing=4),
                )

            top_merchants = _build_top_merchants(year, month)

            recent_list = ft.Column(
                [
                    ft.Container(height=16),
                    ft.Text("Ultimas Transacciones", size=16, weight=ft.FontWeight.W_600, color=AppTheme.ON_SURFACE),
                    ft.Container(height=8),
                    *[
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(t.date.isoformat(), size=12, color=AppTheme.TEXT_SECONDARY),
                                    ft.Text(t.description, size=13, color=AppTheme.ON_SURFACE, expand=True),
                                    ft.Text(
                                        f"{'+' if t.type == 'income' else '-'}${t.amount:,.2f}",
                                        size=13,
                                        color=AppTheme.SUCCESS if t.type == "income" else AppTheme.ERROR,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                ]
                            ),
                            padding=ft.Padding.symmetric(vertical=4),
                        )
                        for t in recent
                    ],
                ]
            )

            right_content = ft.Column(
                [
                    CategoryPieChart(expenses_by_cat, summary["expenses"]),
                    ft.Container(height=16),
                    recent_list,
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

            left_items = [
                cards,
                ft.Container(height=16),
                split_card,
            ]
            if budget_section:
                left_items.extend([ft.Container(height=16), budget_section])
            if top_merchants:
                left_items.extend([ft.Container(height=16), top_merchants])

            content_column.controls.extend([
                ft.Column(left_items, spacing=0, expand=True),
                ft.Container(height=16),
                right_content,
            ])

        page.update()

    _reload(today.year, today.month)

    return ft.Column(
        [
            ft.Row(
                [
                    selected_month,
                    ft.Container(expand=True),
                    period_dropdown,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=24),
            content_column,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
