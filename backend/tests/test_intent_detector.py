"""
Tests for Intent Detection System
"""
import pytest
from app.agent.intent_detector import IntentDetector, get_intent_detector


class TestIntentDetector:
    """Test suite for IntentDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create intent detector instance."""
        return IntentDetector()
    
    # ==================== SELF REFERENCE TESTS ====================
    
    def test_self_reference_quien_eres(self, detector):
        """Test self-reference detection for '¿Quién eres?'"""
        result = detector.detect_intent("¿Quién eres?")
        assert result["intent"] == "self_reference"
        assert result["needs_rag"] == False
        assert result["confidence"] > 0.9
    
    def test_self_reference_que_puedes_hacer(self, detector):
        """Test self-reference detection for capabilities question."""
        result = detector.detect_intent("¿Qué puedes hacer por mí?")
        assert result["intent"] == "self_reference"
        assert result["needs_rag"] == False
    
    def test_self_reference_presentate(self, detector):
        """Test self-reference detection for introduction request."""
        result = detector.detect_intent("Preséntate")
        assert result["intent"] == "self_reference"
        assert result["needs_rag"] == False
    
    # ==================== CREATION TESTS ====================
    
    def test_create_pdf_no_rag(self, detector):
        """Test PDF creation without RAG contamination."""
        result = detector.detect_intent("Genera un PDF explicándome quién eres")
        assert result["intent"] == "create"
        assert result["needs_rag"] == False  # KEY: Should NOT activate RAG
        assert result["action_type"] == "document"
        assert result["confidence"] > 0.85
    
    def test_create_pdf_with_rag(self, detector):
        """Test PDF creation that SHOULD use RAG."""
        result = detector.detect_intent("Genera un PDF con la información del documento laura.txt")
        assert result["intent"] == "create"
        assert result["needs_rag"] == True  # Should activate RAG here
        assert result["action_type"] == "document"
    
    def test_create_email(self, detector):
        """Test email creation detection."""
        result = detector.detect_intent("Envía un correo a juan@ejemplo.com diciéndole hola")
        assert result["intent"] == "create"
        assert result["action_type"] == "email"
        assert result["needs_rag"] == False
    
    def test_create_calendar_event(self, detector):
        """Test calendar event creation."""
        result = detector.detect_intent("Crea un evento mañana a las 10am llamado Reunión")
        assert result["intent"] == "create"
        assert result["action_type"] == "calendar"
        assert result["needs_rag"] == False
    
    def test_create_report(self, detector):
        """Test document creation."""
        result = detector.detect_intent("Genera un informe de ventas del mes pasado")
        assert result["intent"] == "create"
        assert result["action_type"] == "document"
    
    # ==================== DOCUMENT QUERY TESTS ====================
    
    def test_query_document_explicit(self, detector):
        """Test explicit document query."""
        result = detector.detect_intent("¿Qué dice el archivo laura.txt?")
        assert result["intent"] == "query_docs"
        assert result["needs_rag"] == True
        assert result["confidence"] > 0.9
    
    def test_query_document_segun_el(self, detector):
        """Test document query with 'según el'."""
        result = detector.detect_intent("Según el documento, ¿cuál es la fecha límite?")
        assert result["intent"] == "query_docs"
        assert result["needs_rag"] == True
    
    def test_query_document_busca_en(self, detector):
        """Test document search request."""
        result = detector.detect_intent("Busca en mis documentos información sobre contratos")
        assert result["intent"] == "query_docs"
        assert result["needs_rag"] == True
    
    def test_query_specific_file_pdf(self, detector):
        """Test query mentioning specific PDF file."""
        result = detector.detect_intent("Resume el contrato_alquiler.pdf")
        assert result["intent"] == "query_docs"
        assert result["needs_rag"] == True
    
    # ==================== ACTION TESTS ====================
    
    def test_action_email_send(self, detector):
        """Test email send action."""
        result = detector.detect_intent("Envía un email a juan diciéndole que la reunión es mañana")
        assert result["intent"] in ["create", "action"]
        assert result["action_type"] == "email"
    
    def test_action_calendar_list(self, detector):
        """Test calendar list action."""
        result = detector.detect_intent("Muéstrame mis eventos de hoy")
        # Could be 'action' or 'general', but should NOT need RAG
        assert result["needs_rag"] == False
    
    # ==================== GENERAL QUERY TESTS ====================
    
    def test_general_short_question(self, detector):
        """Test short general question."""
        result = detector.detect_intent("¿Qué día es hoy?")
        assert result["intent"] == "general"
        assert result["needs_rag"] == False
        assert result["action_type"] is None
    
    def test_general_greeting(self, detector):
        """Test greeting."""
        result = detector.detect_intent("Hola, ¿cómo estás?")
        # Should be general, no RAG
        assert result["needs_rag"] == False
    
    def test_general_ambiguous(self, detector):
        """Test ambiguous query."""
        result = detector.detect_intent("Ayúdame con mis tareas")
        assert result["intent"] == "general"
        # Conservative: no RAG unless clearly needed
        assert result["needs_rag"] == False
    
    # ==================== EDGE CASES ====================
    
    def test_empty_message(self, detector):
        """Test empty message handling."""
        result = detector.detect_intent("")
        assert result["intent"] == "general"
        assert result["needs_rag"] == False
    
    def test_very_long_message(self, detector):
        """Test very long message."""
        long_msg = "Genera un informe " + "muy detallado " * 50 + "sobre el proyecto"
        result = detector.detect_intent(long_msg)
        assert result["intent"] == "create"
    
    def test_mixed_intents_create_priority(self, detector):
        """Test that creation intent has priority over query."""
        # This should be 'create' not 'query_docs' despite 'archivo'
        result = detector.detect_intent("Genera un archivo PDF con mi información")
        assert result["intent"] == "create"
        assert result["needs_rag"] == False  # No explicit doc reference
    
    def test_mixed_self_reference_priority(self, detector):
        """Test that self-reference has highest priority."""
        # Even if it mentions documents, self-ref wins
        result = detector.detect_intent("¿Quién eres y qué documentos puedes leer?")
        assert result["intent"] == "self_reference"
        assert result["needs_rag"] == False
    
    # ==================== SINGLETON TEST ====================
    
    def test_get_intent_detector_singleton(self):
        """Test that get_intent_detector returns singleton."""
        detector1 = get_intent_detector()
        detector2 = get_intent_detector()
        assert detector1 is detector2


# Run with: pytest tests/test_intent_detector.py -v
