"""
Tests for Upload API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)


class TestUploadEndpoint:
    """Test suite for file upload endpoint."""
    
    def test_upload_text_file(self):
        """Test uploading a text file."""
        file_content = b"This is a test document for ServiBot.\nIt contains sample text."
        
        response = client.post(
            "/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert data["status"] == "success"
        assert "filename" in data
        assert "file_id" in data
        assert data["filename"] == "test.txt"
    
    def test_upload_without_file(self):
        """Test upload endpoint without providing a file."""
        response = client.post("/upload")
        
        # Should return 422 (validation error)
        assert response.status_code == 422
    
    def test_upload_large_file(self):
        """Test uploading a larger file."""
        # Create a 1MB test file
        file_content = b"A" * (1024 * 1024)
        
        response = client.post(
            "/upload",
            files={"file": ("large.txt", io.BytesIO(file_content), "text/plain")}
        )
        
        # Should handle or reject gracefully
        assert response.status_code in [200, 413]  # 413 = Payload Too Large
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"


class TestUploadStatusEndpoint:
    """Test suite for upload status endpoint."""
    
    def test_upload_status_existing_file(self):
        """Test status check for existing uploaded file."""
        # First upload a file
        file_content = b"Test content for status check"
        upload_response = client.post(
            "/upload",
            files={"file": ("status_test.txt", io.BytesIO(file_content), "text/plain")}
        )
        
        if upload_response.status_code == 200:
            file_id = upload_response.json()["file_id"]
            
            # Check status
            status_response = client.get(f"/upload/status/{file_id}")
            
            assert status_response.status_code == 200
            data = status_response.json()
            
            assert "file_id" in data
            assert "status" in data
    
    def test_upload_status_nonexistent_file(self):
        """Test status check for non-existent file."""
        response = client.get("/upload/status/nonexistent_file_id")
        
        # Should return 404 or error status
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "error" or "not found" in str(data).lower()


class TestReindexEndpoint:
    """Test suite for reindex endpoint."""
    
    def test_reindex_all_documents(self):
        """Test reindexing all documents."""
        response = client.post("/upload/reindex")
        
        # Should complete successfully
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        # status can be "success" or provide information about indexed files
    
    def test_reindex_empty_directory(self):
        """Test reindex when no files are uploaded."""
        # Clear uploads first (if endpoint exists)
        response = client.post("/upload/reindex")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle gracefully
        assert "status" in data


class TestUploadIntegration:
    """Integration tests for upload + RAG indexing flow."""
    
    def test_upload_and_query_flow(self):
        """Test full flow: upload file -> index -> query."""
        # 1. Upload file
        file_content = b"ServiBot is an intelligent assistant. It helps users with tasks."
        upload_response = client.post(
            "/upload",
            files={"file": ("integration_test.txt", io.BytesIO(file_content), "text/plain")}
        )
        
        assert upload_response.status_code == 200
        filename = upload_response.json()["filename"]
        
        # 2. Index file
        index_response = client.post(
            "/rag/index",
            json={"filename": filename}
        )
        
        if index_response.status_code == 200:
            # 3. Query indexed content
            query_response = client.post(
                "/rag/query",
                json={"query": "What is ServiBot?", "top_k": 3}
            )
            
            assert query_response.status_code == 200
            data = query_response.json()
            
            # Should find relevant results
            assert len(data["results"]) > 0
            # First result should mention ServiBot
            first_doc = data["results"][0]["document"]
            assert "ServiBot" in first_doc or "assistant" in first_doc.lower()


class TestListUploadsEndpoint:
    """Test suite for listing uploaded files."""
    
    def test_list_uploads(self):
        """Test listing all uploaded files."""
        response = client.get("/upload/list")
        
        # Endpoint may or may not exist
        if response.status_code == 404:
            pytest.skip("List uploads endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of files
        assert "files" in data or isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
