"""JSON persistence for notes."""

import json
import os
from pathlib import Path
from .models import Note

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "claude-stickies"
NOTES_FILE = CONFIG_DIR / "notes.json"


def load_notes() -> list[Note]:
    """Load all notes from disk."""
    if not NOTES_FILE.exists():
        return []
    try:
        data = json.loads(NOTES_FILE.read_text())
        return [Note.from_dict(n) for n in data]
    except (json.JSONDecodeError, KeyError):
        return []


def save_notes(notes: list[Note]):
    """Save all notes to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = [n.to_dict() for n in notes]
    NOTES_FILE.write_text(json.dumps(data, indent=2))
