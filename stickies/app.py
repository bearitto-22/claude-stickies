"""Main application class."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, Gdk, GLib

from .models import Note
from .storage import load_notes, save_notes
from .note_window import NoteWindow
from .css import generate_css
from .shortcuts import setup_app_shortcuts


class StickiesApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.claude.stickies",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.notes: dict[str, Note] = {}  # id -> Note
        self.windows: dict[str, NoteWindow] = {}  # id -> NoteWindow
        self._save_timeout_id = None

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Load CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string(generate_css())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Register actions
        new_action = Gio.SimpleAction.new("new-note", None)
        new_action.connect("activate", self._on_new_note)
        self.add_action(new_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)

        setup_app_shortcuts(self)

    def do_activate(self):
        # Load saved notes
        saved = load_notes()
        if not saved:
            # Create a default note
            saved = [Note()]

        for note in saved:
            self.notes[note.id] = note
            self._open_note_window(note)

    def _open_note_window(self, note: Note):
        """Create and show a window for a note."""
        win = NoteWindow(app=self, note=note)
        self.windows[note.id] = win
        win.present()

    def _on_new_note(self, action, param):
        """Create a new note."""
        note = Note()
        self.notes[note.id] = note
        self._open_note_window(note)
        self.schedule_save()

    def delete_note(self, note_id: str):
        """Delete a note and close its window."""
        if note_id in self.notes:
            del self.notes[note_id]
        if note_id in self.windows:
            win = self.windows.pop(note_id)
            win._is_deleting = True
            win.close()
        self.schedule_save()

        # If no notes left, create a new one
        if not self.notes:
            self._on_new_note(None, None)

    def on_window_closed(self, note_id: str):
        """Called when a note window is closed (not deleted)."""
        if note_id in self.windows:
            # Save current state before removing
            win = self.windows[note_id]
            self._sync_note_from_window(win)
            del self.windows[note_id]
        self.schedule_save()

        # If no windows left, quit
        if not self.windows:
            self.quit()

    def _sync_note_from_window(self, win: NoteWindow):
        """Update note data from window state."""
        note = win.note
        note.width, note.height = win.get_default_size()
        note.content = win.get_serialized_content()
        note.color = win.current_color
        note.always_on_top = win.always_on_top
        note.translucent = win.translucent

    def schedule_save(self):
        """Debounced save - saves 500ms after last change."""
        if self._save_timeout_id:
            GLib.source_remove(self._save_timeout_id)
        self._save_timeout_id = GLib.timeout_add(500, self._do_save)

    def _do_save(self):
        """Actually persist notes."""
        # Sync all open windows
        for note_id, win in self.windows.items():
            self._sync_note_from_window(win)
        save_notes(list(self.notes.values()))
        self._save_timeout_id = None
        return False  # Don't repeat
