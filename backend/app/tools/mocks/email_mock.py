"""Mock email tool for ServiBot.
Stores sent emails into a local JSON file under MOCK_OUTPUT_DIR.
"""
from datetime import datetime
import json
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

EMAILS_FILE = os.path.join(settings.MOCK_OUTPUT_DIR, "sent_emails.json")


def _ensure_dir():
    os.makedirs(settings.MOCK_OUTPUT_DIR, exist_ok=True)


def send_email(to: str, subject: str, body: str, from_email: str = "servibot@example.local") -> dict:
    """Simulate sending an email and persist record locally.

    Returns a dict with message id and status.
    """
    _ensure_dir()
    message_id = f"msg_{int(datetime.utcnow().timestamp())}"
    record = {
        "id": message_id,
        "to": to,
        "from": from_email,
        "subject": subject,
        "body": body,
        "sent_at": datetime.utcnow().isoformat()
    }

    try:
        if os.path.exists(EMAILS_FILE):
            with open(EMAILS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(record)
        with open(EMAILS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to write mock email: {e}")

    logger.info(f"Mock email sent: {message_id} to {to}")
    return {"id": message_id, "status": "sent"}
