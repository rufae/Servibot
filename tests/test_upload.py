"""
Tests for upload endpoint.
"""
import pytest
from io import BytesIO


def test_upload_endpoint_txt_file(client):
    """Test uploading a text file."""
    file_content = b"This is a test document."
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
    
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "filename" in data
    assert "file_id" in data


def test_upload_endpoint_pdf_file(client):
    """Test uploading a PDF file."""
    # Create minimal PDF-like content
    file_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["file_type"] == ".pdf"


def test_upload_endpoint_unsupported_file(client):
    """Test uploading an unsupported file type."""
    file_content = b"test content"
    files = {"file": ("test.exe", BytesIO(file_content), "application/x-msdownload")}
    
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400


def test_upload_status_endpoint(client):
    """Test the upload status endpoint."""
    file_id = "test_file_123"
    response = client.get(f"/api/upload/status/{file_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "file_id" in data
    assert data["file_id"] == file_id


def test_list_uploaded_files(client):
    """Test listing uploaded files."""
    response = client.get("/api/upload/list")
    assert response.status_code == 200
    
    data = response.json()
    assert "count" in data
    assert "files" in data
    assert isinstance(data["files"], list)
