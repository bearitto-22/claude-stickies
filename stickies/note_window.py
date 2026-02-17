"""Per-note window with toolbar, text area, and formatting controls."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib, Pango

from .models import Note
from .colors import PALETTE, COLOR_ORDER, TEXT_COLORS
from .formatting import (
    setup_tags, toggle_tag, apply_font_size, apply_font_family,
    apply_text_color, apply_pending_tags, get_tags_at_iter,
    DEFAULT_FONT_SIZE, DEFAULT_FONT_FAMILY, FONT_FAMILIES, FONT_SIZES,
)
from .serializer import serialize_buffer, deserialize_to_buffer
from .shortcuts import setup_window_shortcuts


class NoteWindow(Adw.ApplicationWindow):
    def __init__(self, app, note: Note):
        super().__init__(application=app, title="Sticky Note")
        self.note = note
        self.app = app
        self.current_color = note.color
        self.always_on_top = note.always_on_top
        self.translucent = note.translucent
        self._pending_tags: dict = {}
        self._is_deleting = False
        self._updating_toolbar = False

        self.set_default_size(note.width, note.height)

        # Build UI
        self._build_ui()

        # Apply color
        self._apply_color_css()

        # Load content
        if note.content:
            deserialize_to_buffer(self.buffer, note.content)

        # Apply translucency
        if self.translucent:
            self._apply_translucency(True)

        # Update title from first line
        self._update_title()

        # Defer always-on-top until the window is actually mapped
        if self.always_on_top:
            self.connect("map", self._on_map_set_above)

        # Setup shortcuts
        setup_window_shortcuts(self)

        # Connect close
        self.connect("close-request", self._on_close_request)

    def _build_ui(self):
        """Build the complete window UI."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header bar
        self.header = Adw.HeaderBar()
        self.header.set_show_end_title_buttons(True)
        self.header.set_show_start_title_buttons(True)
        self.header.set_decoration_layout("close:")

        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_popover(self._build_menu_popover())
        self.header.pack_end(menu_button)

        # New note button
        new_btn = Gtk.Button(icon_name="list-add-symbolic")
        new_btn.set_tooltip_text("New Note (Ctrl+N)")
        new_btn.connect("clicked", lambda _: self.app.activate_action("new-note"))
        self.header.pack_start(new_btn)

        main_box.append(self.header)

        # Format toolbar
        self.toolbar = self._build_format_toolbar()
        main_box.append(self.toolbar)

        # Text view in a scrolled window
        scrolled = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.textview = Gtk.TextView()
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.set_left_margin(0)
        self.textview.set_right_margin(0)
        self.textview.set_top_margin(0)
        self.textview.set_bottom_margin(0)
        self.textview.add_css_class("note-textview")

        self.buffer = self.textview.get_buffer()
        setup_tags(self.buffer)

        # Connect buffer signals
        self.buffer.connect("changed", self._on_buffer_changed)
        self.buffer.connect_after("insert-text", self._on_after_insert_text)
        self.buffer.connect("mark-set", self._on_cursor_moved)

        scrolled.set_child(self.textview)
        main_box.append(scrolled)

        self.set_content(main_box)
        self.add_css_class("note-window")

    def _build_format_toolbar(self) -> Gtk.Box:
        """Build the formatting toolbar."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        toolbar.add_css_class("format-toolbar")

        # Bold
        self.bold_btn = Gtk.ToggleButton(label="B")
        self.bold_btn.set_tooltip_text("Bold (Ctrl+B)")
        self.bold_btn.connect("toggled", self._on_format_toggle, "bold")
        toolbar.append(self.bold_btn)

        # Italic
        self.italic_btn = Gtk.ToggleButton(label="I")
        self.italic_btn.set_tooltip_text("Italic (Ctrl+I)")
        self.italic_btn.connect("toggled", self._on_format_toggle, "italic")
        toolbar.append(self.italic_btn)

        # Underline
        self.underline_btn = Gtk.ToggleButton(label="U")
        self.underline_btn.set_tooltip_text("Underline (Ctrl+U)")
        self.underline_btn.connect("toggled", self._on_format_toggle, "underline")
        toolbar.append(self.underline_btn)

        # Strikethrough
        self.strike_btn = Gtk.ToggleButton(label="S")
        self.strike_btn.set_tooltip_text("Strikethrough (Ctrl+D)")
        self.strike_btn.connect("toggled", self._on_format_toggle, "strikethrough")
        toolbar.append(self.strike_btn)

        # Separator
        toolbar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # Font family dropdown
        self.family_dropdown = Gtk.DropDown.new_from_strings(FONT_FAMILIES)
        self.family_dropdown.set_tooltip_text("Font Family")
        self.family_dropdown.set_size_request(100, -1)
        try:
            idx = FONT_FAMILIES.index(DEFAULT_FONT_FAMILY)
            self.family_dropdown.set_selected(idx)
        except ValueError:
            pass
        self.family_dropdown.connect("notify::selected", self._on_family_changed)
        toolbar.append(self.family_dropdown)

        # Font size spin button
        adj = Gtk.Adjustment(value=DEFAULT_FONT_SIZE, lower=8, upper=48, step_increment=1)
        self.size_spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0)
        self.size_spin.set_tooltip_text("Font Size")
        self.size_spin.set_size_request(60, -1)
        self.size_spin.connect("value-changed", self._on_size_changed)
        toolbar.append(self.size_spin)

        # Separator
        toolbar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # Text color button
        self.color_btn = Gtk.MenuButton(label="A")
        self.color_btn.set_tooltip_text("Text Color")
        self.color_btn.set_popover(self._build_text_color_popover())
        toolbar.append(self.color_btn)

        return toolbar

    def _build_text_color_popover(self) -> Gtk.Popover:
        """Build a popover with text color swatches."""
        popover = Gtk.Popover()
        grid = Gtk.FlowBox()
        grid.set_max_children_per_line(4)
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.set_homogeneous(True)

        for hex_color, name in TEXT_COLORS:
            btn = Gtk.Button()
            btn.add_css_class("text-color-swatch")
            btn.set_tooltip_text(name)
            # Set background via inline CSS
            css = Gtk.CssProvider()
            css.load_from_string(f".text-color-{name.lower()} {{ background: {hex_color}; }}")
            btn.add_css_class(f"text-color-{name.lower()}")
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), css,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
            )
            btn.connect("clicked", self._on_text_color_selected, hex_color, popover)
            grid.append(btn)

        popover.set_child(grid)
        return popover

    def _build_menu_popover(self) -> Gtk.Popover:
        """Build the note menu popover."""
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        # Note color section
        color_label = Gtk.Label(label="Note Color", xalign=0)
        color_label.set_margin_bottom(4)
        box.append(color_label)

        color_flow = Gtk.FlowBox()
        color_flow.set_max_children_per_line(6)
        color_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        color_flow.set_homogeneous(True)

        self._color_swatches = {}
        for color_name in COLOR_ORDER:
            colors = PALETTE[color_name]
            btn = Gtk.Button()
            btn.add_css_class("color-swatch")
            btn.set_tooltip_text(color_name.capitalize())
            css = Gtk.CssProvider()
            css.load_from_string(f".swatch-{color_name} {{ background: {colors['bg']}; }}")
            btn.add_css_class(f"swatch-{color_name}")
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), css,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
            )
            if color_name == self.current_color:
                btn.add_css_class("selected")
            btn.connect("clicked", self._on_note_color_selected, color_name, popover)
            self._color_swatches[color_name] = btn
            color_flow.append(btn)

        box.append(color_flow)

        # Separator
        box.append(Gtk.Separator())

        # Always on top toggle
        aot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        aot_box.append(Gtk.Label(label="Always on Top", hexpand=True, xalign=0))
        self.aot_switch = Gtk.Switch(active=self.always_on_top)
        self.aot_switch.connect("notify::active", self._on_always_on_top_toggled)
        aot_box.append(self.aot_switch)
        box.append(aot_box)

        # Translucency toggle
        trans_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        trans_box.append(Gtk.Label(label="Translucent", hexpand=True, xalign=0))
        self.trans_switch = Gtk.Switch(active=self.translucent)
        self.trans_switch.connect("notify::active", self._on_translucency_toggled)
        trans_box.append(self.trans_switch)
        box.append(trans_box)

        # Separator
        box.append(Gtk.Separator())

        # Delete button
        delete_btn = Gtk.Button(label="Delete Note")
        delete_btn.add_css_class("destructive-action")
        delete_btn.connect("clicked", lambda _: self.app.delete_note(self.note.id))
        box.append(delete_btn)

        popover.set_child(box)
        return popover

    # --- Signal handlers ---

    def _on_format_toggle(self, button, tag_name):
        """Handle format toggle button clicks."""
        if self._updating_toolbar:
            return
        toggle_tag(self.buffer, tag_name, self._pending_tags)
        self.textview.grab_focus()

    def _on_family_changed(self, dropdown, pspec):
        """Handle font family change."""
        if self._updating_toolbar:
            return
        idx = dropdown.get_selected()
        if 0 <= idx < len(FONT_FAMILIES):
            family = FONT_FAMILIES[idx]
            result = apply_font_family(self.buffer, family, self._pending_tags)
            if result is not None:
                self._pending_tags = result
            self.textview.grab_focus()

    def _on_size_changed(self, spin):
        """Handle font size change."""
        if self._updating_toolbar:
            return
        size = int(spin.get_value())
        if size in FONT_SIZES:
            result = apply_font_size(self.buffer, size, self._pending_tags)
            if result is not None:
                self._pending_tags = result
        self.textview.grab_focus()

    def _on_text_color_selected(self, btn, hex_color, popover):
        """Handle text color selection."""
        result = apply_text_color(self.buffer, hex_color, self._pending_tags)
        if result is not None:
            self._pending_tags = result
        popover.popdown()
        self.textview.grab_focus()

    def _on_note_color_selected(self, btn, color_name, popover):
        """Handle note color change."""
        # Update selected state
        for name, swatch in self._color_swatches.items():
            if name == color_name:
                swatch.add_css_class("selected")
            else:
                swatch.remove_css_class("selected")

        self.current_color = color_name
        self._apply_color_css()
        self.app.schedule_save()
        popover.popdown()

    def _on_always_on_top_toggled(self, switch, pspec):
        """Toggle always-on-top."""
        self.always_on_top = switch.get_active()
        self._set_keep_above(self.always_on_top)
        self.app.schedule_save()

    def _on_translucency_toggled(self, switch, pspec):
        """Toggle translucency."""
        self.translucent = switch.get_active()
        self._apply_translucency(self.translucent)
        self._apply_color_css()
        self.app.schedule_save()

    def _on_buffer_changed(self, buffer):
        """Handle text content changes."""
        self._update_title()
        self.app.schedule_save()

    def _on_after_insert_text(self, buffer, location, text, length):
        """Apply pending tags to just-inserted text."""
        if self._pending_tags:
            end_offset = location.get_offset()
            start_offset = end_offset - len(text)
            apply_pending_tags(buffer, self._pending_tags, start_offset, end_offset)

    def _on_cursor_moved(self, buffer, location, mark):
        """Update toolbar state when cursor moves."""
        if mark != buffer.get_insert():
            return
        self._update_toolbar_state()

    def _on_close_request(self, window):
        """Handle window close."""
        if not self._is_deleting:
            self.app.on_window_closed(self.note.id)
        return False

    # --- Public methods for shortcuts ---

    def toggle_format(self, tag_name: str):
        """Toggle a format tag (called from shortcuts)."""
        toggle_tag(self.buffer, tag_name, self._pending_tags)
        self._update_toolbar_state()

    def get_serialized_content(self) -> list[dict]:
        """Get current content as serialized runs."""
        return serialize_buffer(self.buffer)

    # --- Private methods ---

    def _apply_color_css(self):
        """Apply note color CSS classes."""
        # Remove all color classes
        for name in COLOR_ORDER:
            self.remove_css_class(f"note-{name}")
            self.remove_css_class(f"note-{name}-translucent")

        if self.translucent:
            self.add_css_class(f"note-{self.current_color}-translucent")
        else:
            self.add_css_class(f"note-{self.current_color}")

    def _update_title(self):
        """Set window title from first line of content."""
        start = self.buffer.get_start_iter()
        end = start.copy()
        end.forward_to_line_end()
        first_line = self.buffer.get_text(start, end, False).strip()
        self.set_title(first_line if first_line else "Sticky Note")

    def _update_toolbar_state(self):
        """Update toolbar toggles/values to reflect cursor position."""
        self._updating_toolbar = True

        mark = self.buffer.get_insert()
        it = self.buffer.get_iter_at_mark(mark)
        tags = get_tags_at_iter(self.buffer, it)

        # Also include pending tags
        merged = {**tags, **self._pending_tags}

        self.bold_btn.set_active("bold" in merged)
        self.italic_btn.set_active("italic" in merged)
        self.underline_btn.set_active("underline" in merged)
        self.strike_btn.set_active("strikethrough" in merged)

        # Font size
        active_size = DEFAULT_FONT_SIZE
        for key in merged:
            if key.startswith("size-"):
                try:
                    active_size = int(key[5:])
                except ValueError:
                    pass
        self.size_spin.set_value(active_size)

        # Font family
        active_family = DEFAULT_FONT_FAMILY
        for key in merged:
            if key.startswith("family-"):
                active_family = key[7:]
        try:
            idx = FONT_FAMILIES.index(active_family)
            self.family_dropdown.set_selected(idx)
        except ValueError:
            pass

        self._updating_toolbar = False

    def _on_map_set_above(self, widget):
        """Set always-on-top once the window is mapped and visible."""
        GLib.timeout_add(150, self._set_keep_above, True)

    def _apply_translucency(self, translucent: bool):
        """Apply or remove window translucency via widget opacity."""
        self.set_opacity(0.88 if translucent else 1.0)

    def _get_window_xid(self) -> int | None:
        """Get the X11 window ID from the GDK surface, if available."""
        surface = self.get_surface()
        if surface is None:
            return None
        try:
            gi.require_version("GdkX11", "4.0")
            from gi.repository import GdkX11
            if isinstance(surface, GdkX11.X11Surface):
                return surface.get_xid()
        except (ValueError, ImportError):
            pass
        return None

    def _set_keep_above(self, above: bool):
        """Set window to stay above others via X11 _NET_WM_STATE ClientMessage.

        This sends a proper EWMH client message to the root window, which is
        the correct way to ask the window manager to toggle always-on-top.
        Requires the app to be running on an X11 display (see main.py).
        """
        import ctypes

        xid = self._get_window_xid()
        if not xid:
            return False

        try:
            libx11 = ctypes.CDLL("libX11.so.6")
        except OSError:
            return False

        # Xlib constants
        SubstructureRedirectMask = 1 << 20
        SubstructureNotifyMask = 1 << 19
        ClientMessage = 33  # X event type

        # XClientMessageEvent structure (64-bit)
        class XClientMessageEvent(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.c_int),
                ("serial", ctypes.c_ulong),
                ("send_event", ctypes.c_int),
                ("display", ctypes.c_void_p),
                ("window", ctypes.c_ulong),
                ("message_type", ctypes.c_ulong),
                ("format", ctypes.c_int),
                ("data", ctypes.c_long * 5),
            ]

        try:
            # Set arg/return types to avoid segfaults
            libx11.XOpenDisplay.argtypes = [ctypes.c_char_p]
            libx11.XOpenDisplay.restype = ctypes.c_void_p
            libx11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
            libx11.XDefaultRootWindow.restype = ctypes.c_ulong
            libx11.XInternAtom.argtypes = [
                ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int,
            ]
            libx11.XInternAtom.restype = ctypes.c_ulong
            libx11.XSendEvent.argtypes = [
                ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int,
                ctypes.c_long, ctypes.c_void_p,
            ]
            libx11.XSendEvent.restype = ctypes.c_int
            libx11.XFlush.argtypes = [ctypes.c_void_p]
            libx11.XCloseDisplay.argtypes = [ctypes.c_void_p]

            display = libx11.XOpenDisplay(None)
            if not display:
                return False

            root = libx11.XDefaultRootWindow(display)

            wm_state = libx11.XInternAtom(
                display, b"_NET_WM_STATE", 0,
            )
            wm_state_above = libx11.XInternAtom(
                display, b"_NET_WM_STATE_ABOVE", 0,
            )

            # Build the ClientMessage event
            # data.l[0] = action: 1=add, 0=remove
            # data.l[1] = _NET_WM_STATE_ABOVE atom
            # data.l[2] = 0 (no second property)
            # data.l[3] = 1 (source: application)
            event = XClientMessageEvent()
            event.type = ClientMessage
            event.serial = 0
            event.send_event = 1
            event.display = display
            event.window = xid
            event.message_type = wm_state
            event.format = 32
            event.data[0] = 1 if above else 0
            event.data[1] = wm_state_above
            event.data[2] = 0
            event.data[3] = 1
            event.data[4] = 0

            libx11.XSendEvent(
                display, root, 0,
                SubstructureRedirectMask | SubstructureNotifyMask,
                ctypes.byref(event),
            )
            libx11.XFlush(display)
            libx11.XCloseDisplay(display)
        except Exception:
            pass

        return False  # Don't repeat GLib.timeout_add
