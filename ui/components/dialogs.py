from datetime import date
from decimal import Decimal

import flet as ft

from core.schemas import TransactionCreate, CategoryCreate, AccountCreate, SplitEntry
from services.transaction_service import transaction_service
from services.category_service import category_service
from services.account_service import account_service
from services.participant_service import participant_service
from ui.components.snack_undo import show_snackbar
from ui.theme import AppTheme
from utils.constants import OWNERSHIP_TYPES, OWNERSHIP_LABELS, OWNERSHIP_COLORS


class TransactionDialog(ft.AlertDialog):
    """Dialog for creating/editing a transaction."""

    def __init__(self, page: ft.Page, on_saved, transaction=None):
        self._page = page
        self._on_saved = on_saved
        self._transaction = transaction
        self._ready = False
        is_edit = transaction is not None

        categories = category_service.list_all()
        accounts = account_service.list_all()

        if not categories or not accounts:
            super().__init__(
                title=ft.Text("Configuracion incompleta"),
                content=ft.Text(
                    "Necesitas al menos una categoria y una cuenta primero.\n"
                    "Ve a las secciones Categorias y Cuentas para crearlas.",
                    color=AppTheme.TEXT_SECONDARY,
                ),
                actions=[ft.TextButton("Cerrar", on_click=lambda e: self._close())],
            )
            return

        self._ready = True

        self._amount = ft.TextField(
            label="Monto",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="0.00",
            width=200,
            prefix=ft.Text("$ "),
            border_color=AppTheme.BORDER_COLOR,
        )

        self._description = ft.TextField(
            label="Descripcion",
            hint_text="Ej: Supermercado",
            expand=True,
            multiline=False,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._date = ft.TextField(
            label="Fecha",
            hint_text="YYYY-MM-DD",
            value=date.today().isoformat(),
            width=150,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._category_dd = ft.Dropdown(
            label="Categoria",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in categories],
            value=str(categories[0].id),
            width=200,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._account_dd = ft.Dropdown(
            label="Cuenta",
            options=[ft.dropdown.Option(str(a.id), a.name) for a in accounts],
            value=str(accounts[0].id),
            width=200,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._type_dd = ft.SegmentedButton(
            segments=[
                ft.Segment("expense", label="Gasto"),
                ft.Segment("income", label="Ingreso"),
            ],
            selected=["expense"],
        )

        self._ownership_dd = ft.Dropdown(
            label="Tipo de gasto",
            options=[
                ft.dropdown.Option(t["value"], t["label"])
                for t in OWNERSHIP_TYPES
            ],
            value="shared",
            width=200,
            border_color=AppTheme.BORDER_COLOR,
            on_select=self._on_ownership_change,
        )

        self._split_ratio = ft.TextField(
            label="Tu %",
            hint_text="50",
            value="50",
            width=100,
            suffix=ft.Text("%"),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._ownership_info = ft.Text(
            "Se divide 50/50 con tu papa",
            size=12,
            color=OWNERSHIP_COLORS["shared"],
        )

        self._participants = participant_service.list_active()
        self._split_fields: dict[int, ft.TextField] = {}
        self._split_section = ft.Column(visible=False, spacing=8)
        if len(self._participants) >= 2:
            existing_splits: dict[int, Decimal] = {}
            if is_edit:
                existing_splits = {
                    s.participant_id: s.percentage
                    for s in transaction_service.get_splits(transaction.id)
                }
            elif categories:
                existing_splits = {
                    s.participant_id: s.percentage
                    for s in category_service.get_default_split(categories[0].id)
                }
            for participant in self._participants:
                field = ft.TextField(
                    label=participant.name,
                    value=str(existing_splits.get(participant.id, "")),
                    suffix_text="%",
                    width=110,
                    border_color=AppTheme.BORDER_COLOR,
                )
                self._split_fields[participant.id] = field
            self._split_section.visible = True
            self._split_section.controls = [
                ft.Text("Division entre personas (opcional)", size=12, color=AppTheme.TEXT_SECONDARY),
                ft.Row(list(self._split_fields.values()), spacing=12, wrap=True),
            ]

        if is_edit:
            self._amount.value = str(transaction.amount)
            self._description.value = transaction.description
            self._date.value = transaction.date.isoformat()
            self._category_dd.value = str(transaction.category_id)
            self._account_dd.value = str(transaction.account_id)
            self._type_dd.selected = [transaction.type]
            self._ownership_dd.value = transaction.ownership_type
            pct = int(transaction.split_ratio * 100)
            self._split_ratio.value = str(pct)
            self._update_ownership_info(transaction.ownership_type)

        super().__init__(
            title=ft.Text("Editar Transaccion" if is_edit else "Nueva Transaccion"),
            content=ft.Column(
                [
                    ft.Row([self._amount, self._type_dd], spacing=16),
                    self._description,
                    ft.Row([self._date, self._category_dd, self._account_dd], spacing=16),
                    ft.Row(
                        [self._ownership_dd, self._split_ratio],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    self._ownership_info,
                    self._split_section,
                ],
                width=600,
                height=360 if not self._split_section.visible else 420,
                spacing=12,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close()),
                ft.FilledButton(
                    "Guardar",
                    on_click=lambda e: self._save(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_ownership_change(self, e):
        self._update_ownership_info(e.control.value)

    def _update_ownership_info(self, ownership: str):
        descriptions = {
            "shared": "Se divide con tu papa segun el % indicado",
            "personal": "Pagas el 100% — no se rinde a tu papa",
            "external": "No pagas nada — lo cubre tu papa",
        }
        self._ownership_info.value = descriptions.get(ownership, "")
        self._ownership_info.color = OWNERSHIP_COLORS.get(ownership, AppTheme.TEXT_SECONDARY)
        visible = ownership == "shared"
        self._split_ratio.visible = visible
        self._ownership_info.update()
        self._split_ratio.update()

    def _save(self):
        try:
            if not self._account_dd.value or not self._category_dd.value:
                show_snackbar(self._page, 
                    ft.SnackBar(content=ft.Text("Selecciona una cuenta y categoria"), bgcolor=AppTheme.WARNING)
                )
                return
            if not self._amount.value or not self._description.value:
                show_snackbar(self._page, 
                    ft.SnackBar(content=ft.Text("Completa todos los campos requeridos"), bgcolor=AppTheme.WARNING)
                )
                return

            ownership = self._ownership_dd.value
            pct = int(self._split_ratio.value or "50")
            split_ratio = Decimal(pct) / 100

            data = TransactionCreate(
                account_id=int(self._account_dd.value),
                category_id=int(self._category_dd.value),
                amount=Decimal(self._amount.value.replace(",", ".")),
                date=date.fromisoformat(self._date.value),
                description=self._description.value,
                type=self._type_dd.selected[0],
                ownership_type=ownership,
                split_ratio=split_ratio,
            )
            if self._transaction:
                from core.schemas import TransactionUpdate
                update_data = TransactionUpdate(
                    account_id=data.account_id,
                    category_id=data.category_id,
                    amount=data.amount,
                    date=data.date,
                    description=data.description,
                    type=data.type,
                    ownership_type=ownership,
                    split_ratio=split_ratio,
                )
                transaction_service.update(self._transaction.id, update_data)
                tx_id = self._transaction.id
            else:
                tx = transaction_service.create(data)
                tx_id = tx.id

            if self._split_fields:
                splits = [
                    SplitEntry(participant_id=pid, percentage=Decimal(field.value))
                    for pid, field in self._split_fields.items()
                    if field.value and field.value.strip()
                ]
                transaction_service.set_splits(tx_id, splits)

            self._close()
            if self._on_saved:
                self._on_saved()
        except Exception as ex:
            show_snackbar(self._page,
                ft.SnackBar(
                    content=ft.Text(f"Error: {ex}"),
                    bgcolor=AppTheme.ERROR,
                )
            )

    def _close(self):
        self.open = False
        self.update()


class CategoryDialog(ft.AlertDialog):
    """Dialog for creating/editing a category."""

    def __init__(self, page: ft.Page, on_saved, category=None):
        self._page = page
        self._on_saved = on_saved
        self._category = category
        is_edit = category is not None

        self._name = ft.TextField(
            label="Nombre",
            hint_text="Ej: Alimentación",
            expand=True,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._icon = ft.TextField(
            label="Icono",
            hint_text="restaurant",
            width=150,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._color = ft.TextField(
            label="Color",
            hint_text="#FF6B6B",
            width=120,
            border_color=AppTheme.BORDER_COLOR,
        )

        if is_edit:
            self._name.value = category.name
            self._icon.value = category.icon
            self._color.value = category.color

        content_controls = [
            self._name,
            ft.Row([self._icon, self._color], spacing=16),
        ]

        self._participants = participant_service.list_active()
        self._split_fields: dict[int, ft.TextField] = {}
        if is_edit and len(self._participants) >= 2:
            existing_splits = {
                s.participant_id: s.percentage for s in category_service.get_default_split(category.id)
            }
            for participant in self._participants:
                field = ft.TextField(
                    label=participant.name,
                    value=str(existing_splits.get(participant.id, "")),
                    suffix_text="%",
                    width=110,
                    border_color=AppTheme.BORDER_COLOR,
                )
                self._split_fields[participant.id] = field
            content_controls.append(
                ft.Column(
                    [
                        ft.Text("División por defecto (opcional)", size=12, color=AppTheme.TEXT_SECONDARY),
                        ft.Row(list(self._split_fields.values()), spacing=12, wrap=True),
                    ],
                    spacing=8,
                )
            )

        super().__init__(
            title=ft.Text("Editar Categoría" if is_edit else "Nueva Categoría"),
            content=ft.Column(
                content_controls,
                width=420,
                height=160 if not self._split_fields else 240,
                spacing=16,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close()),
                ft.FilledButton("Guardar", on_click=lambda e: self._save()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _save(self):
        try:
            if not self._name.value:
                show_snackbar(self._page,
                    ft.SnackBar(content=ft.Text("El nombre es requerido"), bgcolor=AppTheme.WARNING)
                )
                return
            data = CategoryCreate(
                name=self._name.value,
                icon=self._icon.value or "category",
                color=self._color.value or "#98A2FF",
            )
            if self._category:
                category_service.update(self._category.id, data)
                if self._split_fields:
                    splits = [
                        SplitEntry(participant_id=pid, percentage=Decimal(field.value))
                        for pid, field in self._split_fields.items()
                        if field.value and field.value.strip()
                    ]
                    category_service.set_default_split(self._category.id, splits)
            else:
                category_service.create(data)
            self._close()
            if self._on_saved:
                self._on_saved()
        except Exception as ex:
            show_snackbar(self._page,
                ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=AppTheme.ERROR)
            )

    def _close(self):
        self.open = False
        self.update()


class AccountDialog(ft.AlertDialog):
    """Dialog for creating/editing an account."""

    def __init__(self, page: ft.Page, on_saved, account=None):
        self._page = page
        self._on_saved = on_saved
        self._account = account
        is_edit = account is not None

        self._name = ft.TextField(
            label="Nombre",
            hint_text="Ej: Mi Cuenta Corriente",
            expand=True,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._type_dd = ft.Dropdown(
            label="Tipo",
            options=[
                ft.dropdown.Option("cash", "Efectivo"),
                ft.dropdown.Option("debit", "Débito"),
                ft.dropdown.Option("credit", "Crédito"),
            ],
            value="cash",
            width=200,
            border_color=AppTheme.BORDER_COLOR,
        )

        self._balance = ft.TextField(
            label="Balance inicial",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="0.00",
            prefix=ft.Text("$ "),
            width=150,
            border_color=AppTheme.BORDER_COLOR,
        )

        if is_edit:
            self._name.value = account.name
            self._type_dd.value = account.type
            self._balance.value = str(account.balance)

        super().__init__(
            title=ft.Text("Editar Cuenta" if is_edit else "Nueva Cuenta"),
            content=ft.Column(
                [
                    self._name,
                    ft.Row([self._type_dd, self._balance], spacing=16),
                ],
                width=400,
                height=160,
                spacing=16,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close()),
                ft.FilledButton("Guardar", on_click=lambda e: self._save()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _save(self):
        try:
            if not self._name.value:
                show_snackbar(self._page, 
                    ft.SnackBar(content=ft.Text("El nombre es requerido"), bgcolor=AppTheme.WARNING)
                )
                return
            data = AccountCreate(
                name=self._name.value,
                type=self._type_dd.value,
                balance=Decimal(self._balance.value or "0"),
            )
            if self._account:
                account_service.update(self._account.id, data)
            else:
                account_service.create(data)
            self._close()
            if self._on_saved:
                self._on_saved()
        except Exception as ex:
            show_snackbar(self._page, 
                ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=AppTheme.ERROR)
            )

    def _close(self):
        self.open = False
        self.update()
