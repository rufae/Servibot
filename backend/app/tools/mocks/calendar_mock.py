"""Mock calendar tool for ServiBot.
Stores created events into a local JSON file under MOCK_OUTPUT_DIR.
"""
from datetime import datetime
import json
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

EVENTS_FILE = os.path.join(settings.MOCK_OUTPUT_DIR, "calendar_events.json")


def _ensure_dir():
    os.makedirs(settings.MOCK_OUTPUT_DIR, exist_ok=True)


def create_event(title: str, start_time: str, duration_minutes: int = 60, description: str = "") -> dict:
    """Create a mock calendar event and persist to local file.

    Returns a dict with event id and details.
    """
    _ensure_dir()
    event_id = f"evt_{int(datetime.utcnow().timestamp())}"
    event = {
        "id": event_id,
        "title": title,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(event)
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to write mock event: {e}")

    logger.info(f"Mock calendar event created: {event_id}")
    return event
