<div align="center">
  <h1>Finco</h1>
  <p><strong>Finanzas Compartidas</strong> — Gestión de gastos con OCR, multi-cuenta y dashboard</p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python">
    <img src="https://img.shields.io/badge/Flet-0.86.1-teal?logo=flutter">
    <img src="https://img.shields.io/badge/OCR-PP--OCRv6-orange">
    <img src="https://img.shields.io/badge/DB-SQLite_WAL-brightgreen">
    <img src="https://img.shields.io/badge/Platform-Windows-lightgrey">
  </p>
</div>

---

## Características

- **OCR Inteligente** — Escanea vouchers de Visa, Mastercard, Amex y más. Soporta imágenes y PDFs.
- **Multi-transacción** — Un solo estado de cuenta genera múltiples transacciones seleccionables.
- **Multi-cuenta** — Efectivo, débito y crédito.
- **Presupuestos** — Límite mensual por categoría con alertas visuales al 80% y 100%.
- **Dashboard** — Resumen mensual, gastos por categoría (gráfico de dona).
- **Offline-first** — Todo funciona sin internet. OCR 100% local.
- **Dark mode** — Tema oscuro con variante de alto contraste.
- **Undo pattern** — Acciones destructivas con SnackBar + "Deshacer", sin modales.

## Stack

| Componente | Tecnología |
|---|---|
| UI | Python Flet 0.86.1 (Material Design) |
| OCR | ONNX Runtime + PP-OCRv6 (CPU) |
| Base de Datos | SQLite + SQLAlchemy 2.0 (WAL mode) |
| PDF | pdf2image |
| Charts | fl_chart (nativo Flet) |
| Tests | pytest + pytest-asyncio |
| Linting | ruff |

## Requisitos

- Python 3.12+
- Windows (target de producción; funciona en Linux/macOS para desarrollo)

## Instalación

```bash
git clone https://github.com/KathaMonge/Finco.git
cd Finco
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Desarrollo

```bash
python main.py              # Iniciar app en modo desarrollo
pytest tests/               # Tests
ruff check .                # Linting
```

## Uso Rápido

1. Al primer inicio, el **Onboarding Wizard** guía la configuración inicial.
2. Crea una cuenta (efectivo/débito/crédito) y categorías.
3. Registra transacciones manualmente o escanea vouchers con OCR.
4. Revisa el dashboard para ver resúmenes y gráficos.

## Estructura

```
Finco/
├── main.py              # Entry point
├── core/                # DB, config, settings, modelos, schemas
├── ui/                  # Vistas y componentes Flet
├── services/            # Lógica de negocio + OCR pipeline
├── utils/               # Helpers, constantes, threading
├── tests/               # Tests unitarios y de integración
└── assets/              # Recursos (iconos, sample receipts)
```

## Build Producción

```bash
pip install -r requirements.txt
flet build windows       # o PyInstaller + NSIS
```

> Bundle actualmente usa ONNX Runtime (~300-400MB). Si se necesita reducir, evaluar PyInstaller + NSIS.

## Licencia

MIT
