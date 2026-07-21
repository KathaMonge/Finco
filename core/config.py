import os
from pathlib import Path


def get_user_data_dir() -> Path:
    app = "Finco"
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif os.name == "posix":
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    else:
        base = Path.home() / ".finco"
    return base / app


USER_DATA_DIR = get_user_data_dir()
DB_PATH = USER_DATA_DIR / "finco.db"
RECEIPTS_DIR = USER_DATA_DIR / "receipts"
SCHEMA_VERSION = 1

DEFAULT_CATEGORIES = [
    {"name": "Alimentación", "icon": "restaurant", "color": "#FF6B6B"},
    {"name": "Transporte", "icon": "directions_car", "color": "#4ECDC4"},
    {"name": "Servicios", "icon": "home", "color": "#45B7D1"},
    {"name": "Entretenimiento", "icon": "movie", "color": "#96CEB4"},
    {"name": "Salud", "icon": "local_hospital", "color": "#FFEAA7"},
    {"name": "Educación", "icon": "school", "color": "#DDA0DD"},
    {"name": "Otros", "icon": "category", "color": "#98A2FF"},
]
