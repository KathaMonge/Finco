"""Main application with routing, theme, and keyboard shortcuts."""

from datetime import date

import flet as ft

from core.database import init_db
from services.category_service import category_service
from ui.theme import AppTheme, page_styles
from ui.components.sidebar import Sidebar
from ui.components.keyboard import register_shortcuts
from core.settings import get as get_settings, set as set_settings
from ui.components.onboarding import OnboardingWizard
from ui.views.dashboard_view import dashboard_view
from ui.views.transactions_view import transactions_view
from ui.views.categories_view import categories_view
from ui.views.accounts_view import accounts_view
from ui.views.ocr_scan_view import ocr_scan_view


def _build_splash(page: ft.Page):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("FC", size=48, weight=ft.FontWeight.BOLD, color=AppTheme.PRIMARY),
                ft.Container(height=8),
                ft.ProgressRing(width=32, height=32, color=AppTheme.PRIMARY),
                ft.Container(height=16),
                ft.Text("Cargando...", size=14, color=AppTheme.TEXT_SECONDARY),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
        ),
        bgcolor=AppTheme.BACKGROUND,
        alignment=ft.Alignment(0, 0),
        expand=True,
    )


async def main(page: ft.Page):
    page.title = "Finco"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 900
    page.window.min_height = 600

    page_styles(page)

    splash = _build_splash(page)
    page.add(splash)
    page.update()

    init_db()
    category_service.seed_defaults()

    content_area = ft.Container(expand=True, padding=ft.Padding.all(24))
    views = {
        0: lambda: dashboard_view(page),
        1: lambda: transactions_view(page),
        2: lambda: ocr_scan_view(page),
        3: lambda: categories_view(page),
        4: lambda: accounts_view(page),
    }

    def navigate(index: int):
        nonlocal views
        # Clear any stale search state when navigating to a view
        if index != 1:
            page._search_query = None
        if index in views:
            content_area.content = views[index]()
            page.update()

    page._navigate = navigate

    sidebar = Sidebar(on_navigate=navigate)

    def check_onboarding():
        nonlocal content_area
        if get_settings("onboarding_completed"):
            return
        wizard = OnboardingWizard(
            page=page,
            on_complete=lambda: _finish_onboarding(wizard, content_area),
        )
        content_area.content = wizard
        page.update()

    def _finish_onboarding(wizard, content):
        set_settings("onboarding_completed", True)
        content.content = views[0]()
        page.update()

    # Remove splash and show main UI
    page.clean()
    page.add(
        ft.Row(
            [
                sidebar,
                ft.VerticalDivider(width=1, color=AppTheme.BORDER_COLOR),
                content_area,
            ],
            expand=True,
            spacing=0,
        )
    )

    register_shortcuts(page, {
        "Ctrl+1": lambda: navigate(0),
        "Ctrl+2": lambda: navigate(1),
        "Ctrl+3": lambda: navigate(2),
        "Ctrl+4": lambda: navigate(3),
        "Ctrl+5": lambda: navigate(4),
        "Ctrl+N": lambda: _open_new_tx(page),
    })

    check_onboarding()


def _open_new_tx(page: ft.Page):
    from ui.components.dialogs import TransactionDialog
    navigate = getattr(page, "_navigate", None)
    dialog = TransactionDialog(
        page=page,
        on_saved=lambda: navigate(1) if navigate else None,
    )
    page.show_dialog(dialog)
