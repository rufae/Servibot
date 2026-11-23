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


def test_upload_status_endpoint_unknown_returns_404(client):
    """Un id sin registrar devuelve 404 con detalle legible."""
    response = client.get("/api/upload/status/test_file_123")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_upload_status_endpoint_returns_registered_status(client):
    """Con el estado registrado devuelve la ficha completa del archivo."""
    from app.api import upload as upload_api

    upload_api.UPLOAD_STATUS["test_file_123"] = {
        "status": "completed",
        "message": "ok",
        "attempts": 1,
        "debug": {},
    }
    response = client.get("/api/upload/status/test_file_123")
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == "test_file_123"
    assert data["status"] == "completed"


def test_list_uploaded_files(client):
    """Test listing uploaded files."""
    response = client.get("/api/upload/list")
    assert response.status_code == 200
    
    data = response.json()
    assert "count" in data
    assert "files" in data
    assert isinstance(data["files"], list)
