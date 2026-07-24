"""Onboarding wizard for first-time users."""

import flet as ft

from ui.theme import AppTheme
from core.config import DEFAULT_CATEGORIES
from services.category_service import category_service
from services.account_service import account_service
from services.participant_service import participant_service
from core.schemas import AccountCreate, CategoryCreate, ParticipantCreate

PARTICIPANT_COLORS = ["#4ECDC4", "#FF6B6B", "#45B7D1", "#FFD93D", "#96CEB4", "#DDA0DD"]


class OnboardingWizard(ft.Container):
    """6-step onboarding wizard for first-time users."""

    def __init__(self, page: ft.Page, on_complete):
        self._page = page
        self._on_complete = on_complete
        self._step = 0
        self._participant_count = 2
        self._participant_fields: list[ft.TextField] = []
        self._participant_count_text = ft.Text("2", size=20, weight=ft.FontWeight.BOLD, color=AppTheme.ON_BACKGROUND)
        self._participant_fields_col = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self._steps = [
            self._step_welcome(),
            self._step_create_account(),
            self._step_participants(),
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
                for i in range(6)
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

    def _step_participants(self) -> ft.Column:
        self._render_participant_fields()
        return ft.Column(
            [
                ft.Icon(ft.Icons.PEOPLE, size=64, color=AppTheme.ACCENT),
                ft.Container(height=24),
                ft.Text(
                    "¿Con cuántas personas compartís gastos?",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.ON_BACKGROUND,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Podés dividir gastos por categoría (ej. renta entre roommates) "
                    "y ajustar cada transacción despues.",
                    size=14,
                    color=AppTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=24),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                            on_click=lambda _: self._change_participant_count(-1),
                        ),
                        self._participant_count_text,
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                            on_click=lambda _: self._change_participant_count(1),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=16),
                self._participant_fields_col,
                ft.Container(height=24),
                ft.FilledButton(
                    content="Crear personas",
                    on_click=lambda _: self._create_participants_and_next(),
                    icon=ft.Icons.CHECK,
                ),
                ft.Container(height=8),
                ft.TextButton(
                    content="Omitir paso",
                    on_click=lambda _: self._skip_participants(),
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

    def _render_participant_fields(self):
        self._participant_count_text.value = str(self._participant_count)
        self._participant_fields = [
            ft.TextField(
                label=f"Persona {i + 1}",
                value="Yo" if i == 0 else "",
                width=280,
            )
            for i in range(self._participant_count)
        ]
        self._participant_fields_col.controls = self._participant_fields

    def _change_participant_count(self, delta: int):
        new_count = self._participant_count + delta
        if new_count < 1 or new_count > 6:
            return
        self._participant_count = new_count
        self._render_participant_fields()
        if self._participant_fields_col.page:
            self._participant_count_text.update()
            self._participant_fields_col.update()

    def _create_participants_and_next(self):
        for i, field in enumerate(self._participant_fields):
            name = (field.value or "").strip() or f"Persona {i + 1}"
            participant_service.create(
                ParticipantCreate(name=name, color=PARTICIPANT_COLORS[i % len(PARTICIPANT_COLORS)])
            )
        self._next_step()

    def _skip_participants(self):
        participant_service.create(ParticipantCreate(name="Yo", color=PARTICIPANT_COLORS[0]))
        self._next_step()

    def _create_categories_and_next(self):
        category_service.seed_defaults()
        self._next_step()

    def _complete(self):
        if self._on_complete:
            self._on_complete()
