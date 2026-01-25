"""
Intent Detection System
Determines user intent to route requests correctly and avoid RAG contamination
"""
from typing import Dict, List
import re
import logging

logger = logging.getLogger(__name__)


class IntentDetector:
    """Detects user intent from natural language queries."""
    
    # Keywords for different intents
    CREATE_KEYWORDS = [
        "genera", "crea", "crear", "generar", "escribe", "escribir",
        "haz un", "hacer un", "hazme", "redacta", "redactar",
        "prepara", "preparar", "construye", "construir"
    ]
    
    QUERY_DOCUMENT_KEYWORDS = [
        "según el", "segun el", "en el archivo", "en el documento",
        "qué dice el", "que dice el", "busca en", "encuentra en",
        "lee el", "revisa el", "consulta el", "dime que dice"
    ]
    
    SELF_REFERENCE_KEYWORDS = [
        "quién eres", "quien eres", "qué eres", "que eres",
        "qué puedes hacer", "que puedes hacer", "tus capacidades",
        "preséntate", "presentate", "explica quién eres", "explica quien eres",
        "cuéntame sobre ti", "cuentame sobre ti", "háblame de ti", "hablame de ti"
    ]
    
    EMAIL_KEYWORDS = [
        "envía un correo", "envia un correo", "enviar email",
        "manda un email", "mandar correo", "escribe un email",
        "redacta un correo", "correo a", "email a"
    ]
    
    CALENDAR_KEYWORDS = [
        "crea un evento", "crear evento", "agenda", "agendar",
        "añade a mi calendario", "anade a mi calendario",
        "programa una reunión", "programar reunion",
        "recordatorio", "cita"
    ]
    
    def detect_intent(self, message: str) -> Dict[str, any]:
        """
        Detect user intent from message.
        
        Args:
            message: User's message
            
        Returns:
            Dict with:
                - intent: primary intent ('create', 'query_docs', 'self_reference', 'action', 'general')
                - needs_rag: whether to query RAG system
                - confidence: confidence score (0-1)
                - action_type: specific action if detected ('email', 'calendar', 'document', None)
        """
        msg_lower = message.lower()
        
        # Check for self-reference (highest priority - no RAG)
        if self._contains_keywords(msg_lower, self.SELF_REFERENCE_KEYWORDS):
            logger.info(f"Intent detected: SELF_REFERENCE")
            return {
                "intent": "self_reference",
                "needs_rag": False,
                "confidence": 0.95,
                "action_type": None,
                "reasoning": "User asking about ServiBot itself"
            }
        
        # Check for creation intent (generate/create)
        is_creation = self._contains_keywords(msg_lower, self.CREATE_KEYWORDS)
        
        # Check for document query intent
        has_doc_query_keywords = self._contains_keywords(msg_lower, self.QUERY_DOCUMENT_KEYWORDS)
        
        # Check for specific actions
        is_email = self._contains_keywords(msg_lower, self.EMAIL_KEYWORDS)
        is_calendar = self._contains_keywords(msg_lower, self.CALENDAR_KEYWORDS)
        
        # Decision tree
        if is_creation:
            # User wants to CREATE something
            if is_email:
                action_type = "email"
            elif is_calendar:
                action_type = "calendar"
            elif any(kw in msg_lower for kw in ["pdf", "documento", "archivo", "excel", "informe", "reporte"]):
                action_type = "document"
            else:
                action_type = None
            
            # For creation, only use RAG if explicitly asking to base it on existing docs
            needs_rag = has_doc_query_keywords or self._mentions_specific_file(msg_lower)
            
            logger.info(f"Intent detected: CREATE (action_type={action_type}, needs_rag={needs_rag})")
            return {
                "intent": "create",
                "needs_rag": needs_rag,
                "confidence": 0.9,
                "action_type": action_type,
                "reasoning": f"Creation intent detected with action type: {action_type}"
            }
        
        if has_doc_query_keywords or self._mentions_specific_file(msg_lower):
            # User explicitly asking about document content
            logger.info(f"Intent detected: QUERY_DOCS")
            return {
                "intent": "query_docs",
                "needs_rag": True,
                "confidence": 0.95,
                "action_type": None,
                "reasoning": "Explicit document query detected"
            }
        
        if is_email or is_calendar:
            # Action without document context
            logger.info(f"Intent detected: ACTION (email={is_email}, calendar={is_calendar})")
            return {
                "intent": "action",
                "needs_rag": False,
                "confidence": 0.85,
                "action_type": "email" if is_email else "calendar",
                "reasoning": "Action intent without document context"
            }
        
        # General query - decide based on heuristics
        # If message is very short or question-like, probably doesn't need RAG
        if len(msg_lower.split()) < 10 and ("?" in message or any(q in msg_lower for q in ["qué", "que", "cuál", "cual", "cómo", "como", "cuándo", "cuando"])):
            logger.info(f"Intent detected: GENERAL (short query, no RAG)")
            return {
                "intent": "general",
                "needs_rag": False,
                "confidence": 0.7,
                "action_type": None,
                "reasoning": "Short general query"
            }
        
        # Default: general with optional RAG
        logger.info(f"Intent detected: GENERAL (ambiguous, allow RAG)")
        return {
            "intent": "general",
            "needs_rag": False,  # Conservative: don't contaminate unless clearly needed
            "confidence": 0.6,
            "action_type": None,
            "reasoning": "Ambiguous intent, defaulting to no RAG"
        }
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        return any(kw in text for kw in keywords)
    
    def _mentions_specific_file(self, text: str) -> bool:
        """Check if text mentions a specific filename."""
        # Look for common file extensions
        file_patterns = [
            r'\b\w+\.pdf\b',
            r'\b\w+\.docx?\b',
            r'\b\w+\.xlsx?\b',
            r'\b\w+\.txt\b',
            r'\b\w+\.csv\b'
        ]
        for pattern in file_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


# Singleton instance
_intent_detector = None

def get_intent_detector() -> IntentDetector:
    """Get or create the global intent detector instance."""
    global _intent_detector
    if _intent_detector is None:
        _intent_detector = IntentDetector()
    return _intent_detector
