import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models, crud, database
from app.main import app, get_db

# -------------------------------
# ✅ 1️⃣ Use file-based SQLite
# -------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Remove leftover test DB
if os.path.exists("test.db"):
    os.remove("test.db")

# Create engine & test session
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Make sure all modules share this session
database.SessionLocal = TestingSessionLocal
crud.SessionLocal = TestingSessionLocal

# Create all tables
models.Base.metadata.create_all(bind=engine)

# -------------------------------
# ✅ 2️⃣ Override FastAPI DB dependency
# -------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# -------------------------------
# ✅ 3️⃣ Sprint 1: System & Logging
# -------------------------------
def test_system_status():
    res = client.get("/system/status?service=api")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_log_traffic():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.10",
        "method": "GET",
        "url": "/home",
        "headers": "test",
        "user_agent": "normal",
        "request_size": 50,
        "response_code": 200,
        "response_time_ms": 30
    })
    assert res.status_code == 200
    assert res.json()["message"] == "Traffic logged"

def test_traffic_summary():
    res = client.get("/analytics/traffic-summary")
    assert res.status_code == 200
    assert "total_requests" in res.json()

# -------------------------------
# ✅ 4️⃣ Sprint 2: Alerts
# -------------------------------
def test_suspicious_agent_alert():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.11",
        "method": "GET",
        "url": "/home",
        "headers": "test",
        "user_agent": "sqlmap",
        "request_size": 20,
        "response_code": 200,
        "response_time_ms": 25
    })
    data = res.json()
    assert res.status_code == 200
    assert any("sqlmap" in alert for alert in data["alerts_triggered"])

def test_sensitive_url_alert():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.12",
        "method": "GET",
        "url": "/admin",
        "headers": "test",
        "user_agent": "normal",
        "request_size": 10,
        "response_code": 200,
        "response_time_ms": 20
    })
    data = res.json()
    assert res.status_code == 200
    assert any("/admin" in alert for alert in data["alerts_triggered"])

# -------------------------------
# ✅ 5️⃣ Sprint 3: Spike Detection & Block
# -------------------------------
def test_spike_blocking():
    for _ in range(105):
        res = client.post("/traffic/log", json={
            "source_ip": "192.168.1.13",
            "method": "GET",
            "url": "/home",
            "headers": "test",
            "user_agent": "normal",
            "request_size": 10,
            "response_code": 200,
            "response_time_ms": 10
        })
        assert res.status_code == 200

    # Confirm blocked
    res = client.get("/blocked-ips")
    blocked = res.json()
    assert any(ip["ip_address"] == "192.168.1.13" for ip in blocked)

# -------------------------------
# ✅ 6️⃣ Sprint 4: Unblock & Action Logs
# -------------------------------
def test_unblock_ip_and_logs():
    # Unblock IP
    res = client.post("/unblock-ip", json={"ip": "192.168.1.13"})
    assert res.status_code == 200

    # Confirm unblock recorded
    res = client.get("/admin/action-logs")
    logs = res.json()
    actions = [log["action"] for log in logs]
    assert "Block IP" in actions
    assert "Unblock IP" in actions

# -------------------------------
# ✅ 7️⃣ Clean up
# -------------------------------
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    if os.path.exists("test.db"):
        os.remove("test.db")
