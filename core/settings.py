import json
from pathlib import Path
from core.config import USER_DATA_DIR


_USER_SETTINGS_PATH = USER_DATA_DIR / "settings.json"

_defaults = {
    "onboarding_completed": False,
}


def _load() -> dict:
    if _USER_SETTINGS_PATH.exists():
        try:
            return json.loads(_USER_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save(settings: dict):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    _USER_SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def get(key: str):
    data = _load()
    return data.get(key, _defaults.get(key))


def set(key: str, value):
    data = _load()
    data[key] = value
    _save(data)
