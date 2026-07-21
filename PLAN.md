# Finco — Plan de Desarrollo

## Visión General

**Finco** (Finanzas Compartidas) — Aplicación de escritorio Windows para gestión de gastos compartidos con enfoque en tracking de gastos, escaneo OCR de vouchers de tarjeta, y dashboard visual. Construida con Python Flet + PaddleOCR.

## Lecciones Aprendidas (Pre-Mortem)

> Problemas identificados durante la revisión del plan inicial que han sido corregidos:

| # | Problema | Corrección Aplicada |
|---|----------|---------------------|
| 1 | Bundle size estimado en 300MB pero PaddlePaddle + Flet + Python da ~700MB | Meta actualizada a 500MB. ONNX Runtime como alternativa si excede |
| 2 | Flet es Cliente-Servidor local (WebSocket), no app desktop nativa | Documentado en arquitectura. Threading obligatorio para no bloquear UI |
| 3 | OCR bloquea el event loop de Flet (sin threading) | `asyncio.to_thread()` + `ProgressBar` desde el día 1 |
| 4 | No hay soporte para PDFs bancarios | `pdf2image` añadido al stack OCR |
| 5 | Ordenamiento top-to-bottom naive en OCR | Algoritmo de layout analysis por columnas |
| 6 | Sin empty states ni onboarding | Componentes `EmptyState` y `OnboardingWizard` |
| 7 | Sin atajos de teclado | Sistema de keyboard shortcuts en `ui/components/keyboard.py` |
| 8 | Confirmaciones modales molestas | Patrón **undo** (acción inmediata + SnackBar con "Deshacer") |
| 9 | Sin campo currency en Transaction | `currency` con default "ARS" agregado al modelo |
| 10 | Alembic es overkill para single-user | `Base.metadata.create_all()` + tabla `_schema_version` |
| 11 | SQLite sin WAL mode | `PRAGMA journal_mode=WAL` en connection setup |
| 12 | Sin backup/restore de DB | `BackupService` exporta/importa `.db` + `.json` |

## Requerimientos

### Funcionales

| ID | Requerimiento | Prioridad | Fase |
|---|---|---|---|
| RF-01 | Registro manual de gastos (monto, fecha, categoría, descripción) | Alta | 1 |
| RF-02 | CRUD de categorías (personalizables por el usuario) | Alta | 1 |
| RF-03 | Dashboard con resumen mensual (ingresos vs gastos) | Alta | 1 |
| RF-04 | Escaneo OCR de vouchers de tarjeta (múltiples emisores) | Alta | 2 |
| RF-05 | Previsualización y corrección manual de datos extraídos por OCR | Alta | 2 |
| RF-06 | Dashboard con gráficos interactivos (gastos por categoría, evolución) | Media | 2 |
| RF-07 | Exportación de datos a CSV | Media | 3 |
| RF-08 | Presupuestos mensuales por categoría con alertas | Media | 3 |
| RF-09 | Búsqueda y filtros avanzados de transacciones | Baja | 3 |
| RF-10 | Multi-cuenta (efectivo, débito, crédito) | Media | 1 |
| RF-11 | Escaneo de PDFs bancarios (conversión automática a imagen) | Alta | 2 |
| RF-12 | Backup y restauración de base de datos | Media | 1 |
| RF-13 | Atajos de teclado para acciones principales | Baja | 1 |
| RF-14 | Onboarding para nuevo usuario (guía inicial) | Baja | 1 |

### No Funcionales

| ID | Requerimiento | Prioridad |
|---|---|---|
| RNF-01 | Aplicación offline-first (sin dependencia de internet) | Alta |
| RNF-02 | Ejecutable Windows standalone (bundleado) | Alta |
| RNF-03 | OCR funcional en CPU, sin GPU requerida | Alta |
| RNF-04 | Tema oscuro (dark mode) como default | Alta |
| RNF-05 | Base de datos SQLite local, cero configuración | Alta |
| RNF-06 | Tiempo de respuesta en OCR < 8s en CPU moderna (meta realista) | Media |
| RNF-07 | Bundle final < 500MB (meta realista) | Media |
| RNF-08 | UI nunca se congela (OCR y procesos pesados en thread separado) | Alta |
| RNF-09 | Acciones destructivas tienen undo en lugar de confirmación modal | Media |
| RNF-10 | Estados vacíos visibles en todas las pantallas con guías de acción | Media |

## Stack Tecnológico

| Componente | Tecnología | Razón |
|---|---|---|
| UI Framework | Python Flet (≥ 0.26) | Material Design, dark mode nativo, desktop Windows |
| OCR Engine | PaddleOCR PP-OCRv6 Medium | 34.5M params, CPU, 50 idiomas, precisión SOTA |
| OCR Alternativa (si bundle excede) | ONNX Runtime + PP-OCRv3 | ~40MB vs ~200MB de PaddlePaddle |
| Image Processing | OpenCV + Pillow | Preprocessing, deskew, thresholding |
| PDF Conversion | pdf2image | Convierte PDF bancarios a imágenes para OCR |
| Base de Datos | SQLite + SQLAlchemy 2.0 | Zero config, ACID, embebida |
| ORM | SQLAlchemy 2.0 (sin Alembic) | `create_all()` + tabla `_schema_version` |
| Charts | Flet Charts (fl_chart) | Nativo Flet, Material Design consistente |
| Packaging | Flet build windows + verificación PyInstaller fallback | Flutter-based producción |
| Testing | pytest | Estándar Python |
| Linting | ruff | Rápido, moderno, reemplaza flake8/isort |

### Dependencias Principales

```txt
flet>=0.26.0
paddleocr>=2.8.0
paddlepaddle>=2.6.0 (CPU version)
opencv-python>=4.9.0
pillow>=10.0.0
pdf2image>=1.17.0
sqlalchemy>=2.0
pydantic>=2.0
python-dateutil>=2.8
ruff
pytest
pytest-asyncio
```

### Packaging Strategy (Verificación Temprana)

**Sprint 0 bloqueante**: Antes de escribir UI, verificar que el bundle es viable:

1. Probar `flet build windows` con PaddlePaddle → medir tamaño
2. Si > 500MB o falla: migrar a ONNX Runtime + PP-OCRv3
3. Alternativa: PyInstaller + NSIS para más control

## Fases de Desarrollo

### Fase 0 — Verificación Técnica (NUEVA)
**Objetivo**: Probar que el stack elegido funciona antes de invertir en UI.

- [ ] Crear PoC de build: `flet build windows` con PaddlePaddle
- [ ] Medir tamaño del bundle resultante
- [ ] Si falla o excede 500MB: probar ONNX Runtime
- [ ] Probar OCR en CPU midiendo tiempo real
- [ ] Decidir stack final y documentar en TECH_DECISIONS.md

### Fase 1 — Fundación (MVP-1)
**Objetivo**: Aplicación funcional con registro manual, categorías, dashboard básico.

- [ ] Inicializar proyecto con estructura modular
- [ ] Configurar base de datos SQLite + modelos (Transaction, Category, Account)
  - [ ] WAL mode activado por defecto
  - [ ] Campo currency en Transaction (default "ARS")
- [ ] Implementar UI base con navegación lateral (Flet)
- [ ] Sistema de ruteo entre vistas con animaciones
- [ ] Pantalla de Dashboard con resumen del mes + empty state
- [ ] Pantalla de Transacciones (lista + registro manual)
  - [ ] Patrón UNDO en eliminaciones
  - [ ] Atajos de teclado: Ctrl+N nueva, Ctrl+F buscar
- [ ] Pantalla de Categorías (CRUD)
- [ ] Pantalla de Cuentas (CRUD)
- [ ] Componente OnboardingWizard para primer uso
- [ ] Tema oscuro global con variante de alto contraste
- [ ] Pruebas unitarias de modelos y servicios
- [ ] BackupService (exportar/importar DB)

### Fase 2 — OCR Inteligente (MVP-2)
**Objetivo**: Escaneo de vouchers con extracción automática de datos.

- [ ] Integrar PaddleOCR en `services/ocr_service.py`
  - [ ] Ejecutar en `asyncio.to_thread()` para no bloquear UI
  - [ ] LoadingOverlay con progreso indeterminado
- [ ] Implementar preprocessing OpenCV (deskew, threshold, crop)
- [ ] Convertidor PDF → imagen (pdf2image)
- [ ] Pipeline de detección de emisor por patrones
- [ ] Parsers específicos por emisor (Visa, Mastercard, Amex, genérico)
  - [ ] Layout analysis: ordenamiento por columnas, no top-to-bottom
- [ ] Parser fallback genérico para emisores desconocidos
- [ ] Sistema de confianza por campo extraído
- [ ] Pantalla de escaneo OCR con selector de archivos (imagen + PDF)
- [ ] Vista previa de datos extraídos + corrección manual
- [ ] Guardado de transacción desde OCR

### Fase 3 — Reportes y UX (Refinamiento)
**Objetivo**: Dashboard avanzado, presupuestos, exportación.

- [ ] Dashboard con gráficos (gastos por categoría, evolución mensual)
- [ ] Presupuestos mensuales por categoría
- [ ] Alertas visuales de sobrepaso de presupuesto
- [ ] Exportación a CSV/Excel
- [ ] Búsqueda y filtros (fecha, categoría, monto, texto)
- [ ] Mejoras de UX (animaciones, tooltips, atajos)
- [ ] Testing E2E de flujos principales
- [ ] Build de producción (flet build windows o PyInstaller)

## Decisiones Técnicas Clave

### OCR: PaddleOCR > Tesseract (con backup ONNX)

| Aspecto | PaddleOCR PP-OCRv6 | Tesseract 5 | ONNX + PP-OCRv3 |
|---|---|---|---|
| Precisión general | 96.3% (OmniDocBench) | ~85-90% | ~94% |
| CPU Performance | 5.2× más rápido con OpenVINO | Aceptable | ~3× más rápido que Paddle |
| Bundle size | Modelo ~14MB + PaddlePaddle ~180MB | ~50MB + tessdata | Modelo ~15MB + ONNX ~30MB |
| Bundle Total Estimado | ~500-700MB | ~200-300MB | ~300-400MB |
| Mantenimiento | Activo (2026) | Legacy | Activo |

### SQLite con WAL mode

Para app desktop personal con operaciones concurrentes (lectura UI + escritura OCR):

```python
engine = create_engine(
    "sqlite:///finco.db",
    connect_args={"check_same_thread": False}
)
# Al conectar: PRAGMA journal_mode=WAL;
# Al conectar: PRAGMA busy_timeout=5000;
```

### Sin Alembic: Schema versioning simple

```python
SCHEMA_VERSION = 1

def check_schema(conn):
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        # crear tablas
        Base.metadata.create_all(bind=conn)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
```

### Patrón Undo en lugar de Confirmación Modal

```python
def delete_transaction(tx_id):
    tx = transaction_service.delete(tx_id)
    page.show_snack_bar(
        SnackBar(
            content=Text("Transacción eliminada"),
            action="Deshacer",
            on_action=lambda e: transaction_service.restore(tx)
        )
    )
```

### Threading para OCR

```python
import asyncio

async def process_image(path):
    loop = asyncio.get_event_loop()
    # OCR corre en thread separado, UI no se congela
    result = await loop.run_in_executor(
        None, ocr_engine.process, path
    )
    return result
```

### Arquitectura Modular

```
Finco/
├── main.py              # Entry point
├── core/                # DB, config, models, settings
├── ui/                  # Flet views & components
├── services/            # Business logic
├── utils/               # Helpers
└── assets/              # Resources
```

Separación clara de capas permite:
- Testear lógica sin UI
- Cambiar de OCR engine sin tocar UI
- Reutilizar servicios en otros contextos (CLI, web)
