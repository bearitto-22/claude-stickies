"""Rich text serialization: TextBuffer <-> JSON runs."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from .formatting import (
    get_or_create_color_tag, DEFAULT_FONT_SIZE, DEFAULT_FONT_FAMILY,
    FONT_SIZES, FONT_FAMILIES,
)


def serialize_buffer(buffer: Gtk.TextBuffer) -> list[dict]:
    """Serialize a TextBuffer's content into a list of styled runs."""
    runs = []
    start = buffer.get_start_iter()
    end = buffer.get_end_iter()

    if start.equal(end):
        return []

    it = start.copy()
    while it.compare(end) < 0:
        # Find next tag boundary
        next_it = it.copy()
        next_it.forward_to_tag_toggle(None)
        if next_it.compare(end) > 0:
            next_it = end.copy()

        # If no progress, move forward one char to avoid infinite loop
        if it.equal(next_it):
            if not next_it.forward_char():
                next_it = end.copy()

        text = buffer.get_text(it, next_it, True)
        if text:
            run = {"text": text}

            # Collect tags at this position
            tags = it.get_tags()
            for tag in tags:
                name = tag.get_property("name")
                if name is None:
                    continue
                if name == "bold":
                    run["bold"] = True
                elif name == "italic":
                    run["italic"] = True
                elif name == "underline":
                    run["underline"] = True
                elif name == "strikethrough":
                    run["strikethrough"] = True
                elif name.startswith("size-"):
                    try:
                        run["size"] = int(name[5:])
                    except ValueError:
                        pass
                elif name.startswith("family-"):
                    run["family"] = name[7:]
                elif name.startswith("color-"):
                    run["color"] = name[6:]

            runs.append(run)

        it = next_it

    # Merge adjacent runs with identical formatting
    return _merge_runs(runs)


def deserialize_to_buffer(buffer: Gtk.TextBuffer, runs: list[dict]):
    """Restore styled runs into a TextBuffer."""
    buffer.set_text("")
    for run in runs:
        text = run.get("text", "")
        if not text:
            continue

        # Insert text
        end = buffer.get_end_iter()
        offset_before = end.get_offset()
        buffer.insert(end, text)

        # Apply tags
        start_iter = buffer.get_iter_at_offset(offset_before)
        end_iter = buffer.get_end_iter()

        if run.get("bold"):
            tag = buffer.get_tag_table().lookup("bold")
            if tag:
                buffer.apply_tag(tag, start_iter, end_iter)

        if run.get("italic"):
            tag = buffer.get_tag_table().lookup("italic")
            if tag:
                buffer.apply_tag(tag, start_iter, end_iter)

        if run.get("underline"):
            tag = buffer.get_tag_table().lookup("underline")
            if tag:
                buffer.apply_tag(tag, start_iter, end_iter)

        if run.get("strikethrough"):
            tag = buffer.get_tag_table().lookup("strikethrough")
            if tag:
                buffer.apply_tag(tag, start_iter, end_iter)

        if "size" in run:
            tag = buffer.get_tag_table().lookup(f"size-{run['size']}")
            if tag:
                buffer.apply_tag(tag, start_iter, end_iter)

        if "family" in run:
            tag = buffer.get_tag_table().lookup(f"family-{run['family']}")
            if tag:
                buffer.apply_tag(tag, start_iter, end_iter)

        if "color" in run:
            tag = get_or_create_color_tag(buffer, run["color"])
            buffer.apply_tag(tag, start_iter, end_iter)


def _merge_runs(runs: list[dict]) -> list[dict]:
    """Merge adjacent runs with identical formatting."""
    if not runs:
        return []
    merged = [runs[0]]
    for run in runs[1:]:
        prev = merged[-1]
        # Compare formatting (everything except text)
        prev_fmt = {k: v for k, v in prev.items() if k != "text"}
        curr_fmt = {k: v for k, v in run.items() if k != "text"}
        if prev_fmt == curr_fmt:
            prev["text"] += run["text"]
        else:
            merged.append(run)
    return merged
