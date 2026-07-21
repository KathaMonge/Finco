"""Onboarding wizard for first-time users."""

import flet as ft

from ui.theme import AppTheme
from core.config import DEFAULT_CATEGORIES
from services.category_service import category_service
from services.account_service import account_service
from core.schemas import AccountCreate, CategoryCreate


class OnboardingWizard(ft.Container):
    """5-step onboarding wizard for first-time users."""

    def __init__(self, page: ft.Page, on_complete):
        self._page = page
        self._on_complete = on_complete
        self._step = 0

        self._steps = [
            self._step_welcome(),
            self._step_create_account(),
            self._step_create_categories(),
            self._step_first_transaction(),
            self._step_done(),
        ]

        self._content_area = ft.Column(
            controls=[self._steps[0]],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._progress = ft.Row(
            controls=[
                ft.Container(
                    width=40, height=4,
                    bgcolor=AppTheme.PRIMARY,
                    border_radius=2,
                ) if i == 0 else ft.Container(
                    width=40, height=4,
                    bgcolor=AppTheme.SURFACE_VARIANT,
                    border_radius=2,
                )
                for i in range(5)
            ],
            spacing=4,
        )

        super().__init__(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    self._progress,
                    ft.Container(height=40),
                    self._content_area,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=AppTheme.BACKGROUND,
            expand=True,
            padding=40,
        )

    def _step_welcome(self) -> ft.Column:
        return ft.Column(
            [
                ft.Icon(ft.Icons.WAVING_HAND, size=64, color=AppTheme.PRIMARY),
                ft.Container(height=24),
                ft.Text(
                    "¡Bienvenido a Finco!",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.ON_BACKGROUND,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Tu asistente personal de finanzas. "
                    "Registra tus gastos, escanea vouchers con OCR, "
                    "y lleva el control de tu dinero.",
                    size=16,
                    color=AppTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                ft.FilledButton(
                    content="Comenzar",
                    on_click=lambda _: self._next_step(),
                    icon=ft.Icons.ARROW_FORWARD,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _step_create_account(self) -> ft.Column:
        return ft.Column(
            [
                ft.Icon(ft.Icons.ACCOUNT_BALANCE, size=64, color=AppTheme.SECONDARY),
                ft.Container(height=24),
                ft.Text(
                    "Crea tu primera cuenta",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.ON_BACKGROUND,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Puedes tener cuentas de efectivo, débito o crédito.",
                    size=14,
                    color=AppTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=24),
                ft.FilledButton(
                    content="Crear cuenta de Efectivo",
                    on_click=lambda _: self._create_account_and_next("cash"),
                    icon=ft.Icons.PAYMENTS,
                ),
                ft.Container(height=8),
                ft.OutlinedButton(
                    content="Crear cuenta de Débito",
                    on_click=lambda _: self._create_account_and_next("debit"),
                    icon=ft.Icons.CREDIT_CARD,
                ),
                ft.Container(height=8),
                ft.OutlinedButton(
                    content="Crear cuenta de Crédito",
                    on_click=lambda _: self._create_account_and_next("credit"),
                    icon=ft.Icons.CREDIT_SCORE,
                ),
                ft.Container(height=16),
                ft.TextButton(
                    content="Omitir paso",
                    on_click=lambda _: self._next_step(),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _step_create_categories(self) -> ft.Column:
        return ft.Column(
            [
                ft.Icon(ft.Icons.LABEL, size=64, color=AppTheme.ACCENT),
                ft.Container(height=24),
                ft.Text(
                    "Categorías predefinidas",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.ON_BACKGROUND,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Vamos a crear categorías básicas para organizar tus gastos.",
                    size=14,
                    color=AppTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=24),
                ft.Column(
                    [ft.Text(f"• {cat['name']}", size=14, color=AppTheme.ON_SURFACE) for cat in DEFAULT_CATEGORIES],
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=24),
                ft.FilledButton(
                    content="Crear categorías",
                    on_click=lambda _: self._create_categories_and_next(),
                    icon=ft.Icons.CHECK,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _step_first_transaction(self) -> ft.Column:
        return ft.Column(
            [
                ft.Icon(ft.Icons.RECEIPT_LONG, size=64, color=AppTheme.SUCCESS),
                ft.Container(height=24),
                ft.Text(
                    "¡Todo listo!",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.ON_BACKGROUND,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Ya puedes empezar a registrar tus transacciones "
                    "y explorar el dashboard.",
                    size=14,
                    color=AppTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                ft.FilledButton(
                    content="Ir al Dashboard",
                    on_click=lambda _: self._next_step(),
                    icon=ft.Icons.DASHBOARD,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _step_done(self) -> ft.Column:
        return ft.Column(
            [
                ft.Icon(ft.Icons.CELEBRATION, size=64, color=AppTheme.ACCENT),
                ft.Container(height=24),
                ft.Text(
                    "¡Finco está listo!",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.ON_BACKGROUND,
                ),
                ft.Container(height=40),
                ft.Text(
                    "Consejos rápidos:\n"
                    "• Usa Ctrl+N para agregar una transacción\n"
                    "• Escanea vouchers con OCR Scan\n"
                    "• Revisa tu dashboard mensualmente",
                    size=14,
                    color=AppTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                ft.FilledButton(
                    content="¡Empezar!",
                    on_click=lambda _: self._complete(),
                    icon=ft.Icons.ROCKET_LAUNCH,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _next_step(self):
        self._step += 1
        if self._step >= len(self._steps):
            self._complete()
            return
        self._content_area.controls = [self._steps[self._step]]
        self._progress.controls = [
            ft.Container(
                width=40, height=4,
                bgcolor=AppTheme.PRIMARY if i <= self._step else AppTheme.SURFACE_VARIANT,
                border_radius=2,
            )
            for i in range(5)
        ]
        self.update()

    def _create_account_and_next(self, acc_type: str):
        type_labels = {"cash": "Efectivo", "debit": "Débito", "credit": "Crédito"}
        account_service.create(
            AccountCreate(
                name=f"Mi {type_labels[acc_type]}",
                type=acc_type,
                balance=0,
            )
        )
        self._next_step()

    def _create_categories_and_next(self):
        category_service.seed_defaults()
        self._next_step()

    def _complete(self):
        if self._on_complete:
            self._on_complete()
