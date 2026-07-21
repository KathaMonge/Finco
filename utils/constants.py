APP_NAME = "Finco"
APP_VERSION = "0.1.0"

import flet as ft

NAV_ITEMS = [
    {"label": "Dashboard", "icon": ft.icons.Icons.DASHBOARD, "index": 0, "shortcut": "Ctrl+1"},
    {"label": "Transacciones", "icon": ft.icons.Icons.RECEIPT_LONG, "index": 1, "shortcut": "Ctrl+2"},
    {"label": "OCR Scan", "icon": ft.icons.Icons.DOCUMENT_SCANNER, "index": 2, "shortcut": "Ctrl+3"},
    {"label": "Categorías", "icon": ft.icons.Icons.LABEL, "index": 3, "shortcut": "Ctrl+4"},
    {"label": "Cuentas", "icon": ft.icons.Icons.ACCOUNT_BALANCE, "index": 4, "shortcut": "Ctrl+5"},
]

ACCOUNT_TYPES = [
    {"value": "cash", "label": "Efectivo", "icon": "payments"},
    {"value": "debit", "label": "Débito", "icon": "credit_card"},
    {"value": "credit", "label": "Crédito", "icon": "credit_score"},
]

TRANSACTION_TYPES = [
    {"value": "expense", "label": "Gasto", "icon": "arrow_upward", "color": "#FF6B6B"},
    {"value": "income", "label": "Ingreso", "icon": "arrow_downward", "color": "#4ECDC4"},
]

CONFIDENCE_COLORS = {
    "high": "#4ECDC4",
    "medium": "#FFD93D",
    "low": "#FF6B6B",
}

OWNERSHIP_TYPES = [
    {"value": "shared", "label": "Compartido 50/50", "icon": "people", "color": "#4ECDC4", "description": "Se divide con tu papa"},
    {"value": "personal", "label": "Personal", "icon": "person", "color": "#FF6B6B", "description": "Pagas todo vos"},
    {"value": "external", "label": "Externo", "icon": "block", "color": "#9E9E9E", "description": "No pagas nada (lo cubre tu papa)"},
]

OWNERSHIP_ICONS = {t["value"]: t["icon"] for t in OWNERSHIP_TYPES}
OWNERSHIP_COLORS = {t["value"]: t["color"] for t in OWNERSHIP_TYPES}
OWNERSHIP_LABELS = {t["value"]: t["label"] for t in OWNERSHIP_TYPES}
