"""Rich text formatting for TextBuffer."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Pango


# Default font settings
DEFAULT_FONT_SIZE = 14
DEFAULT_FONT_FAMILY = "Sans"

FONT_FAMILIES = ["Sans", "Serif", "Monospace", "Cantarell", "Ubuntu", "Noto Sans"]
FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48]


def setup_tags(buffer: Gtk.TextBuffer):
    """Create all formatting tags on a TextBuffer."""
    tag_table = buffer.get_tag_table()

    # Bold, italic, underline, strikethrough
    buffer.create_tag("bold", weight=Pango.Weight.BOLD)
    buffer.create_tag("italic", style=Pango.Style.ITALIC)
    buffer.create_tag("underline", underline=Pango.Underline.SINGLE)
    buffer.create_tag("strikethrough", strikethrough=True)

    # Font sizes
    for size in FONT_SIZES:
        buffer.create_tag(f"size-{size}", size=size * Pango.SCALE)

    # Font families
    for family in FONT_FAMILIES:
        buffer.create_tag(f"family-{family}", family=family)

    # Text colors - create on demand via get_or_create_color_tag


def get_or_create_color_tag(buffer: Gtk.TextBuffer, hex_color: str) -> Gtk.TextTag:
    """Get or create a text color tag."""
    tag_name = f"color-{hex_color}"
    tag_table = buffer.get_tag_table()
    tag = tag_table.lookup(tag_name)
    if tag is None:
        tag = buffer.create_tag(tag_name, foreground=hex_color)
    return tag


def toggle_tag(buffer: Gtk.TextBuffer, tag_name: str, pending_tags: dict):
    """Toggle a boolean tag (bold/italic/underline/strikethrough) on selection or pending."""
    bounds = buffer.get_selection_bounds()
    if bounds:
        start, end = bounds
        tag = buffer.get_tag_table().lookup(tag_name)
        if tag is None:
            return
        # Check if entire selection already has this tag
        if _selection_has_tag(buffer, tag, start, end):
            buffer.remove_tag(tag, start, end)
        else:
            buffer.emit("begin-user-action")
            buffer.apply_tag(tag, start, end)
            buffer.emit("end-user-action")
    else:
        # No selection: toggle pending
        if tag_name in pending_tags:
            del pending_tags[tag_name]
        else:
            pending_tags[tag_name] = True


def apply_font_size(buffer: Gtk.TextBuffer, size: int, pending_tags: dict):
    """Apply a font size to selection or set as pending."""
    bounds = buffer.get_selection_bounds()
    if bounds:
        start, end = bounds
        # Remove all existing size tags
        for s in FONT_SIZES:
            tag = buffer.get_tag_table().lookup(f"size-{s}")
            if tag:
                buffer.remove_tag(tag, start, end)
        # Apply new size
        tag = buffer.get_tag_table().lookup(f"size-{size}")
        if tag:
            buffer.emit("begin-user-action")
            buffer.apply_tag(tag, start, end)
            buffer.emit("end-user-action")
    else:
        # Remove any pending size, set new one
        pending_tags = {k: v for k, v in pending_tags.items() if not k.startswith("size-")}
        pending_tags[f"size-{size}"] = True
        return pending_tags
    return pending_tags


def apply_font_family(buffer: Gtk.TextBuffer, family: str, pending_tags: dict):
    """Apply a font family to selection or set as pending."""
    bounds = buffer.get_selection_bounds()
    if bounds:
        start, end = bounds
        for f in FONT_FAMILIES:
            tag = buffer.get_tag_table().lookup(f"family-{f}")
            if tag:
                buffer.remove_tag(tag, start, end)
        tag = buffer.get_tag_table().lookup(f"family-{family}")
        if tag:
            buffer.emit("begin-user-action")
            buffer.apply_tag(tag, start, end)
            buffer.emit("end-user-action")
    else:
        pending_tags = {k: v for k, v in pending_tags.items() if not k.startswith("family-")}
        pending_tags[f"family-{family}"] = True
        return pending_tags
    return pending_tags


def apply_text_color(buffer: Gtk.TextBuffer, hex_color: str, pending_tags: dict):
    """Apply a text color to selection or set as pending."""
    bounds = buffer.get_selection_bounds()
    if bounds:
        start, end = bounds
        # Remove existing color tags by iterating tags on the range
        _remove_color_tags_in_range(buffer, start, end)
        tag = get_or_create_color_tag(buffer, hex_color)
        buffer.emit("begin-user-action")
        buffer.apply_tag(tag, start, end)
        buffer.emit("end-user-action")
    else:
        pending_tags = {k: v for k, v in pending_tags.items() if not k.startswith("color-")}
        pending_tags[f"color-{hex_color}"] = True
        return pending_tags
    return pending_tags


def apply_pending_tags(buffer: Gtk.TextBuffer, pending_tags: dict, start_offset: int, end_offset: int):
    """Apply pending tags to a just-inserted text range."""
    if not pending_tags:
        return
    start = buffer.get_iter_at_offset(start_offset)
    end = buffer.get_iter_at_offset(end_offset)

    for tag_name in list(pending_tags.keys()):
        if tag_name.startswith("color-"):
            hex_color = tag_name[6:]
            tag = get_or_create_color_tag(buffer, hex_color)
        else:
            tag = buffer.get_tag_table().lookup(tag_name)
        if tag:
            buffer.apply_tag(tag, start, end)


def get_tags_at_iter(buffer: Gtk.TextBuffer, text_iter: Gtk.TextIter) -> dict:
    """Get active formatting tags at a position."""
    result = {}
    tags = text_iter.get_tags()
    for tag in tags:
        name = tag.get_property("name")
        if name is None:
            continue
        if name in ("bold", "italic", "underline", "strikethrough"):
            result[name] = True
        elif name.startswith("size-"):
            result[name] = True
        elif name.startswith("family-"):
            result[name] = True
        elif name.startswith("color-"):
            result[name] = True
    return result


def _selection_has_tag(buffer: Gtk.TextBuffer, tag: Gtk.TextTag, start: Gtk.TextIter, end: Gtk.TextIter) -> bool:
    """Check if the entire selection has a given tag."""
    it = start.copy()
    while it.compare(end) < 0:
        if not it.has_tag(tag):
            return False
        if not it.forward_char():
            break
    return True


def _remove_color_tags_in_range(buffer: Gtk.TextBuffer, start: Gtk.TextIter, end: Gtk.TextIter):
    """Remove all color-* tags in a range."""
    tag_table = buffer.get_tag_table()
    # Collect color tags
    color_tags = []
    def _collect(tag):
        name = tag.get_property("name")
        if name and name.startswith("color-"):
            color_tags.append(tag)
    tag_table.foreach(_collect)
    for tag in color_tags:
        buffer.remove_tag(tag, start, end)
