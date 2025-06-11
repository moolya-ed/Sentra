# tests/test_sprint1.py

import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure app is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import get_db, SessionLocal
from app import models

# 1. Setup In-Memory SQLite Test DB
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Bind models to test DB
models.Base.metadata.create_all(bind=engine)

# 3. Rebind production SessionLocal to test engine
#SessionLocal.configure(bind=engine)

# 4. Override get_db to use test session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 5. Create test client
client = TestClient(app)

# ---------------------------
# ✅ TESTS START HERE
# ---------------------------

def test_system_status_valid():
    response = client.get("/system/status?service=db")
    assert response.status_code == 200

def test_system_status_invalid():
    response = client.get("/system/status?service=invalid")
    assert response.status_code == 404

def test_traffic_log_post():
    payload = {
        "source_ip": "192.168.1.77",
        "method": "GET",
        "url": "/dashboard",
        "headers": "{}",
        "user_agent": "TestAgent",
        "request_size": 150,
        "response_code": 200,
        "response_time_ms": 42
    }
    response = client.post("/traffic/log", json=payload)
    assert response.status_code == 200
    assert response.json()["source_ip"] == "192.168.1.77"

def test_analytics_summary_all():
    response = client.get("/analytics/traffic-summary")
    assert response.status_code == 200
    assert "total_requests" in response.json()

def test_analytics_summary_with_filters():
    response = client.get("/analytics/traffic-summary?ip=192.168.1.77&method=GET")
    assert response.status_code == 200
