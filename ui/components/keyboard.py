"""Global keyboard shortcuts manager for Flet."""


def register_shortcuts(page, handlers: dict[str, callable]):
    """Register keyboard shortcuts.

    Args:
        page: ft.Page instance
        handlers: dict mapping shortcut key (e.g. "Ctrl+N") to callback
    """
    shortcut_map = {}
    for key_combo, handler in handlers.items():
        parts = key_combo.lower().split("+")
        shortcut_map[key_combo] = {
            "ctrl": "ctrl" in parts,
            "alt": "alt" in parts,
            "shift": "shift" in parts,
            "key": parts[-1],
            "handler": handler,
        }

    original_on_keyboard = page.on_keyboard_event

    def on_keyboard(e):
        for shortcut in shortcut_map.values():
            if getattr(e, "ctrl", False) == shortcut["ctrl"]:
                if getattr(e, "alt", False) == shortcut["alt"]:
                    if getattr(e, "shift", False) == shortcut["shift"]:
                        if e.key.lower() == shortcut["key"]:
                            shortcut["handler"]()
                            return
        if original_on_keyboard:
            original_on_keyboard(e)

    page.on_keyboard_event = on_keyboard
