import logging
from typing import List, Optional
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 12


def _post_json(url: str, payload: dict, headers: dict, timeout: int = DEFAULT_TIMEOUT):
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _parse_response_json(j: dict) -> str:
    if not j:
        return ""
    try:
        choices = j.get("choices")
        if choices and isinstance(choices, list) and len(choices) > 0:
            first = choices[0]
            # chat format
            msg = first.get("message") or first.get("delta")
            if msg:
                if isinstance(msg, dict):
                    # content may be dict or string
                    content = msg.get("content")
                    if isinstance(content, dict):
                        return content.get("text") or ""
                    return content or ""
                return str(msg)
            if first.get("text"):
                return first.get("text")
    except Exception:
        pass

    try:
        outputs = j.get("output") or j.get("outputs")
        if outputs and isinstance(outputs, list) and outputs:
            o = outputs[0]
            if isinstance(o, dict):
                if o.get("text"):
                    return o.get("text")
                if o.get("content"):
                    c = o.get("content")
                    if isinstance(c, list):
                        texts = []
                        for item in c:
                            if isinstance(item, dict):
                                texts.append(item.get("text") or item.get("content") or "")
                            else:
                                texts.append(str(item))
                        return " ".join([t for t in texts if t])
                    return str(c)
    except Exception:
        pass

    for k in ("text", "generated_text", "result", "response"):
        if j.get(k):
            return j.get(k)
    return ""


def generate_summary_from_prompt(prompt: str, max_tokens: int = 512) -> str:
    if not settings.LM_USE_LOCAL_LM or not settings.LM_API_URL:
        raise RuntimeError("Local LM not configured")
    url_base = settings.LM_API_URL.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if getattr(settings, "LM_API_KEY", None):
        headers["Authorization"] = f"Bearer {settings.LM_API_KEY}"

    # Try chat/completions first
    try:
        chat_url = f"{url_base}/v1/chat/completions"
        payload = {
            "model": settings.LM_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un asistente que resume texto en español, conciso y claro."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2
        }
        j = _post_json(chat_url, payload, headers)
        txt = _parse_response_json(j)
        if txt:
            return txt.strip()
    except Exception as e:
        logger.debug(f"chat/completions failed: {e}")

    # Fallback to /v1/responses
    try:
        resp_url = f"{url_base}/v1/responses"
        payload = {"model": settings.LM_MODEL, "input": prompt, "max_tokens": max_tokens}
        j = _post_json(resp_url, payload, headers)
        txt = _parse_response_json(j)
        if txt:
            return txt.strip()
    except Exception as e:
        logger.debug(f"/v1/responses failed: {e}")

    raise RuntimeError("Local LM did not return a valid response")


def summarize_texts(texts: List[str], max_tokens: int = 512, max_chars: int = 3000) -> Optional[str]:
    joined = "\n\n".join([t.strip() for t in texts if t])
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "..."
    prompt = f"Resume concisamente los siguientes fragmentos en español, indicando puntos clave:\n\n{joined}\n\nResumen:"
    try:
        return generate_summary_from_prompt(prompt, max_tokens=max_tokens)
    except Exception as e:
        logger.exception(f"Local LM summarize failed: {e}")
        return None
