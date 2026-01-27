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


def classify_user_intent(user_message: str) -> dict:
    """
    Use LLM to classify user intent instead of keywords.
    Returns: {action_type: 'email'|'calendar'|'document'|'query'|'general', needs_rag: bool, reasoning: str}
    """
    if not settings.LM_USE_LOCAL_LM or not settings.LM_API_URL:
        # Fallback to simple heuristic
        msg_lower = user_message.lower()
        if any(w in msg_lower for w in ['correo', 'email', 'mail', 'mand']):
            return {'action_type': 'email', 'needs_rag': False, 'reasoning': 'Email keywords detected'}
        elif any(w in msg_lower for w in ['evento', 'calendario', 'agenda', 'cita']):
            return {'action_type': 'calendar', 'needs_rag': False, 'reasoning': 'Calendar keywords'}
        elif any(w in msg_lower for w in ['busca', 'quien es', 'dime', 'información']):
            return {'action_type': 'query', 'needs_rag': True, 'reasoning': 'Query detected'}
        else:
            return {'action_type': 'general', 'needs_rag': True, 'reasoning': 'Ambiguous query'}
    
    url_base = settings.LM_API_URL.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if getattr(settings, "LM_API_KEY", None):
        headers["Authorization"] = f"Bearer {settings.LM_API_KEY}"
    
    prompt = f"""Clasifica la intención en UNA palabra:

Petición: "{user_message}"

Categorías (responde SOLO la palabra clave):
- email (enviar/redactar correo)
- calendar (evento calendario)
- document (generar PDF/Excel)
- query (pregunta sobre personas/temas)
- general (conversación)

¿Necesita RAG? true si pregunta sobre personas/temas ("busca"/"quien es"/"dime sobre"). false para email/calendar/general.

JSON: {{"action_type": "email|calendar|document|query|general", "needs_rag": true|false}}"""
    
    try:
        chat_url = f"{url_base}/v1/chat/completions"
        payload = {
            "model": settings.LM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.1
        }
        j = _post_json(chat_url, payload, headers, timeout=8)
        text = _parse_response_json(j).strip()
        
        # Parse JSON from response
        import json
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(text)
        logger.info(f"🧠 LLM classified intent: {result}")
        return result
    except Exception as e:
        logger.warning(f"LLM intent classification failed: {e}, using fallback")
        msg_lower = user_message.lower()
        if 'busca' in msg_lower or 'quien' in msg_lower or 'dime' in msg_lower or '?' in user_message:
            return {'action_type': 'query', 'needs_rag': True, 'reasoning': 'Query fallback'}
        return {'action_type': 'general', 'needs_rag': False, 'reasoning': 'Fallback'}


def generate_response_with_context(
    user_message: str,
    tool_results: Optional[str] = None,
    rag_context: Optional[str] = None,
    current_date: Optional[str] = None,
    user_info: Optional[dict] = None,
    max_tokens: int = 300,
    temperature: float = 0.2
) -> str:
    """
    Generate a user-facing response using local LM, combining user message,
    tool results (e.g., calendar/email replies), RAG context snippets, and
    simple server-side metadata like current date.
    """
    if not settings.LM_USE_LOCAL_LM or not settings.LM_API_URL:
        raise RuntimeError("Local LM not configured")

    # Build a clear prompt with sections so the LM focuses on composing a
    # concise, helpful reply in Spanish.
    parts = []
    parts.append("Eres un asistente conversacional útil y conciso. Responde en español.")
    if current_date:
        parts.append(f"Fecha actual (servidor): {current_date}")
    if user_info and isinstance(user_info, dict):
        ui = user_info.get('name') or user_info.get('email') or None
        if ui:
            parts.append(f"Usuario: {ui}")

    parts.append("Contexto de la conversación (si existe):")
    if rag_context:
        parts.append(f"Información relevante extraída de documentos:\n{rag_context}")

    if tool_results:
        parts.append(f"Resultados de herramientas (calendario/correos u otros):\n{tool_results}")

    parts.append(f"Solicitud del usuario: {user_message}")

    prompt = "\n\n".join(parts)

    # Use the existing generate_summary_from_prompt helper to call the LM
    try:
        return generate_summary_from_prompt(prompt, max_tokens=max_tokens)
    except Exception as e:
        logger.exception(f"generate_response_with_context failed: {e}")
        # Bubble up a generic error for callers to handle
        raise
