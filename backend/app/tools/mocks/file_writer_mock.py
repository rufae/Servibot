"""Mock file writer tool for ServiBot.
Writes simple text/PDF placeholders to MOCK_OUTPUT_DIR and returns path.
"""
from datetime import datetime
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _ensure_dir():
    os.makedirs(settings.MOCK_OUTPUT_DIR, exist_ok=True)


def write_file(content: str, filename: str = None) -> dict:
    _ensure_dir()
    if not filename:
        filename = f"export_{int(datetime.utcnow().timestamp())}.txt"
    path = os.path.join(settings.MOCK_OUTPUT_DIR, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to write mock file: {e}")
        return {"status": "error", "message": str(e)}

    logger.info(f"Mock file written: {path}")
    return {"status": "success", "path": path}
