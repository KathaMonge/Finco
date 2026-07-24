# Finco — Contexto para Agentes y Desarrolladores

Este archivo contiene el contexto necesario para que cualquier agente de IA (o desarrollador) entienda el proyecto rápidamente y pueda contribuir sin fricción.

## Stack Resumido

```
Python 3.12+ | Flet 0.86.1 | PaddleOCR PP-OCRv6 | SQLite + SQLAlchemy 2.0
```

## Reglas de Oro (Actualizadas)

1. **Offline-first**: Todo debe funcionar sin internet. OCR incluido.
2. **CPU-only**: Sin dependencia de GPU. PaddleOCR en modo `use_gpu=False`.
3. **Windows target**: La app se empaqueta para Windows. Código multiplataforma pero el build target es Windows.
4. **Dark mode + High Contrast**: UI en tema oscuro con variante de alto contraste.
5. **SQLite con WAL mode**: `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;`
6. **Sin Alembic**: Schema versioning con `PRAGMA user_version`. `create_all()` para tablas.
7. **Bundle < 500MB**: Si PaddlePaddle lo excede, migrar a ONNX Runtime.
8. **Threading obligatorio**: OCR y procesos pesados en `asyncio.to_thread()`. NUNCA bloquear el event loop de Flet.
9. **Undo over Confirm**: Toda acción destructiva usa soft-delete + SnackBar con "Deshacer".
10. **Empty states siempre**: Toda vista sin datos muestra `EmptyState` con guía de acción.
11. **PDF support**: Los PDFs bancarios se convierten a imágenes con `pdf2image`.
12. **Layout analysis**: El texto OCR se ordena por columnas, no top-to-bottom naive.
13. **Repo público, datos reales en el pipeline**: Este proyecto procesa estados de cuenta y vouchers reales vía OCR. Ningún script de debug (`debug_*.py`) debe escribir su output (imágenes, JSON de resultados) al repo root — usa carpetas ignoradas (`.local/`, `tmp/`). Fixtures de test deben ser sintéticas, nunca capturas de un estado de cuenta real. Ver `CLAUDE.md` sección "Datos sensibles".

## Stack Detallado

| Componente | Elección | Alternativa si falla |
|---|---|---|
| UI | Flet 0.86.1 | — |
| OCR | PaddleOCR PP-OCRv6 | ONNX Runtime + PP-OCRv3 |
| DB | SQLite + SQLAlchemy 2.0 | — |
| PDF | pdf2image | PyMuPDF |
| Charts | Flet Charts (fl_chart) | — |
| Packaging | Flet build windows | PyInstaller + NSIS |
| Tests | pytest + pytest-asyncio | — |
| Linting | ruff | — |

## Lecciones Aprendidas (no repetir)

1. **Flet es Cliente-Servidor**: Corre un backend asyncio + frontend Flutter por WebSocket. Las operaciones CPU-bound (OCR, export) deben ir a threads.
2. **PaddlePaddle es grande**: ~180MB el wheel CPU. Bundle total estimado 500-700MB. Verificar temprano.
3. **Ordenamiento OCR naive falla**: Vouchers multicolumna necesitan layout analysis, no top-to-bottom.
4. **ConfirmDialog frustra usuarios**: Usar patrón undo con SnackBar.
5. **Alembic es overkill**: Para single-user SQLite, `create_all()` + schema version es suficiente.
6. **Flet ≥0.80 eliminó helpers de módulo**: `ft.padding.all()`, `ft.border.all()`, `ft.border_radius.only()` fueron reemplazados por métodos estáticos de clase: `ft.Padding.all()`, `ft.Border.all()`, `ft.BorderRadius.only()`. NO usar `ft.padding.*`, `ft.border.*`, `ft.border_radius.*`.
7. **Flet ≥0.80 cambió `ft.app()` por `ft.run()`**: Usar `ft.run(main)` no `ft.app(target=main)`.
8. **Flet ≥0.80 eliminó parámetros directos de `ft.Theme`**: `brightness`, `primary_color`, `on_primary`, `secondary_color`, `error_color`, `surface_tint_color` ya no existen en `Theme`. Usar `color_scheme=ft.ColorScheme(primary=..., on_primary=..., ...)`.
9. **SQLAlchemy 2.0+ requiere `text()`**: Toda SQL raw en `conn.execute()` debe envolverse con `text()`. Ej: `conn.execute(text("PRAGMA user_version"))`.
10. **Flet ≥0.86 cambió `SegmentedButton.selected`**: Ahora es `List[str]`, no `Set[str]`. Usar `selected=["expense"]` en vez de `selected={"expense"}`.
11. **Flet ≥0.80 `FilePicker` es un `Service`**: NO usar `page.overlay.append()`. NO usar `on_result` callback. `pick_files()` es `async` y retorna `list[FilePickerFile]` directamente. Ejemplo: `files = await ft.FilePicker().pick_files(allow_multiple=True)`.

## El Problema del OCR

Estamos construyendo un sistema OCR que debe funcionar con **múltiples emisores** de tarjetas (Visa, Mastercard, Amex, etc.), cada uno con su propio formato de voucher. Algunos son térmicos (texto claro), otros son PDF bancarios, otros son capturas de email.

### Estrategia: PaddleOCR + Layout Analysis + Parsers por Emisor

1. **PaddleOCR PP-OCRv6 Medium** (34.5M params, CPU, ~14MB)
2. **OpenCV preprocessing** para mejorar calidad de imagen
3. **Layout analysis** para ordenar texto por columnas
4. **Parsers por emisor** con regex
5. **Sistema de confianza**
6. **Corrección manual** en UI como respaldo

## Cómo Navegar el Proyecto

```
PLAN.md              → Visión general, decisiones, pre-mortem
ARCHITECTURE.md      → Arquitectura técnica, pipeline OCR, threading, UX
ROADMAP.md           → Timeline, sprints, milestones
PROJECT_STRUCTURE.md → Árbol de directorios, convenciones de código
```

## Tests

```bash
pytest tests/                    # Todos los tests
pytest tests/unit/               # Solo unitarios
pytest tests/integration/        # Solo integración
pytest -k "ocr"                  # Tests relacionados a OCR
```

## Comandos Principales

```bash
pip install -r requirements.txt    # Instalar dependencias
python main.py                     # Ejecutar app en modo desarrollo
flet build windows                 # Build producción (verificar tamaño)
pytest tests/                      # Correr tests
ruff check .                       # Linting
ruff format .                      # Formateo automático
```

## Para Agentes de IA

Cuando trabajes en este proyecto:

1. **Siempre lee PLAN.md primero** para entender en qué fase estamos y qué problemas evitamos.
2. **NUNCA bloquees el event loop de Flet** — usa `asyncio.to_thread()` para OCR y procesos pesados.
3. **Sigue el patrón UNDO** — soft-delete + SnackBar, no ConfirmDialog.
4. **Cada vista necesita un EmptyState** — si no hay datos, muestra una guía.
5. **No introduzcas dependencias nuevas** sin justificarlas en el plan.
6. **No uses GPU, no uses APIs externas**, todo debe funcionar offline.
7. **Los test deben correr sin internet**, sin GPU, sin configuración extra.
8. **WAL mode siempre** en la conexión SQLite. `check_same_thread=False`.
9. **Flet API — NO uses helpers de módulo**: `ft.padding.*`, `ft.border.*`, `ft.border_radius.*` NO existen. Usa `ft.Padding.*`, `ft.Border.*`, `ft.BorderRadius.*`.
10. **Flet API — `ft.Theme` sin colores directos**: Usa `ft.ColorScheme` dentro del parámetro `color_scheme=`. NO pases `brightness`, `primary_color`, etc.
11. **Flet API — `ft.run()` en vez de `ft.app()`**: El entry point usa `ft.run(main)`.
12. **SQLAlchemy 2.0 — `text()` obligatorio**: Cualquier SQL string crudo en `conn.execute()` debe ir con `text("...")`.
13. **Flet API — `SegmentedButton.selected` es `List[str]`**: NO usar `set`.
14. **Flet API — `FilePicker` es un `Service`**: NO usar `page.overlay.append()`. NO usar `on_result`. `pick_files()` es `async` y retorna archivos directamente.

## AI Context Block

```
PROJECT=Finco
STACK=python3.12,flet0.86.1,paddleocr,opencv,sqlalchemy2,sqlite,pdf2image
PLATFORM=windows-desktop
OCR_ENGINE=paddleocr-ppocrv6-medium
OCR_FALLBACK=onnx+ppocrv3
DB=sqlite-local-wal
UI_THEME=dark+highcontrast
OFFLINE=true
GPU_REQUIRED=false
UNDO_PATTERN=true
EMPTY_STATES=true
PDF_SUPPORT=true
THREADING_MANDATORY=true
SCHEMA_VERSIONING=pragma_user_version
PACKAGING=flet-build-windows|pyinstaller
BUNDLE_TARGET_MB=500
FLET_API_CLASS_METHODS=true  # ft.Padding.* ft.Border.* ft.BorderRadius.* (not ft.padding.*)
FLET_THEME_USES_COLORSCHEME=true  # ft.Theme(color_scheme=ft.ColorScheme(...))
SQLALCHEMY_TEXT_REQUIRED=true  # conn.execute(text("..."))
SEGMENTEDBUTTON_USES_LIST=true  # selected=["x"] not selected={"x"}
FILEPICKER_IS_SERVICE=true  # NO page.overlay.append(), NO on_result, use await pick_files() directly
SEGMENTEDBUTTON_USES_LIST=true  # selected=["x"] not selected={"x"}
```
