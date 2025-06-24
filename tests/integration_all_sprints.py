# ✅ tests/integration_all_sprints.py

import os
import sys
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, get_db
from app import models, database

# ✅ Shared test DB
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(bind=engine)
database.SessionLocal = TestingSessionLocal

models.Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# -----------------------------
# ✅ Sprint 1
# -----------------------------

def test_system_status():
    res = client.get("/system/status?service=api")
    assert res.status_code == 200
    assert res.json()["api"] == "ok"

    conn = engine.connect()
    conn.execute(text("SELECT 1"))
    conn.close()

def test_log_traffic():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.10",
        "method": "GET",
        "url": "/home",
        "headers": "{}",
        "user_agent": "Normal",
        "request_size": 50,
        "response_code": 200,
        "response_time_ms": 20
    })
    assert res.status_code == 200
    assert "Traffic logged" in res.json()["message"]

def test_traffic_summary():
    res = client.get("/analytics/traffic-summary")
    assert res.status_code == 200
    assert "total_requests" in res.json()

# -----------------------------
# ✅ Sprint 2
# -----------------------------

def test_suspicious_agent():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.20",
        "method": "GET",
        "url": "/page",
        "headers": "{}",
        "user_agent": "sqlmap",
        "request_size": 10,
        "response_code": 200,
        "response_time_ms": 5
    })
    assert res.status_code == 200
    alerts = res.json()["alerts_triggered"]
    assert any("sqlmap" in alert for alert in alerts)

def test_sensitive_url():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.21",
        "method": "GET",
        "url": "/admin",
        "headers": "{}",
        "user_agent": "Normal",
        "request_size": 10,
        "response_code": 200,
        "response_time_ms": 5
    })
    assert res.status_code == 200
    alerts = res.json()["alerts_triggered"]
    assert any("/admin" in alert for alert in alerts)

# -----------------------------
# ✅ Sprint 3
# -----------------------------

def test_spike_block():
    for _ in range(105):
        res = client.post("/traffic/log", json={
            "source_ip": "192.168.1.30",
            "method": "GET",
            "url": "/page",
            "headers": "{}",
            "user_agent": "Normal",
            "request_size": 10,
            "response_code": 200,
            "response_time_ms": 5
        })
        assert res.status_code == 200
        time.sleep(0.005)

    res = client.get("/blocked-ips")
    assert res.status_code == 200
    assert any(ip["ip_address"] == "192.168.1.30" for ip in res.json())

# -----------------------------
# ✅ Sprint 4
# -----------------------------

def test_unblock_and_logs():
    res = client.post("/unblock-ip", json={"ip": "192.168.1.30"})
    assert res.status_code == 200
    assert "unblocked" in res.json()["message"]

    res = client.get("/admin/action-logs")
    assert res.status_code == 200
    actions = [log["action"] for log in res.json()]
    assert "Block IP" in actions
    assert "Unblock IP" in actions
