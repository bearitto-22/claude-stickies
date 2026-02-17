# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A macOS Stickies clone for GNOME, built with Python, GTK4, and libadwaita. Each sticky note is its own window with rich text editing (bold, italic, underline, strikethrough, font family/size, text color), configurable note colors, always-on-top, and translucency.

## Running

```bash
python main.py
```

Requires: Python 3, GTK4, libadwaita (via PyGObject/gi). No build step, no package manager, no tests.

## Key Constraints

- **Forces X11 backend** (`GDK_BACKEND=x11` in `main.py`) because always-on-top uses `_NET_WM_STATE_ABOVE` via raw Xlib ctypes calls. This works under XWayland.
- **Always-on-top** is implemented by sending X11 ClientMessage events directly through `libX11.so.6` (see `note_window.py:_set_keep_above`). This is the most complex and fragile part of the codebase.
- Notes persist as JSON at `$XDG_CONFIG_HOME/claude-stickies/notes.json` (or `~/.config/claude-stickies/notes.json`).
- Saves are debounced (500ms) via `GLib.timeout_add` in `StickiesApp.schedule_save`.

## Architecture

- `main.py` — Entry point; sets X11 backend, launches `StickiesApp`
- `stickies/app.py` — `StickiesApp(Adw.Application)`: manages note lifecycle, tracks `notes` (data) and `windows` (UI) dicts keyed by note ID, handles save coordination
- `stickies/note_window.py` — `NoteWindow(Adw.ApplicationWindow)`: one window per note, builds UI (header bar, format toolbar, text view), handles all user interaction
- `stickies/models.py` — `Note` dataclass with `to_dict`/`from_dict` for serialization
- `stickies/storage.py` — JSON load/save to disk
- `stickies/formatting.py` — TextBuffer tag management; tags use naming conventions: `bold`, `italic`, `size-{n}`, `family-{name}`, `color-{hex}`
- `stickies/serializer.py` — Converts between `Gtk.TextBuffer` and JSON "runs" (list of dicts with `text` + formatting keys). Adjacent runs with identical formatting are merged.
- `stickies/colors.py` — `PALETTE` dict defines 6 note colors; `COLOR_ORDER` controls UI display order; `TEXT_COLORS` defines text color options
- `stickies/css.py` — Generates CSS dynamically from `PALETTE` for both solid and translucent modes
- `stickies/shortcuts.py` — Keyboard shortcuts (Ctrl+B/I/U/D for formatting, Ctrl+N new note, Ctrl+W close, Ctrl+Q quit)

## Formatting System

Rich text uses a "pending tags" pattern: when no text is selected, toggling a format sets a pending tag dict on the window. On `insert-text`, pending tags are applied to the just-inserted text range. This is how format-then-type works. The pending tags dict is passed by reference between `NoteWindow` and `formatting.py` functions.
