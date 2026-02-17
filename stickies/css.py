"""CSS styling for sticky notes."""

from .colors import PALETTE


def generate_css() -> str:
    """Generate all CSS for the application."""
    css = """
/* Base note window styling */
.note-window {
    border-radius: 0;
}

.note-window headerbar {
    min-height: 32px;
    padding: 0 6px;
    border-radius: 0;
    box-shadow: none;
    border: none;
}

.note-window headerbar .title {
    font-size: 12px;
    font-weight: 600;
}

/* Text view styling */
.note-textview {
    font-size: 14px;
    padding: 8px 10px;
    caret-color: currentColor;
}

.note-textview text {
    background: transparent;
}

/* Toolbar styling */
.format-toolbar {
    min-height: 28px;
    padding: 2px 6px;
    border: none;
    box-shadow: none;
}

.format-toolbar button {
    min-height: 22px;
    min-width: 22px;
    padding: 2px 5px;
    margin: 1px;
    border-radius: 4px;
    font-size: 11px;
}

.format-toolbar button:checked {
    font-weight: 800;
}

.format-toolbar .linked button {
    min-width: 18px;
}

/* Color swatch button */
.color-swatch {
    min-height: 24px;
    min-width: 24px;
    border-radius: 50%;
    padding: 0;
    margin: 3px;
    border: 2px solid rgba(0,0,0,0.15);
}

.color-swatch:hover {
    border-color: rgba(0,0,0,0.4);
}

.color-swatch.selected {
    border-color: rgba(0,0,0,0.7);
    border-width: 3px;
}

/* Text color swatch */
.text-color-swatch {
    min-height: 20px;
    min-width: 20px;
    border-radius: 3px;
    padding: 0;
    margin: 2px;
    border: 1px solid rgba(0,0,0,0.2);
}

.text-color-swatch:hover {
    border-color: rgba(0,0,0,0.5);
}
"""

    # Generate per-color classes for both solid and translucent modes
    for name, colors in PALETTE.items():
        css += f"""
/* {name} note */
.note-{name},
.note-{name} .note-textview,
.note-{name} .note-textview text,
.note-{name} scrolledwindow {{
    background: {colors['header']};
    color: {colors['text']};
}}
.note-{name} headerbar,
.note-{name} .format-toolbar {{
    background: {colors['header']};
    color: {colors['text']};
}}
.note-{name}-translucent,
.note-{name}-translucent .note-textview,
.note-{name}-translucent .note-textview text,
.note-{name}-translucent scrolledwindow {{
    background: {colors['header_alpha']};
    color: {colors['text']};
}}
.note-{name}-translucent headerbar,
.note-{name}-translucent .format-toolbar {{
    background: {colors['header_alpha']};
    color: {colors['text']};
}}
"""

    return css
