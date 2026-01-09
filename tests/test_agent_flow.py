from fastapi.testclient import TestClient
from backend.app.main import app


def test_chat_plan_execute_evaluate():
    client = TestClient(app)

    payload = {
        "message": "Por favor, crea una nota de prueba y envíame un recordatorio.",
        "context": {}
    }

    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Basic structure checks
    assert "plan" in data
    assert isinstance(data["plan"], list)
    assert "execution" in data
    assert isinstance(data["execution"], dict)
    assert "evaluation" in data
    assert isinstance(data["evaluation"], dict)
