# Finco — Estructura del Proyecto

```
Finco/
│
├── main.py                          # Entry point de la aplicación Flet
├── pyproject.toml                   # Configuración del proyecto, dependencias
├── requirements.txt                 # Pinned dependencies
├── .gitignore
├── .pre-commit-config.yaml
│
├── core/                            # Capa de datos y configuración
│   ├── __init__.py
│   ├── config.py                    # Configuración (paths, defaults)
│   ├── settings.py                  # User settings persistence (JSON)
│   ├── database.py                  # Engine WAL mode, SessionLocal, Base
│   ├── models.py                    # SQLAlchemy models (Account, Category, Transaction)
│   └── schemas.py                   # Pydantic schemas (validación entrada/salida)
│
├── services/                        # Lógica de negocio (toda async-safe)
│   ├── __init__.py
│   ├── transaction_service.py       # CRUD transacciones + soft-delete + undo
│   ├── category_service.py          # CRUD categorías, presupuestos
│   ├── account_service.py           # CRUD cuentas
│   ├── dashboard_service.py         # Consultas para el dashboard
│   ├── backup_service.py            # Backup/restore DB + JSON export
│   │
│   └── ocr/                         # Módulo OCR completo
│       ├── __init__.py
│       ├── ocr_service.py           # Orquestador (async, thread-safe)
│       ├── preprocessor.py          # OpenCV preprocessing pipeline
│       ├── onnx_engine.py           # ONNX Runtime + PP-OCRv6 (motor principal)
│       ├── pdf_converter.py         # pdf2image wrapper
│       ├── layout_analyzer.py       # Detección automática tabular vs columnar
│       │
│       ├── parsers/                 # Parsers por emisor (plugin pattern)
│       │   ├── __init__.py
│       │   ├── base.py              # BaseParser abstracto
│       │   ├── registry.py          # ParserRegistry
│       │   ├── visa.py              # Visa parser
│       │   ├── mastercard.py        # Mastercard parser
│       │   ├── amex.py              # Amex parser
│       │   └── fallback.py          # Parser genérico
│       │
│       └── models.py                # DataClasses: OCRResult, ExtractedField, ExtractedTransaction
│
├── ui/                              # Interfaz de usuario (Flet)
│   ├── __init__.py
│   ├── app.py                       # App principal, routing, theme, shortcuts
│   ├── theme.py                     # Colores, estilos dark mode + high contrast
│   │
│   ├── views/                       # Pantallas principales
│   │   ├── __init__.py
│   │   ├── dashboard_view.py        # Dashboard con resumen y gráficos
│   │   ├── transactions_view.py     # Lista de transacciones + filtros
│   │   ├── ocr_scan_view.py         # Escaneo OCR con preview
│   │   ├── categories_view.py       # CRUD categorías
│   │   └── accounts_view.py         # CRUD cuentas
│   │
│   └── components/                  # Componentes reutilizables
│       ├── __init__.py
│       ├── sidebar.py               # NavigationRail colapsable
│       ├── dialogs.py               # TransactionDialog, CategoryDialog, etc.
│       ├── data_table.py            # Tabla de transacciones reutilizable
│       ├── summary_cards.py         # Cards de resumen para dashboard
│       ├── charts.py                # Gráficos con fl_chart
│       ├── empty_state.py           # Empty state con icono + mensaje + acción
│       ├── loading_overlay.py       # Overlay con spinner + mensaje
│       ├── snack_undo.py            # SnackBar con acción "Deshacer"
│       ├── keyboard.py              # Sistema global de atajos de teclado
│       └── onboarding.py            # OnboardingWizard (5 pasos para primer uso)
│
├── utils/                           # Utilidades generales
│   ├── __init__.py
│   ├── threading.py                 # ThreadPoolExecutors globales
│   ├── helpers.py                   # format_currency, parse_date (fuzzy), parse_amount
│   └── constants.py                 # Constantes (colores, iconos, etc.)
│
├── assets/                          # Recursos estáticos
│   ├── icons/                       # Iconos personalizados
│   └── sample_receipts/             # Vouchers de prueba para desarrollo OCR
│
├── tests/                           # Tests
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures (DB en memoria, sample images)
│   │
│   ├── unit/                        # Tests unitarios
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_transaction_service.py
│   │   ├── test_category_service.py
│   │   └── test_ocr_parsers.py
│   │
│   └── integration/                 # Tests de integración
│       ├── __init__.py
│       ├── test_ocr_pipeline.py     # Image → OCRResult real
│       └── test_ui_flows.py         # Flujos completos
│
└── docs/                            # Documentación
    └── user_guide.md
```

## Convenciones

### Nombrado
- **Archivos**: `snake_case.py`
- **Clases**: `PascalCase`
- **Funciones/métodos**: `snake_case`
- **Variables**: `snake_case`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Modelos DB**: `PascalCase` (singular: `Transaction`, `Category`)

### Imports
```python
# Standard library
import os
from datetime import date, datetime
from decimal import Decimal

# Third-party
import flet as ft
from sqlalchemy import select, func
from onnxruntime import InferenceSession

# Local
from core.models import Transaction
from services.ocr.ocr_service import OCRService
```

### Estructura de vistas Flet
Cada vista es una función que recibe `page: ft.Page` y retorna `ft.Control`:
```python
def dashboard_view(page: ft.Page) -> ft.Control:
    ...
    return ft.Column([...])
```

### Patrón Async para servicios pesados
```python
class OCRService:
    async def process_image(self, path: str) -> OCRResult:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            OCR_EXECUTOR, self._process_sync, path
        )
        return result
```
