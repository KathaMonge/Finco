# Finco — Roadmap de Desarrollo

> Timeline tentativo. Cada fase produce un entregable funcional y testeable.

## Fase 0 — Verificación Técnica (RESUELTA)
**Objetivo**: Probar que el stack es viable ANTES de invertir en build de producción.
**Duración**: 1-2 días

> ✅ Decisión tomada: ONNX Runtime + PP-OCRv6 como motor OCR (PaddlePaddle excedía bundle size).
> ✅ OCR funcional en CPU con ONNX Runtime. Pendiente: verificar bundle size final en build producción.

- [x] Crear script de prueba: inicializar OCR + procesar 1 imagen
- [x] Medir tiempo de OCR en CPU (target: < 8s) — ✅ ONNX más rápido que PaddlePaddle
- [x] Decidir stack final: ONNX Runtime + PP-OCRv6 (documentado en CONTEXT.md)
- [ ] Probar `flet build windows` con ONNX incluido
- [ ] Medir tamaño del bundle resultante
- [ ] Verificar en máquina limpia (sin Python)

## Fase 1 — Fundación (MVP-1) ✅ COMPLETADA
**Objetivo**: App funcional con registro manual y dashboard básico.
**Duración**: Sprints 1.1 - 1.4

> Todo el código de Fase 1 está escrito y funcional.

### Sprint 1.1 — Setup e Infraestructura ✅
- [x] Inicializar proyecto Python (pyproject.toml, requirements.txt)
- [x] Configurar ruff, pytest, pre-commit, pytest-asyncio
- [x] Crear estructura de directorios
- [x] Setup base de datos SQLite + SQLAlchemy
  - [x] WAL mode + busy_timeout + foreign_keys
  - [x] Schema versioning con PRAGMA user_version (sin Alembic)
- [x] Escribir modelos (Account, Category, Transaction)
  - [x] Campo currency en Transaction (default "ARS")
  - [x] Soft-delete (deleted_at) para patrón UNDO
- [x] Escribir schemas Pydantic de validación

### Sprint 1.2 — Core de UI + UX Foundations ✅
- [x] Entry point `main.py` con tema oscuro + variante alto contraste
- [x] NavigationRail (sidebar) colapsable con todas las secciones
- [x] Sistema de ruteo entre vistas (sin animaciones aún — pendiente UX)
- [x] Keyboard shortcuts globales (Ctrl+1-5 navegación, Ctrl+N, Ctrl+F)
- [x] Componente EmptyState (para todas las vistas)
- [x] Componente LoadingOverlay (spinner + mensaje)
- [x] Componente SnackBar con acción "Deshacer"
- [x] Componente OnboardingWizard (5 pasos)

### Sprint 1.3 — Funcionalidades Base ✅
- [x] CRUD de Categorías
- [x] CRUD de Cuentas
- [x] Registro manual de Transacciones
- [x] Listado de Transacciones con ordenamiento
- [x] Dashboard con resumen del mes (cards + empty state)
- [x] Patrón UNDO en eliminaciones
- [x] Tests unitarios de servicios

### Sprint 1.4 — Pulido Fase 1 ✅
- [x] Validaciones de formularios (Pydantic en backend + UI inline)
- [x] OnboardingWizard funcional
- [x] BackupService (exportar/importar DB y JSON)
- [x] Pruebas de integración básicas
- [x] Bugfix: `page.dialog = dialog` → `page.show_dialog(dialog)` (API eliminada en Flet 0.86.1)

## Fase 2 — OCR Inteligente (MVP-2) ✅ PARCIALMENTE VERIFICADO
**Objetivo**: Escaneo de vouchers con extracción automática.
**Duración**: Sprints 2.1 - 2.4

> ✅ Infraestructura OCR escrita y testeada (unit tests pasan).
> ✅ Motor: ONNX Runtime + PP-OCRv6 (no PaddlePaddle — bundle más liviano).
> ✅ Multi-transacción: detección y guardado batch de múltiples montos en un mismo documento.
> ✅ Layout analysis: detección automática tabular vs columnar.
> ✅ Fuzzy date parsing: fechas OCR-garbled (meses truncados, años abreviados).
> ❌ Falta: verificar con build de producción + muestras de vouchers reales.

### Sprint 2.1 — Core OCR + Threading ✅ (código listo)
- [x] Integrar OCR Engine (ONNX Runtime + PP-OCRv6 medium)
  - [x] CRÍTICO: OCR ejecutado en `asyncio.to_thread()`
  - [x] ThreadPoolExecutor dedicado para OCR
- [x] Módulo de preprocesamiento OpenCV (deskew, threshold, denoise)
- [x] Convertidor PDF → imagen (pdf2image)
- [x] Pipeline OCR básico (imagen/PDF → texto)
- [x] LoadingOverlay en UI mientras OCR corre
- [ ] Tests con muestras de vouchers reales (requiere assets/sample_receipts/)

### Sprint 2.2 — Parsers de Emisores ✅ (código listo)
- [x] Registry de parsers (plugin architecture)
- [x] Layout analysis: detección automática tabular vs columnar (overlap ratio + x-range analysis)
- [x] Parser Visa (genérico)
- [x] Parser Mastercard (genérico)
- [x] Parser Amex
- [x] Parser Fallback (ref+date+desc+code+amount, footer exclusion, dedup)
- [x] Fuzzy date parsing: known garbles, digit→letter normalization, sliding window heuristic
- [x] Sistema de confianza por campo
- [x] Tests unitarios de parsers (sin OCR real)
- [ ] Tests con vouchers reales de cada emisor (20+ muestras pendientes)

### Sprint 2.3 — UI de Escaneo ✅ (código listo)
- [x] Pantalla OCR Scan con FilePicker Service (async pick_files, sin overlay)
- [x] Preview de imagen/PDF seleccionado
- [x] Botón "Escanear" con LoadingOverlay
- [x] Formulario de datos extraídos (editables)
- [x] Indicadores de confianza por campo
- [x] Guardar transacción desde OCR
- [x] **Multi-transacción**: Detección de múltiples montos en estados de cuenta
- [x] **Batch save**: Guardado masivo de transacciones detectadas con selección individual

### Sprint 2.4 — Refinamiento OCR ❌ PENDIENTE
- [ ] Almacenamiento de imágenes de recibos
- [ ] Re-escaneo de imágenes guardadas
- [ ] Feedback loop: correcciones del usuario mejoran parsing
- [ ] Optimización de velocidad (OpenVINO si está disponible)
- [ ] Pruebas con 20+ vouchers reales de diferentes emisores

## Fase 3 — Reportes y UX Pro (Estabilización) ❌ PENDIENTE
**Objetivo**: Dashboard avanzado, presupuestos, exportación, build producción.
**Duración**: Sprints 3.1 - 3.4

### Sprint 3.1 — Dashboard Avanzado ✅
- [x] Gráfico de dona/pie: gastos por categoría (CategoryPieChart)
- [ ] Gráfico de línea: evolución mensual
- [ ] Selector de período (mes/año)
- [ ] Top 5 comercios donde más se gasta

### Sprint 3.2 — Presupuestos ✅
- [x] Límite mensual por categoría
- [x] Barra de progreso vs presupuesto
- [x] Alerta visual al superar 80% y 100%
- [ ] Notificaciones en dashboard

### Sprint 3.3 — Exportación y Filtros ✅
- [x] Exportar transacciones a CSV
- [x] Exportar reporte JSON / DB Backup
- [x] Búsqueda por texto en descripciones (Ctrl+F)
- [ ] Filtros combinados (fecha + categoría + monto)

### Sprint 3.4 — Build y Distribución ❌
- [ ] Ejecutar Fase 0 primero (verificar bundle size)
- [ ] Build producción (flet build windows o PyInstaller + NSIS)
- [ ] Bundle de modelo OCR en el .exe
- [ ] Verificar bundle size < 500MB
- [ ] Probar en máquina limpia (sin Python)
- [ ] Documentación de usuario
- [ ] Release v1.0.0

## Post-MVP (Futuro)

| Feature | Prioridad | Complejidad |
|---|---|---|
| Sincronización cloud (Dropbox/OneDrive) | Baja | Alta |
| App Android/iOS | Baja | Alta |
| Web version | Baja | Media |
| Multi-moneda completo | Media | Media |
| Importación CSV bancario | Media | Baja |
| ML para categorización automática (basado en historial) | Alta | Media |
| Recordatorios de facturas | Media | Baja |
| Split de gastos entre personas | Baja | Alta |
| Tags/labels adicionales en transacciones | Baja | Baja |

## Milestones Clave

| Milestone | Fecha estimada | Entregable |
|---|---|---|
| M0 — Stack Verificado | Semana 1 | PoC de build + OCR funcional en CPU |
| M1 — MVP Fundación | Semana 3-4 | App con registro manual + dashboard + undo + onboarding |
| M2 — MVP OCR | Semana 6-7 | App con escaneo de vouchers + PDF funcional |
| M3 — Release 1.0 | Semana 9-10 | App completa con build producción (< 500MB) |
