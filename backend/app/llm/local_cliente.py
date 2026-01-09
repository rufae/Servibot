# backend/app/llm/local_client.py
import requests
from typing import List, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 12  # segundos

def _post_json(url: str, payload: dict, headers: dict, timeout: int = DEFAULT_TIMEOUT):
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def _parse_response_json(j: dict) -> str:
    # Varios formatos posibles: OpenAI-like choices/message, responses.output, text fields.
    if not j:
        return ""
    # OpenAI-like chat completions
    try:
        choices = j.get("choices")
        if choices and isinstance(choices, list):
            first = choices[0]
            # chat format
            msg = first.get("message") or first.get("delta")
            if msg:
                return msg.get("content") if isinstance(msg, dict) else str(msg)
            # completion format
            if first.get("text"):
                return first.get("text")
    except Exception:
        pass
    # LM Studio "responses" format (output)
    try:
        outputs = j.get("output") or j.get("outputs")
        if outputs and isinstance(outputs, list) and outputs:
            o = outputs[0]
            if isinstance(o, dict):
                # some servers put text under 'content' or 'text'
                if o.get("text"):
                    return o.get("text")
                if o.get("content"):
                    # content may be list
                    c = o.get("content")
                    if isinstance(c, list):
                        # join text items
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
    # Fallback: try top-level text keys
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

    # Try chat/completions first (OpenAI-like)
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

    # Fall back to /v1/responses or /v1/completions
    try:
        resp_url = f"{url_base}/v1/responses"
        payload = {"model": settings.LM_MODEL, "input": prompt, "max_tokens": max_tokens}
        j = _post_json(resp_url, payload, headers)
        txt = _parse_response_json(j)
        if txt:
            return txt.strip()
    except Exception as e:
        logger.debug(f"/v1/responses failed: {e}")

    # fallback: empty
    raise RuntimeError("Local LM did not return a valid response")

def summarize_texts(texts: List[str], max_tokens: int = 512, max_chars: int = 3000) -> Optional[str]:
    # Build prompt from top fragments, truncating to max_chars
    joined = "\n\n".join([t.strip() for t in texts if t])
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "..."
    prompt = f"Resume concisamente los siguientes fragmentos en español, indicando puntos clave:\n\n{joined}\n\nResumen:"
    try:
        return generate_summary_from_prompt(prompt, max_tokens=max_tokens)
    except Exception as e:
        logger.exception(f"Local LM summarize failed: {e}")
        return None