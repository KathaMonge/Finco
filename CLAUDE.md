# Finco — Instrucciones para Agentes

Repo publico. Punto de partida obligatorio antes de tocar codigo.

## Leer primero

| Archivo | Contenido |
|---|---|
| `CONTEXT.md` | Reglas de oro, stack, lecciones aprendidas (Flet API, SQLAlchemy, etc.), AI Context Block |
| `ARCHITECTURE.md` | Arquitectura tecnica, pipeline OCR, threading |
| `PLAN.md` | Vision, requerimientos, pre-mortem |
| `ROADMAP.md` | Fases, sprints |
| `PROJECT_STRUCTURE.md` | Arbol de directorios, convenciones de nombrado |

No repitas esas reglas aca — si cambian, actualiza el archivo fuente, no este.

## Datos sensibles (repo publico — critico)

Este proyecto procesa **estados de cuenta y vouchers reales** via OCR. Cualquier archivo generado durante debug/desarrollo puede contener nombres, montos, comercios y numeros de tarjeta reales.

1. **Nunca commitear output de debug con datos reales.** Scripts tipo `debug_*.py` que guardan imagenes/JSON de resultados OCR deben escribir a una carpeta ignorada (`.local/`, `tmp/`) — nunca al repo root. Ya cubierto por `.gitignore` (`debug_*.png/json/jpg`), pero no confies solo en eso: revisa `git status` antes de cualquier commit que toque el pipeline OCR.
2. **Fixtures de test deben ser sinteticas**, no capturas de tu propio estado de cuenta. Genera imagenes con texto ficticio ("MERCHANT_A", "$XXX.XX", nombre generico) para `assets/sample_receipts/` y `tests/`.
3. **`git add` explicito**, no `git add .` en este repo. Revisa `git status`/`git diff --cached` antes de commit, en especial si el cambio toca `services/ocr/`.
4. **Antes de push:** si algo sensible ya se commiteo, no lo arregles con un commit nuevo de borrado — el dato sigue en el historial. Purga con `git filter-branch`/`filter-repo` y coordina el force-push (ver incidente resuelto 2026-07-23 en `CONTEXT.md`).
5. **Pre-commit activo**: `check-added-large-files` (>500KB) y `detect-private-key` corren en cada commit (`.pre-commit-config.yaml`). Instalar una vez: `pre-commit install`.

## Workflow de desarrollo

- Sin sobre-ingenieria: no agregues abstracciones, flags o validaciones para casos hipoteticos. Ver "Lecciones Aprendidas" en `CONTEXT.md` (ej. Alembic descartado por overkill).
- Nuevas dependencias se justifican en `PLAN.md` antes de agregarlas.
- Todo corre offline, CPU-only, sin GPU ni APIs externas.
- OCR y cualquier proceso pesado va en thread (`asyncio.to_thread` / `ThreadPoolExecutor`) — nunca bloquear el event loop de Flet.
- Comandos: `pytest tests/`, `ruff check .`, `ruff format .` antes de dar por terminado un cambio.
