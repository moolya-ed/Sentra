# ✅ tests/test_sprint4.py

import os
import sys
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import app properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, get_db
from app import models, database

# Use StaticPool for isolated in-memory DB
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


def test_unblock_and_action_logs():
    # Block IP first by triggering spike
    for _ in range(105):
        res = client.post("/traffic/log", json={
            "source_ip": "192.168.1.99",
            "method": "GET",
            "url": "/test",
            "headers": "{}",
            "user_agent": "Normal",
            "request_size": 10,
            "response_code": 200,
            "response_time_ms": 5
        })
        assert res.status_code == 200
        time.sleep(0.005)

    # Unblock IP
    res = client.post("/unblock-ip", json={"ip": "192.168.1.99"})
    assert res.status_code == 200
    assert "unblocked" in res.json()["message"]

    # Verify action logs have Block & Unblock
    res = client.get("/admin/action-logs")
    assert res.status_code == 200
    actions = [log["action"] for log in res.json()]
    assert "Block IP" in actions
    assert "Unblock IP" in actions
