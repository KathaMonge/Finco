from datetime import date

import flet as ft

from services.dashboard_service import dashboard_service
from ui.components.empty_state import EmptyState
from ui.components.summary_cards import SummaryCards
from ui.components.charts import CategoryPieChart
from ui.components.split_expense_card import SplitExpenseCard
from ui.theme import AppTheme


def dashboard_view(page: ft.Page) -> ft.Control:
    today = date.today()
    summary = dashboard_service.get_month_summary(today.year, today.month)
    expenses_by_cat = dashboard_service.get_expenses_by_category(today.year, today.month)
    recent = dashboard_service.get_recent_transactions(5)

    has_data = summary["transaction_count"] > 0

    if not has_data:
        return EmptyState(
            icon=ft.Icons.DASHBOARD,
            title="Sin datos este mes",
            subtitle="Comienza registrando tus transacciones desde la sección 'Transacciones'",
            action_text="Ir a Transacciones",
            on_action=lambda _: page._navigate(1) if hasattr(page, '_navigate') else None,
        )

    cards = SummaryCards(
        balance=summary["balance"],
        incomes=summary["incomes"],
        expenses=summary["expenses"],
    )

    split_card = SplitExpenseCard(
        total_expenses=summary["expenses"],
        shared_expenses=summary["shared_expenses"],
        personal_expenses=summary["personal_expenses"],
        external_expenses=summary["external_expenses"],
        shared_due=summary["shared_due"],
        split_50_total=summary["split_50_total"],
        month_name=today.strftime("%B %Y"),
    )

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

    return ft.Column(
        [
            ft.Text(
                f"Resumen de {today.strftime('%B %Y')}",
                size=22,
                weight=ft.FontWeight.BOLD,
                color=AppTheme.ON_BACKGROUND,
            ),
            ft.Container(height=24),
            cards,
            ft.Container(height=16),
            split_card,
            ft.Container(height=24),
            ft.Row(
                [right_content],
                expand=True,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
