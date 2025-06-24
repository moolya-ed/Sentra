# ✅ tests/test_sprint3.py

import os
import sys
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Make app importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, get_db
from app import models, database

# ✅ Use StaticPool: NO LIMIT
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # 💪 disables QueuePool limit
)

TestingSessionLocal = sessionmaker(bind=engine)

# ✅ Ensure all modules use same SessionLocal
database.SessionLocal = TestingSessionLocal

# ✅ Create all tables
models.Base.metadata.create_all(bind=engine)

# ✅ Proper DB override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ✅ Spike test with delay to prevent connection exhaustion
def test_spike_detection_block():
    for _ in range(105):
        res = client.post("/traffic/log", json={
            "source_ip": "192.168.1.30",
            "method": "GET",
            "url": "/page",
            "headers": "{}",
            "user_agent": "NormalAgent",
            "request_size": 10,
            "response_code": 200,
            "response_time_ms": 5
        })
        assert res.status_code == 200
        time.sleep(0.01)  # ✅ slow down loop to let sessions close

    # ✅ Confirm block happened
    res = client.get("/blocked-ips")
    assert res.status_code == 200
    assert any(ip["ip_address"] == "192.168.1.30" for ip in res.json())
