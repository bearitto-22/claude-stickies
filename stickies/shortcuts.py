"""Keyboard shortcut registration."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


def setup_app_shortcuts(app):
    """Register application-level keyboard shortcuts."""
    app.set_accels_for_action("app.new-note", ["<Control>n"])
    app.set_accels_for_action("app.quit", ["<Control>q"])


def setup_window_shortcuts(window):
    """Register window-level keyboard shortcuts via event controller."""
    controller = Gtk.EventControllerKey()
    controller.connect("key-pressed", _on_key_pressed, window)
    window.add_controller(controller)


def _on_key_pressed(controller, keyval, keycode, state, window):
    """Handle per-window keyboard shortcuts."""
    from gi.repository import Gdk

    ctrl = state & Gdk.ModifierType.CONTROL_MASK

    if not ctrl:
        return False

    key_name = Gdk.keyval_name(keyval).lower() if Gdk.keyval_name(keyval) else ""

    if key_name == "b":
        window.toggle_format("bold")
        return True
    elif key_name == "i":
        window.toggle_format("italic")
        return True
    elif key_name == "u":
        window.toggle_format("underline")
        return True
    elif key_name == "d":
        window.toggle_format("strikethrough")
        return True
    elif key_name == "w":
        window.close()
        return True

    return False
