"""
Pytest configuration and fixtures for ServiBot tests.
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Make backend package importable (so `import app` works)
# Add the `backend` directory to sys.path (project root + '/backend')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

from backend.app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "message": "Help me organize my week",
        "conversation_id": "test_conv_123"
    }


@pytest.fixture
def sample_file_path(tmp_path):
    """Create a temporary test file."""
    test_file = tmp_path / "test_document.txt"
    test_file.write_text("This is a test document for ServiBot.")
    return test_file
