import flet as ft

from ui.theme import AppTheme
from utils.constants import NAV_ITEMS


class Sidebar(ft.Container):
    """NavigationRail-based sidebar with icon + label for each section."""

    def __init__(self, on_navigate):
        self._on_navigate = on_navigate
        self._selected_index = 0

        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=self._on_rail_change,
            bgcolor=AppTheme.SURFACE,
            leading=ft.Container(
                content=ft.Text(
                    "FC",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.PRIMARY,
                ),
                padding=ft.Padding.symmetric(vertical=16),
                alignment=ft.Alignment(0, 0),
            ),
            destinations=[
                ft.NavigationRailDestination(
                    icon=item["icon"],
                    selected_icon=item["icon"],
                    label=item["label"],
                    tooltip=f"{item['label']} ({item['shortcut']})",
                )
                for item in NAV_ITEMS
            ],
            height=float("inf"),
        )

        super().__init__(
            content=self.rail,
            bgcolor=AppTheme.SURFACE,
            border=ft.Border.all(1, AppTheme.BORDER_COLOR),
            height=float("inf"),
        )

    def _on_rail_change(self, e):
        self._selected_index = e.control.selected_index
        if self._on_navigate:
            self._on_navigate(e.control.selected_index)

    def select(self, index: int):
        self._selected_index = index
        self.rail.selected_index = index
        self.update()
