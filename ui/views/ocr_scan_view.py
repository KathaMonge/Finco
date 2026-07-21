from datetime import date
from decimal import Decimal

import flet as ft

from ui.components.empty_state import EmptyState
from ui.components.loading_overlay import LoadingOverlay
from ui.components.snack_undo import show_snackbar
from services.ocr.ocr_service import ocr_service
from services.transaction_service import transaction_service
from core.schemas import TransactionCreate
from ui.theme import AppTheme
from utils.constants import CONFIDENCE_COLORS


def ocr_scan_view(page: ft.Page) -> ft.Control:
    overlay = LoadingOverlay(message="Preparando OCR...")
    result_data = {"paths": [], "result": None}
    pending_files_text = ft.Text(
        "Ningún archivo seleccionado",
        size=13,
        color=AppTheme.TEXT_SECONDARY,
    )

    preview_image = ft.Image(
        src=None,
        width=400,
        height=300,
        fit=ft.BoxFit.CONTAIN,
        border_radius=8,
    )

    amount_field = ft.TextField(label="Monto", hint_text="0.00", prefix=ft.Text("$ "), border_color=AppTheme.BORDER_COLOR)
    date_field = ft.TextField(label="Fecha", hint_text="YYYY-MM-DD", border_color=AppTheme.BORDER_COLOR)
    merchant_field = ft.TextField(label="Comercio", hint_text="Nombre del comercio", expand=True, border_color=AppTheme.BORDER_COLOR)
    card_field = ft.TextField(label="Tarjeta (últimos 4)", hint_text="1234", border_color=AppTheme.BORDER_COLOR)

    confidence_text = ft.Text(size=12, color=AppTheme.TEXT_SECONDARY)
    emisor_text = ft.Text(size=14, weight=ft.FontWeight.W_600, color=AppTheme.PRIMARY)

    single_tx_form = ft.Column(spacing=8)
    multi_tx_section = ft.Column(spacing=8)
    multi_tx_container = ft.Column(spacing=4)
    tx_checkboxes: list[ft.Checkbox] = []

    file_picker = ft.FilePicker()

    def _reset_multi():
        tx_checkboxes.clear()
        multi_tx_container.controls.clear()

    def _build_multi_tx_list(result):
        _reset_multi()
        for i, tx in enumerate(result.transactions):
            desc_text = tx.description or f"Transacción {i+1}"
            cb = ft.Checkbox(
                label=f"${tx.amount:,.2f}  |  {tx.date.isoformat() if tx.date else '?'}  |  {desc_text}",
                value=True,
                width=600,
            )
            tx_checkboxes.append(cb)
            multi_tx_container.controls.append(
                ft.Container(
                    content=cb,
                    padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                    bgcolor=AppTheme.SURFACE_VARIANT if i % 2 == 0 else None,
                    border_radius=4,
                )
            )

    async def scan_image(_):
        if not result_data["paths"]:
            show_snackbar(page, 
                ft.SnackBar(content=ft.Text("Selecciona al menos un archivo primero"), bgcolor=AppTheme.WARNING)
            )
            return

        overlay.show("Escaneando voucher...")
        page.update()

        try:
            file_path = result_data["paths"][0]
            overlay.show("Procesando OCR...")
            page.update()

            result = await ocr_service.process(file_path)
            result_data["result"] = result

            emisor_text.value = f"Emisor: {result.emisor.upper()}"
            confidence_text.value = f"Confianza general: {result.overall_confidence:.0%}"

            if result.monto:
                amount_field.value = result.monto.value
            if result.fecha:
                date_field.value = result.fecha.value
            if result.comercio:
                merchant_field.value = result.comercio.value
            if result.tarjeta:
                card_field.value = result.tarjeta.value

            has_multi = len(result.transactions) > 1
            single_tx_form.visible = not has_multi
            multi_tx_section.visible = has_multi

            if has_multi:
                _build_multi_tx_list(result)

            show_snackbar(page, 
                ft.SnackBar(
                    content=ft.Text("OCR completado. Revisa los datos extraídos."),
                    bgcolor=AppTheme.SUCCESS,
                )
            )
        except Exception as ex:
            show_snackbar(page, 
                ft.SnackBar(content=ft.Text(f"Error en OCR: {ex}"), bgcolor=AppTheme.ERROR)
            )
        finally:
            overlay.hide()
            page.update()

    def save_transaction(_):
        result = result_data.get("result")
        if not result:
            show_snackbar(page, 
                ft.SnackBar(content=ft.Text("Primero escanea un voucher"), bgcolor=AppTheme.WARNING)
            )
            return

        raw_amount = amount_field.value.strip() if amount_field.value else ""
        if not raw_amount and result.monto:
            raw_amount = result.monto.value
        if not raw_amount:
            show_snackbar(page, 
                ft.SnackBar(content=ft.Text("Ingresa un monto válido"), bgcolor=AppTheme.WARNING)
            )
            return

        raw_date = date_field.value.strip() if date_field.value else ""
        if not raw_date and result.fecha:
            raw_date = result.fecha.value
        if not raw_date:
            show_snackbar(page, 
                ft.SnackBar(content=ft.Text("Ingresa una fecha válida"), bgcolor=AppTheme.WARNING)
            )
            return

        raw_desc = merchant_field.value.strip() if merchant_field.value else ""
        if not raw_desc and result.comercio:
            raw_desc = result.comercio.value
        if not raw_desc:
            raw_desc = "Voucher escaneado"

        try:
            from services.category_service import category_service
            from services.account_service import account_service

            categories = category_service.list_all()
            accounts = account_service.list_all()

            if not categories or not accounts:
                show_snackbar(page, 
                    ft.SnackBar(content=ft.Text("Necesitas al menos una categoría y una cuenta"), bgcolor=AppTheme.WARNING)
                )
                return

            data = TransactionCreate(
                account_id=accounts[0].id,
                category_id=categories[0].id,
                amount=Decimal(raw_amount.replace(",", ".")),
                date=raw_date,
                description=raw_desc,
                type="expense",
                ocr_confidence=result.overall_confidence,
            )
            transaction_service.create(data)
            show_snackbar(page, 
                ft.SnackBar(content=ft.Text("Transacción guardada"), bgcolor=AppTheme.SUCCESS)
            )
        except Exception as ex:
            show_snackbar(page, 
                ft.SnackBar(content=ft.Text(f"Error al guardar: {ex}"), bgcolor=AppTheme.ERROR)
            )

    def save_multiple_transactions(_):
        result = result_data.get("result")
        if not result or not result.transactions:
            return

        try:
            from services.category_service import category_service
            from services.account_service import account_service

            categories = category_service.list_all()
            accounts = account_service.list_all()
            if not categories or not accounts:
                show_snackbar(page,
                    ft.SnackBar(content=ft.Text("Necesitas al menos una categoría y una cuenta"), bgcolor=AppTheme.WARNING)
                )
                return

            saved = 0
            for i, tx in enumerate(result.transactions):
                if i < len(tx_checkboxes) and not tx_checkboxes[i].value:
                    continue
                desc = tx.description or f"Transacción {i+1}"
                data = TransactionCreate(
                    account_id=accounts[0].id,
                    category_id=categories[0].id,
                    amount=tx.amount,
                    date=tx.date.isoformat() if tx.date else date.today().isoformat(),
                    description=desc,
                    type="expense",
                    ocr_confidence=tx.confidence,
                )
                transaction_service.create(data)
                saved += 1

            show_snackbar(page,
                ft.SnackBar(content=ft.Text(f"{saved} transacciones guardadas"), bgcolor=AppTheme.SUCCESS)
            )
        except Exception as ex:
            show_snackbar(page,
                ft.SnackBar(content=ft.Text(f"Error al guardar: {ex}"), bgcolor=AppTheme.ERROR)
            )

    async def _pick_files(_):
        files = await file_picker.pick_files(
            allow_multiple=True,
            file_type=ft.FilePickerFileType.IMAGE,
        )
        if files and len(files) > 0:
            result_data["paths"] = [f.path for f in files]
            result_data["result"] = None
            first = files[0]
            preview_image.src = first.path
            preview_image.visible = True
            count = len(files)
            if count == 1:
                pending_files_text.value = f"1 archivo seleccionado: {first.name}"
            else:
                pending_files_text.value = f"{count} archivos seleccionados (se procesará el primero)"
            page.update()

    upload_area = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.UPLOAD_FILE, size=48, color=AppTheme.TEXT_SECONDARY),
                ft.Text("Arrastra una imagen o PDF aquí", size=16, color=AppTheme.TEXT_SECONDARY),
                pending_files_text,
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.FilledButton(
                            content="Seleccionar archivos",
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=_pick_files,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=AppTheme.CARD_COLOR,
        border=ft.Border.all(2, AppTheme.BORDER_COLOR),
        border_radius=12,
        padding=40,
        alignment=ft.Alignment(0, 0),
    )

    single_tx_form.controls = [
        amount_field,
        date_field,
        merchant_field,
        card_field,
        ft.Container(height=16),
        ft.Row(
            [
                ft.FilledButton(
                    content="Guardar Transacción",
                    icon=ft.Icons.SAVE,
                    on_click=save_transaction,
                ),
                ft.OutlinedButton(
                    content="Nuevo Escaneo",
                    on_click=lambda _: _reset(),
                ),
            ],
            spacing=8,
        ),
    ]

    multi_tx_section.controls = [
        ft.Text("Transacciones detectadas", size=16, weight=ft.FontWeight.W_600, color=AppTheme.ON_SURFACE),
        ft.Container(
            content=multi_tx_container,
            border=ft.Border.all(1, AppTheme.BORDER_COLOR),
            border_radius=8,
            padding=8,
            bgcolor=AppTheme.SURFACE,
        ),
        ft.Container(height=8),
        ft.Row(
            [
                ft.FilledButton(
                    content="Guardar Seleccionadas",
                    icon=ft.Icons.SAVE,
                    on_click=save_multiple_transactions,
                ),
                ft.OutlinedButton(
                    content="Nuevo Escaneo",
                    on_click=lambda _: _reset(),
                ),
            ],
            spacing=8,
        ),
    ]

    results_section = ft.Column(
        [
            ft.Container(height=24),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                emisor_text,
                                confidence_text,
                                ft.Container(height=16),
                                single_tx_form,
                                multi_tx_section,
                            ],
                            spacing=8,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=True,
                    ),
                    ft.Container(
                        content=preview_image,
                        width=400,
                        height=300,
                        bgcolor=AppTheme.SURFACE_VARIANT,
                        border_radius=8,
                        alignment=ft.Alignment(0, 0),
                    ),
                ],
                spacing=24,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        visible=False,
    )

    def _reset():
        results_section.visible = False
        upload_area.visible = True
        result_data["paths"] = []
        result_data["result"] = None
        pending_files_text.value = "Ningún archivo seleccionado"
        preview_image.src = None
        amount_field.value = ""
        date_field.value = ""
        merchant_field.value = ""
        card_field.value = ""
        _reset_multi()
        single_tx_form.visible = True
        multi_tx_section.visible = False
        page.update()

    main_content = ft.Stack(
        controls=[
            ft.Column(
                [
                    ft.Text("OCR Scan", size=22, weight=ft.FontWeight.BOLD, color=AppTheme.ON_BACKGROUND),
                    ft.Container(height=16),
                    ft.Text(
                        "Escanea vouchers de tarjeta y extrae datos automáticamente. "
                        "Soporta imágenes y PDFs.",
                        size=14,
                        color=AppTheme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=24),
                    upload_area,
                    results_section,
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            overlay,
        ],
        expand=True,
    )

    async def _on_scan(_):
        if result_data["paths"]:
            upload_area.visible = False
            results_section.visible = True
            page.update()
        await scan_image(_)

    scan_btn = ft.FilledButton(
        content="Escanear",
        icon=ft.Icons.DOCUMENT_SCANNER,
        on_click=_on_scan,
    )

    main_content.controls[0].controls.insert(3, scan_btn)

    return main_content
