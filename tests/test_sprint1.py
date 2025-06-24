# ✅ tests/test_sprint1.py

import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Make sure `app` and modules are discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, get_db
from app import models, database

# ✅ Use a unique file-based test DB to avoid conflicts
os.makedirs("tests/temp", exist_ok=True)
TEST_DB = "tests/temp/test_sprint1.db"

# Remove old DB if exists
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{TEST_DB}"

# ✅ Create engine and session for this test
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

# ✅ Create tables
models.Base.metadata.create_all(bind=engine)

# ✅ Override the get_db to use this test session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ---------------------------
# ✅ TESTS START HERE
# ---------------------------

def test_system_status_valid():
    res = client.get("/system/status?service=db")
    assert res.status_code == 200
    assert res.json()["db"] == "ok"

def test_system_status_invalid():
    res = client.get("/system/status?service=invalid")
    assert res.status_code == 404

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
    res = client.post("/traffic/log", json=payload)
    assert res.status_code == 200
    assert res.json()["message"] == "Traffic logged"

def test_analytics_summary_all():
    res = client.get("/analytics/traffic-summary")
    assert res.status_code == 200
    assert "total_requests" in res.json()

def test_analytics_summary_with_filters():
    res = client.get("/analytics/traffic-summary?ip=192.168.1.77&method=GET")
    assert res.status_code == 200
