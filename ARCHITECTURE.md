# Finco — Arquitectura Técnica

## 1. Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                     Flet Client (Flutter Engine)                  │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Dashboard│  │  Transac │  │ OCR Scan│  │  Cat/Acc │  ...     │
│  │  View   │  │tions View│  │   View  │  │  Views   │         │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │             │             │                │
│  ┌────┴─────────────┴─────────────┴─────────────┴────┐          │
│  │            Componentes Reutilizables               │          │
│  │  Sidebar, Charts, Dialogs, Table, EmptyState,     │          │
│  │  LoadingOverlay, OnboardingWizard, SnackUndo      │          │
│  └───────────────────────┬───────────────────────────┘          │
└──────────────────────────┼──────────────────────────────────────┘
                           │ WebSocket (localhost)
┌──────────────────────────┼──────────────────────────────────────┐
│               Flet Backend (Python asyncio)                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                     Event Loop (asyncio)                    │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │ │
│  │  │ UI Handlers  │  │   Services   │  │  ThreadPool      │  │ │
│  │  │ (async)      │  │   (async)    │  │  Executor        │  │ │
│  │  └──────┬───────┘  └──────┬───────┘  │  - OCR pesado    │  │ │
│  │         │                  │          │  - Export CSV    │  │ │
│  │         │                  │          │  - Backup DB     │  │ │
│  │         │                  │          └──────────────────┘  │ │
│  └─────────┼──────────────────┼────────────────────────────────┘ │
└────────────┼──────────────────┼──────────────────────────────────┘
             │                  │
             ▼                  ▼
   ┌─────────────────────────────────────────────┐
   │          SQLite (WAL mode)                   │
    │  finco.db  ←  {user_data_dir}/Finco/   │
   └─────────────────────────────────────────────┘
                          ▲
                          │
   ┌──────────────────────┴──────────────────────────┐
   │              External Tools (bundleados)         │
   │  ┌──────────────┐  ┌──────────┐  ┌───────────┐  │
   │  │ PaddleOCR     │  │  OpenCV  │  │ pdf2image │  │
   │  │ (o ONNX RT)   │  │ preproc  │  │ PDF→img   │  │
   │  └──────────────┘  └──────────┘  └───────────┘  │
   └─────────────────────────────────────────────────┘
```

## 2. Pipeline OCR Detallado

### 2.1 Preprocesamiento de Entrada

```
Archivo de entrada
    │
    ├── Si es PDF (.pdf)
    │      └── pdf2image.convert_from_path(pdf, dpi=300)
    │           └── Lista de imágenes PIL
    │
    └── Si es imagen (.jpg/.png/.bmp)
           └── PIL.Image.open(path)
```

### 2.2 Preprocesamiento (OpenCV)

```
Imagen original (RGB)
    │
    ├─ 1. Convertir a escala de grises
    │      gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    │
    ├─ 2. Denoising (reducir ruido del sensor/compresión)
    │      denoised = cv2.fastNlMeansDenoising(gray)
    │
    ├─ 3. Enderezado (deskew) — detectar ángulo de rotación
    │      coords = np.column_stack(np.where(denoised > 0))
    │      angle = cv2.minAreaRect(coords)[-1]
    │      deskewed = rotate(denoised, angle)
    │
    ├─ 4. Adaptive Threshold — binarizar para OCR
    │      thresh = cv2.adaptiveThreshold(
    │          deskewed, 255, ADAPTIVE_THRESH_GAUSSIAN_C,
    │          THRESH_BINARY, 31, 2
    │      )
    │
    └─ 5. Redimensionar manteniendo aspect ratio
         resized = resize_to_max_height(thresh, 1200)
```

### 2.3 OCR Engine

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,   # clasificador de orientación
    lang="en",            # inglés (suficiente para vouchers)
    use_gpu=False,        # CPU-only
    show_log=False,
    det_db_thresh=0.3,    # umbral detección
    rec_batch_num=6,      # batch recognition
)
```

**Output**: Lista de `(bbox, text, confidence)` donde:
- `bbox`: [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] — coordenadas del texto
- `text`: string reconocido
- `confidence`: float 0-1

### 2.4 Post-Processing con Layout Analysis

El raw output de PaddleOCR necesita ordenamiento inteligente. No es seguro confiar solo en coordenada Y (top-to-bottom) porque los vouchers tienen layouts multicolumna.

```
Algoritmo de Layout Analysis:

1. Agrupar textos por proximidad horizontal (misma línea)
   - Si |y1_i - y1_j| < threshold → misma línea
   - Ordenar por x1 dentro de cada línea

2. Detectar columnas (si aplica):
   - Calcular histograma de posiciones X de los textos
   - Si hay 2+ clusters de X → hay múltiples columnas
   - Procesar columna izquierda primero, luego derecha

3. Orden final: columna → línea → izquierda a derecha

4. Heurísticas específicas de voucher:
   - Montos suelen estar alineados a la derecha
   - Fechas suelen estar cerca del borde superior
   - Nombre de comercio suele ser la línea más grande
```

### 2.5 Detección de Emisor y Parsing

```python
EMISOR_PATTERNS = {
    "visa": {
        "detect": [r"VIS[AÁ]", r"Cr[eé]dito\s+Visa", r"Titular:\s*\w+"],
        "amount":   r"(?:TOTAL|CONSUMO|PAGO)\s*:?\s*\$?\s*([\d.,]+)",
        "date":     r"(?:FECHA|EMISI[OÓ]N)\s*:?\s*(\d{2}[/-]\d{2}[/-]\d{2,4})",
        "merchant": r"(?:COMERCIO|ESTABLECIMIENTO|PROVEEDOR)\s*:?\s*(.+)",
        "card":     r"(?:TARJETA|NRO|N[UÜ]MERO)\s*:?\s*[\*X]?(\d{4})",
    },
    "mastercard": {
        "detect": [r"MASTER", r"Mastercard"],
    },
    "amex": {
        "detect": [r"AMEX", r"American\s+Express"],
    },
    "fallback": {
        # parser genérico basado en patrones universales
        # detecta múltiples transacciones por línea (fecha + descripción + monto)
    }
```

El parser fallback (`services/ocr/parsers/fallback.py`) incluye un patrón `LINE_TX_PATTERN`
que detecta líneas individuales con formato `fecha + descripción + monto`, típico de
estados de cuenta bancarios. Cada línea detectada se convierte en un
`ExtractedTransaction` dentro de `OCRResult.transactions`, permitiendo el guardado
batch de múltiples transacciones desde una sola imagen.
```

### 2.6 Sistema de Confianza

```python
@dataclass
class ExtractedField:
    value: str
    confidence: float  # 0.0 - 1.0
    raw_text: str
    method: str         # "exact_regex", "fuzzy", "manual"

@dataclass
class ExtractedTransaction:
    """Una transacción individual detectada (ej: una fila de estado de cuenta)."""
    amount: Decimal
    date: date | None
    description: str
    confidence: float
    raw_text: str

@dataclass
class OCRResult:
    emisor: str
    monto: ExtractedField | None
    fecha: ExtractedField | None
    comercio: ExtractedField | None
    tarjeta: ExtractedField | None
    items: list[ExtractedField]
    transactions: list[ExtractedTransaction]  # múltiples transacciones de un estado de cuenta
    raw_lines: list[str]
    overall_confidence: float
```

Si `overall_confidence < 0.7`, la UI muestra advertencia pidiendo revisión manual.

Si `len(transactions) > 1`, la UI cambia a modo "batch" mostrando una lista seleccionable en lugar del formulario individual, permitiendo guardar múltiples transacciones de una sola imagen.

## 3. Modelo de Datos (SQLAlchemy)

```python
class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20))   # "cash", "debit", "credit"
    balance: Mapped[Decimal] = mapped_column(Decimal(12, 2), default=0)
    icon: Mapped[str] = mapped_column(String(50), default="credit_card")
    created_at: Mapped[datetime] = mapped_column(default=func.now())

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    icon: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(7))
    monthly_budget: Mapped[Decimal | None] = mapped_column(Decimal(12, 2), nullable=True)
    is_system: Mapped[bool] = mapped_column(default=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    amount: Mapped[Decimal] = mapped_column(Decimal(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="ARS")  # ← NUEVO
    date: Mapped[date]
    description: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(10))      # "income" | "expense"
    receipt_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ocr_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)  # ← Soft-delete para UNDO
```

### Soft-Delete para Undo

En lugar de DELETE físico, se usa `deleted_at IS NULL` para filtrar. El "undo" simplemente pone `deleted_at = None`.

### Diagrama ER

```
┌──────────┐       ┌──────────────┐       ┌─────────────┐
│  Account  │       │ Transaction  │       │  Category   │
├──────────┤       ├──────────────┤       ├─────────────┤
│ id (PK)  │──┐    │ id (PK)      │    ┌──│ id (PK)     │
│ name     │  │    │ account_id   │────┘  │ name        │
│ type     │  └───>│ category_id  │───────│ icon        │
│ balance  │       │ amount       │       │ color       │
│ icon     │       │ currency     │       │ budget      │
│ created  │       │ date         │       │ is_system   │
└──────────┘       │ description  │       └─────────────┘
                   │ type         │
                   │ receipt_img  │
                   │ ocr_data     │
                   │ ocr_conf     │
                   │ deleted_at   │
                   │ created_at   │
                   └──────────────┘
```

## 4. Configuración de SQLite

```python
from sqlalchemy import create_engine, event

engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()
```

## 5. Threading Model (crítico para OCR)

Flet corre un event loop asyncio. Todas las operaciones pesadas deben ir a thread separado:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Pool global de threads (CPU-bound tasks)
_ocr_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ocr")

# Pool global para I/O bound
_io_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="io")

class OCRService:
    async def process_image(self, path: str) -> OCRResult:
        loop = asyncio.get_event_loop()
        # Esto NO bloquea el event loop de Flet
        result = await loop.run_in_executor(
            _ocr_executor,
            self._process_sync,
            path
        )
        return result

    def _process_sync(self, path: str) -> OCRResult:
        # OCR pesado aquí (síncrono, pero en thread aparte)
        image = preprocess(path)
        raw = self.engine.run(image)
        return self.parse(raw)
```

### Loading States

Mientras OCR corre, la UI muestra `LoadingOverlay`. Cada vista tiene:

```python
class LoadingOverlay(ft.Stack):
    """Overlay semitransparente con spinner + mensaje."""
    def __init__(self, message: str = "Procesando..."):
        self.message = message
        # ...
```

## 6. UI Component Tree (Flet)

```
App
├── Theme (dark mode + high contrast variant)
├── Page (full window)
│   ├── Row
│   │   ├── NavigationRail (sidebar colapsable)
│   │   │   ├── NavItem("Dashboard", icon=HOME, shortcut=Ctrl+1)
│   │   │   ├── NavItem("Transacciones", icon=LIST, shortcut=Ctrl+2)
│   │   │   ├── NavItem("OCR Scan", icon=CAMERA, shortcut=Ctrl+3)
│   │   │   ├── NavItem("Categorías", icon=TAG, shortcut=Ctrl+4)
│   │   │   └── NavItem("Cuentas", icon=ACCOUNT_BALANCE, shortcut=Ctrl+5)
│   │   │
│   │   └── Container (content area)
│   │       ├── DashboardView
│   │       │   ├── SummaryCards (balance, gastos mes, ingresos)
│   │       │   ├── Chart (gastos por categoría — pie/donut)
│   │       │   ├── RecentTransactions (últimas 5)
│   │       │   └── EmptyState (si no hay datos)
│   │       │
│   │       ├── TransactionsView
│   │       │   ├── FilterBar (Ctrl+F)
│   │       │   ├── DataTable
│   │       │   ├── EmptyState (si no hay transacciones)
│   │       │   └── FAB ➕ (Ctrl+N)
│   │       │
│   │       ├── OCRScanView
│   │       │   ├── UploadArea (drag & drop / file picker)
│   │       │   ├── ImagePreview (thumbnail)
│   │       │   ├── LoadingOverlay (mientras procesa)
│   │       │   ├── ExtractedDataForm (campos editables)
│   │       │   └── ActionButtons (guardar / cancelar)
│   │       │
│   │       ├── CategoriesView
│   │       │   ├── ListView
│   │       │   ├── EmptyState
│   │       │   └── FAB ➕
│   │       │
│   │       └── AccountsView
│   │           ├── CardsRow
│   │           ├── EmptyState
│   │           └── FAB ➕
│   │
│   ├── Dialogs
│   │   ├── TransactionDialog (crear/editar)
│   │   ├── CategoryDialog
│   │   ├── AccountDialog
│   │   └── ConfirmDialog (solo para acciones irreversibles)
│   │
│   ├── SnackBar (undo actions vía SnackBar)
│   └── OnboardingWizard (solo si primer uso)
```

## 7. Flujo de Datos — OCR Scan

```
Usuario: click "OCR Scan" → UploadArea
    │
    ├─ FilePicker: selecciona imagen o PDF
    │
    ├─ [Si es PDF] → pdf2image → lista de imágenes
    │
    ├─ ImagePreview: muestra thumbnail
    │
    ├─ Click "Escanear"
    │   ├─ UI: muestra LoadingOverlay("Escaneando voucher...")
    │   ├─ Backend: ocr_service.process_image(path) [en thread]
    │   │   ├─ 1. Load image (Pillow)
    │   │   ├─ 2. Preprocess (OpenCV)
    │   │   ├─ 3. Run PaddleOCR
    │   │   ├─ 4. Layout analysis (ordenar por columnas)
    │   │   ├─ 5. Detect emisor (pattern matching)
    │   │   ├─ 6. Apply parser
    │   │   └─ 7. Return OCRResult
    │   └─ UI: oculta LoadingOverlay, muestra resultados
    │
    ├─ ExtractedDataForm: muestra campos extraídos
    │   ├─ monto:     [______]  ✓ confianza 0.95
    │   ├─ fecha:     [______]  ⚠ confianza 0.60
    │   ├─ comercio:  [______]  ✓ confianza 0.98
    │   └─ tarjeta:   [______]  ✓ confianza 0.90
    │
    ├─ Usuario: revisa y corrige campos
    │
    └─ Click "Guardar" → transaction_service.create(data)
         ├─ Crea Transaction en DB
         ├─ SnackBar("Transacción guardada")
         └─ Actualiza Dashboard
```

## 8. Manejo de Imágenes

```
{user_data_dir}/Finco/receipts/
    └── {transaction_id}_{timestamp}.{ext}
```

La ruta se guarda en `Transaction.receipt_image`. Las imágenes originales se conservan para re-escaneo futuro.

## 9. Estrategia Multi-Emisor

### 9.1 Registro de Parsers (Plugin Pattern)

```python
@ParserRegistry.register("visa")
class VisaParser(BaseParser):
    def detect(self, lines: list[str]) -> bool: ...
    def parse(self, lines: list[str]) -> OCRResult: ...
```

### 9.2 Pipeline de detección

```python
def detect_emisor(lines: list[str]) -> str:
    for emisor, parser_cls in ParserRegistry._parsers.items():
        if parser_cls().detect(lines):
            return emisor
    return "fallback"
```

## 10. Keyboard Shortcuts

Sistema global de atajos registrado en `ui/components/keyboard.py`:

| Atajo | Acción |
|-------|--------|
| Ctrl+1-5 | Navegación entre vistas |
| Ctrl+N | Nueva transacción |
| Ctrl+F | Enfocar búsqueda |
| Ctrl+E | Exportar CSV |
| Ctrl+B | Backup DB |
| Delete | Eliminar selección (con undo) |
| Escape | Cerrar diálogo / overlay |

## 11. Backup & Restore

```python
class BackupService:
    def export(self, path: str) -> str:       # Copia .db a destino
    def import_backup(self, path: str) -> None # Restaura .db
    def export_json(self, path: str) -> str:   # Exporta todo a JSON
```

## 12. Patrón Undo

Todas las operaciones destructivas usan soft-delete + SnackBar:

```python
def delete_transaction(self, tx_id: int) -> Transaction:
    tx = session.get(Transaction, tx_id)
    tx.deleted_at = datetime.now()
    session.commit()
    return tx

def restore_transaction(self, tx_id: int) -> Transaction:
    tx = session.get(Transaction, tx_id)
    tx.deleted_at = None
    session.commit()
    return tx
```

## 13. Onboarding Flow

```
Primer inicio → detectar si hay transacciones
    ├── Si hay datos → Dashboard normal
    └── Si no hay datos → OnboardingWizard
        ├── Paso 1: "Bienvenido" (qué hace la app)
        ├── Paso 2: Crear primera cuenta (efectivo/débito/crédito)
        ├── Paso 3: Crear categorías iniciales (predefinidas)
        ├── Paso 4: Registrar primer gasto (opcional)
        └── Paso 5: "¡Listo!" → Dashboard con datos
```
