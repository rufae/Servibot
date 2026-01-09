"""
Tests for main API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Test the root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ServiBot API"
    assert data["version"] == "0.1.0"
    assert "docs" in data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "system" in data


def test_readiness_check(client):
    """Test the readiness check endpoint."""
    response = client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] == True
    assert "timestamp" in data
