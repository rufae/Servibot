"""
Tests for Chat API endpoint
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestChatEndpoint:
    """Test suite for main chat endpoint."""
    
    def test_chat_basic_message(self):
        """Test basic chat message processing."""
        response = client.post(
            "/chat",
            json={"message": "Hola, ¿cómo estás?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "response" in data
        assert "conversation_id" in data
        assert "timestamp" in data
        assert "plan" in data
        assert "execution" in data
        assert "evaluation" in data
        
        # Validate types
        assert isinstance(data["response"], str)
        assert isinstance(data["plan"], list)
        assert isinstance(data["execution"], dict)
    
    def test_chat_with_context(self):
        """Test chat with additional context."""
        response = client.post(
            "/chat",
            json={
                "message": "Genera un informe",
                "context": {"user_id": "test123"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_chat_file_generation_intent(self):
        """Test chat with file generation intent (PDF/Excel)."""
        response = client.post(
            "/chat",
            json={"message": "Genera un PDF con la información"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have execution results
        assert data["execution"] is not None
        
        # May have generated_file if successful
        if "generated_file" in data and data["generated_file"]:
            assert "path" in data["generated_file"] or "filename" in data["generated_file"]
    
    def test_chat_rag_query_intent(self):
        """Test chat that should trigger RAG search."""
        response = client.post(
            "/chat",
            json={"message": "¿Qué información tienes sobre ServiBot?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have sources if documents are indexed
        assert "sources" in data
        # sources can be None, empty list, or populated list
        assert data["sources"] is None or isinstance(data["sources"], list)
    
    def test_chat_document_listing_intent(self):
        """Test chat asking about uploaded documents."""
        response = client.post(
            "/chat",
            json={"message": "¿Qué documentos tengo subidos?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a response about documents
        assert "response" in data
        assert isinstance(data["response"], str)
        # Response should mention documents or files
        assert any(word in data["response"].lower() for word in ["documento", "archivo", "fichero"])
    
    def test_chat_empty_message(self):
        """Test chat with empty message."""
        response = client.post(
            "/chat",
            json={"message": ""}
        )
        
        # Should handle gracefully
        # Either accept and return generic response or reject with 400
        assert response.status_code in [200, 400]
    
    def test_chat_conversation_id_persistence(self):
        """Test conversation ID persistence across messages."""
        # First message
        response1 = client.post(
            "/chat",
            json={"message": "Hola"}
        )
        
        assert response1.status_code == 200
        conv_id = response1.json()["conversation_id"]
        
        # Second message with same conversation ID
        response2 = client.post(
            "/chat",
            json={
                "message": "¿Cómo estás?",
                "conversation_id": conv_id
            }
        )
        
        assert response2.status_code == 200
        # Should maintain conversation ID
        assert response2.json()["conversation_id"] == conv_id


class TestChatAgentFlow:
    """Test suite for agent flow within chat."""
    
    def test_planner_execution(self):
        """Test that planner generates valid plans."""
        response = client.post(
            "/chat",
            json={"message": "Crea una nota sobre ServiBot"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Plan should exist and have subtasks
        assert data["plan"] is not None
        assert len(data["plan"]) > 0
        
        # Each subtask should have required fields
        for subtask in data["plan"]:
            assert "step" in subtask
            assert "action" in subtask
            assert "tool" in subtask
    
    def test_executor_results(self):
        """Test that executor returns results."""
        response = client.post(
            "/chat",
            json={"message": "Realiza una búsqueda"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Execution should have results
        assert data["execution"] is not None
        assert "results" in data["execution"]
        assert isinstance(data["execution"]["results"], list)
        
        # Each result should have status
        for result in data["execution"]["results"]:
            assert "status" in result
            assert result["status"] in ["success", "failed", "pending", "skipped"]
    
    def test_evaluator_assessment(self):
        """Test that evaluator provides assessment."""
        response = client.post(
            "/chat",
            json={"message": "Test task"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Evaluation should exist
        assert data["evaluation"] is not None
        # Should have some assessment fields
        assert any(key in data["evaluation"] for key in ["status", "score", "success", "summary"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
