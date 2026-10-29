"""API integration tests for FastAPI endpoints."""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_dashboard_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Apple Inc." in response.text


def test_quick_actions_endpoint():
    response = client.get("/api/v1/data/quick-actions")
    assert response.status_code == 200
    actions = response.json()
    assert isinstance(actions, list)
    assert len(actions) >= 4
    assert any(a["id"] == "profitability" for a in actions)


def test_kpi_summary_endpoint():
    response = client.get("/api/v1/data/kpi-summary?year=2025")
    assert response.status_code == 200
    kpi = response.json()
    assert "revenue_billion" in kpi
    assert "gross_margin_pct" in kpi
    assert "current_ratio" in kpi


def test_chat_feedback_endpoint():
    payload = {
        "session_id": "sess-test",
        "message_id": "msg-test",
        "feedback": "thumbs_up",
        "comment": "Accurate margin breakdown",
    }
    response = client.post("/api/v1/chat/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_chat_endpoint_structure():
    payload = {
        "message": "What was Apple's gross margin trend?",
        "year_filter": None,
        "chart_preference": "auto",
        "session_id": "test-session",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "answer" in res
    assert "sql_query" in res
    assert "confidence" in res
    assert "suggested_followups" in res
