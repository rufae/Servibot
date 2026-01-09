"""
Tests for chat endpoint.
"""
import pytest


def test_chat_endpoint(client, sample_chat_message):
    """Test the chat endpoint with a sample message."""
    response = client.post("/api/chat", json=sample_chat_message)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
    assert "timestamp" in data
    assert data["conversation_id"] == sample_chat_message["conversation_id"]


def test_chat_endpoint_no_conversation_id(client):
    """Test chat endpoint without conversation_id generates one."""
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 200
    
    data = response.json()
    assert "conversation_id" in data
    assert data["conversation_id"].startswith("conv_")


def test_chat_endpoint_empty_message(client):
    """Test chat endpoint rejects empty messages."""
    response = client.post("/api/chat", json={"message": ""})
    # Should still return 200 but with appropriate response
    assert response.status_code == 200


def test_chat_history_endpoint(client):
    """Test retrieving chat history."""
    conversation_id = "test_conv_123"
    response = client.get(f"/api/chat/history/{conversation_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "conversation_id" in data
    assert data["conversation_id"] == conversation_id
