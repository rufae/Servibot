"""Mock notes tool for ServiBot.
Stores created notes into a local JSON file under MOCK_OUTPUT_DIR.
"""
from datetime import datetime
import json
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

NOTES_FILE = os.path.join(settings.MOCK_OUTPUT_DIR, "notes.json")


def _ensure_dir():
    os.makedirs(settings.MOCK_OUTPUT_DIR, exist_ok=True)


def create_note(title: str, content: str, tags: list[str] | None = None) -> dict:
    _ensure_dir()
    note_id = f"note_{int(datetime.utcnow().timestamp())}"
    note = {
        "id": note_id,
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(note)
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to write mock note: {e}")

    logger.info(f"Mock note created: {note_id}")
    return note
