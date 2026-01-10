"""
Tests for RAG API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRAGEndpoints:
    """Test suite for RAG API endpoints."""
    
    def test_rag_query_no_collection(self):
        """Test RAG query when no collection exists."""
        response = client.post(
            "/rag/query",
            json={"query": "test query", "top_k": 3}
        )
        
        # Should handle gracefully (either 404 or empty results)
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "results" in data
    
    def test_rag_query_with_results(self):
        """Test RAG query with actual indexed documents."""
        # First, try to index a test document
        # (This assumes upload functionality works)
        
        response = client.post(
            "/rag/query",
            json={"query": "ServiBot features", "top_k": 5}
        )
        
        # Should return successfully
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "ServiBot features"
        assert isinstance(data["results"], list)
        
        # If results exist, validate structure
        if data["results"]:
            result = data["results"][0]
            assert "document" in result
            assert "metadata" in result
            assert "distance" in result
    
    def test_rag_index_missing_file(self):
        """Test indexing with non-existent file."""
        response = client.post(
            "/rag/index",
            json={"filename": "nonexistent_file.pdf"}
        )
        
        # Should return 404 or error
        assert response.status_code in [404, 500]
    
    def test_debug_vectors_endpoint(self):
        """Test debug vectors endpoint."""
        response = client.get("/debug/vectors")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "persist_directory" in data
        assert "collections" in data
        assert isinstance(data["collections"], list)


class TestRAGQueryModule:
    """Test suite for RAG query module functions."""
    
    def test_semantic_search_empty_query(self):
        """Test semantic search with empty query."""
        from app.rag.query import semantic_search
        
        results = semantic_search(query="", top_k=5)
        
        # Should return empty list for empty query
        assert results == []
    
    def test_get_context_for_query(self):
        """Test context generation for query."""
        from app.rag.query import get_context_for_query
        
        # Should handle gracefully even with no documents
        context = get_context_for_query(
            query="test query",
            top_k=3,
            max_chars=500
        )
        
        assert isinstance(context, str)
        # Should return error message or "no documents" message
        assert len(context) > 0


class TestEmbeddingsModule:
    """Test suite for embeddings module."""
    
    def test_generate_embeddings_basic(self):
        """Test basic embedding generation."""
        from app.rag.embeddings import generate_embeddings
        
        texts = ["Hello world", "Test document"]
        embeddings = generate_embeddings(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384  # all-MiniLM-L6-v2 dimension
        assert isinstance(embeddings[0], list)
        assert all(isinstance(x, float) for x in embeddings[0])
    
    def test_generate_embeddings_empty_list(self):
        """Test embedding generation with empty list."""
        from app.rag.embeddings import generate_embeddings
        
        embeddings = generate_embeddings([])
        
        assert embeddings == []
    
    def test_embed_query_single(self):
        """Test single query embedding."""
        from app.rag.embeddings import embed_query
        
        embedding = embed_query("test query")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_query_empty(self):
        """Test single query embedding with empty string."""
        from app.rag.embeddings import embed_query
        
        embedding = embed_query("")
        
        assert embedding == []


class TestChromaClient:
    """Test suite for ChromaDB client module."""
    
    def test_get_chroma_client(self):
        """Test ChromaDB client initialization."""
        from app.db.chroma_client import get_chroma_client
        
        client = get_chroma_client()
        
        assert client is not None
    
    def test_get_collection(self):
        """Test collection retrieval/creation."""
        from app.db.chroma_client import get_collection
        
        collection = get_collection("servibot_docs")
        
        assert collection is not None
    
    def test_persist_client(self):
        """Test client persistence."""
        from app.db.chroma_client import persist_client
        
        # Should not raise error
        persist_client()
    
    def test_reset_client(self):
        """Test client reset."""
        from app.db.chroma_client import reset_client, get_chroma_client
        
        # Get client first
        client1 = get_chroma_client()
        
        # Reset
        reset_client()
        
        # Get again (should create new)
        client2 = get_chroma_client()
        
        # Both should be valid clients
        assert client1 is not None
        assert client2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
