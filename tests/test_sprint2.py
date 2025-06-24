# ✅ tests/test_sprint2.py

import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, get_db
from app import models

# --- Setup ---
os.makedirs("tests/temp", exist_ok=True)
TEST_DB = "tests/temp/test_sprint2.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{TEST_DB}"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

models.Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# --- Sprint 2 Tests: Alerting ---
def test_suspicious_agent_alert():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.22",
        "method": "GET",
        "url": "/home",
        "headers": "{}",
        "user_agent": "sqlmap",
        "request_size": 50,
        "response_code": 200,
        "response_time_ms": 10
    })
    assert res.status_code == 200
    assert any("sqlmap" in a for a in res.json()["alerts_triggered"])

def test_sensitive_url_alert():
    res = client.post("/traffic/log", json={
        "source_ip": "192.168.1.23",
        "method": "GET",
        "url": "/admin",
        "headers": "{}",
        "user_agent": "NormalAgent",
        "request_size": 50,
        "response_code": 200,
        "response_time_ms": 10
    })
    assert res.status_code == 200
    assert any("/admin" in a for a in res.json()["alerts_triggered"])
