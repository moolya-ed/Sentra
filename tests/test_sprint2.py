import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure app is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import get_db
from app import models

# Setup In-Memory SQLite DB for Sprint 2
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
models.Base.metadata.create_all(bind=engine)

# Override dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# -------------------------------
# 🔍 SPRINT 2: Alert Tests
# -------------------------------

def test_spike_detection_alert():
    ip = "192.168.1.100"
    for _ in range(6):  # Trigger spike (threshold is 5)
        payload = {
            "source_ip": ip,
            "method": "GET",
            "url": "/home",
            "headers": "{\"User-Agent\": \"TestAgent\"}",
            "user_agent": "TestAgent",
            "request_size": 100,
            "response_code": 200,
            "response_time_ms": 40
        }
        client.post("/traffic/log", json=payload)

    response = client.get("/analytics/traffic-summary")
    assert response.status_code == 200
    recent_alerts = response.json().get("recent_alerts", [])
    assert any("Traffic Spike" in alert["type"] for alert in recent_alerts)


def test_suspicious_user_agent_alert():
    payload = {
        "source_ip": "192.168.1.101",
        "method": "GET",
        "url": "/status",
        "headers": "{\"User-Agent\": \"sqlmap\"}",
        "user_agent": "sqlmap",
        "request_size": 80,
        "response_code": 403,
        "response_time_ms": 70
    }
    response = client.post("/traffic/log", json=payload)
    assert response.status_code == 200
    assert "Detected suspicious agent" in response.json()["alerts_triggered"][0]


def test_sensitive_url_access_alert():
    payload = {
        "source_ip": "192.168.1.102",
        "method": "GET",
        "url": "/admin",
        "headers": "{\"User-Agent\": \"Mozilla\"}",
        "user_agent": "Mozilla",
        "request_size": 90,
        "response_code": 403,
        "response_time_ms": 60
    }
    response = client.post("/traffic/log", json=payload)
    assert response.status_code == 200
    assert "Attempted access" in response.json()["alerts_triggered"][0]


def test_alerts_in_traffic_summary():
    response = client.get("/analytics/traffic-summary")
    assert response.status_code == 200
    alerts = response.json().get("recent_alerts", [])
    assert isinstance(alerts, list)
    assert len(alerts) >= 1
