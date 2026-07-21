import flet as ft

from services.category_service import category_service
from ui.components.empty_state import EmptyState
from ui.components.dialogs import CategoryDialog
from ui.theme import AppTheme


def categories_view(page: ft.Page) -> ft.Control:
    categories = category_service.list_all()

    if not categories:
        return EmptyState(
            icon=ft.Icons.LABEL,
            title="Sin categorías",
            subtitle="Crea categorías para organizar tus gastos",
            action_text="Nueva Categoría",
            on_action=lambda _: _open_new_dialog(page),
        )

    from datetime import date
    from services.dashboard_service import dashboard_service
    today = date.today()
    expenses_by_cat = {
        item["name"]: item["total"]
        for item in dashboard_service.get_expenses_by_category(today.year, today.month)
    }

    def _build_cat_item(cat):
        spent = expenses_by_cat.get(cat.name, 0)
        has_budget = cat.monthly_budget and cat.monthly_budget > 0
        ratio = float(spent / cat.monthly_budget) if has_budget else 0.0
        
        progress_color = AppTheme.SUCCESS
        if ratio >= 1.0:
            progress_color = AppTheme.ERROR
        elif ratio >= 0.8:
            progress_color = "#FFA000"

        budget_info = []
        if has_budget:
            budget_info = [
                ft.Text(
                    f"${spent:,.2f} / ${cat.monthly_budget:,.2f} ({ratio * 100:.0f}%)",
                    size=12,
                    color=progress_color if ratio >= 0.8 else AppTheme.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_600 if ratio >= 0.8 else ft.FontWeight.NORMAL,
                ),
                ft.ProgressBar(
                    value=min(ratio, 1.0),
                    color=progress_color,
                    bgcolor=AppTheme.SURFACE_VARIANT,
                    height=4,
                ),
            ]
        else:
            budget_info = [
                ft.Text("Sin presupuesto", size=12, color=AppTheme.TEXT_SECONDARY)
            ]

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(width=12, height=12, bgcolor=cat.color, border_radius=2),
                            ft.Icon(cat.icon, size=20, color=AppTheme.ON_SURFACE),
                            ft.Text(cat.name, size=15, color=AppTheme.ON_SURFACE, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_size=16,
                                icon_color=AppTheme.TEXT_SECONDARY,
                                on_click=lambda _, c=cat: _open_edit_dialog(page, c),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=16,
                                icon_color=AppTheme.ERROR,
                                on_click=lambda _, c=cat: _delete_cat(page, c),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    *budget_info,
                ],
                spacing=4,
            ),
            padding=ft.Padding.all(12),
            bgcolor=AppTheme.SURFACE_VARIANT,
            border_radius=8,
        )

    cat_list = ft.Column(
        [_build_cat_item(cat) for cat in categories],
        spacing=10,
    )

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Categorías", size=22, weight=ft.FontWeight.BOLD, color=AppTheme.ON_BACKGROUND, expand=True),
                    ft.FilledButton(
                        content="Nueva",
                        icon=ft.Icons.ADD,
                        on_click=lambda _: _open_new_dialog(page),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(height=24),
            cat_list,
        ],
        expand=True,
    )


def _open_new_dialog(page: ft.Page):
    dlg = CategoryDialog(page=page, on_saved=lambda: _refresh(page))
    page.show_dialog(dlg)


def _open_edit_dialog(page: ft.Page, cat):
    dlg = CategoryDialog(page=page, on_saved=lambda: _refresh(page), category=cat)
    page.show_dialog(dlg)


def _delete_cat(page: ft.Page, cat):
    category_service.delete(cat.id)
    _refresh(page)


def _refresh(page: ft.Page):
    if hasattr(page, '_navigate'):
        page._navigate(3)
