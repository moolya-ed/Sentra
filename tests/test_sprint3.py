# tests/test_sprint3.py

import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import get_db
from app import models, database, crud
from app.schemas import TrafficEntry

# ----------------------------
# ✅ Test DB Setup: in-memory
# ----------------------------
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine)
database.SessionLocal = TestingSessionLocal
models.Base.metadata.create_all(bind=engine)

# ----------------------------
# ✅ Dependency override
# ----------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# ----------------------------
# ✅ Sprint 3 Test Suite
# ----------------------------

def test_ip_auto_blocking():
    """
    Verify that after many requests from same IP,
    it is blocked due to spike threshold.
    """
    db = next(override_get_db())

    entry_data = {
        "source_ip": "127.0.0.1",
        "method": "GET",
        "url": "/products",
        "headers": "{}",
        "user_agent": "Mozilla",
        "request_size": 50,
        "response_code": 200,
        "response_time_ms": 30
    }

    # Send requests exceeding threshold
    for _ in range(105):
        entry = TrafficEntry(**entry_data)
        crud.create_traffic_entry(db, entry)
        crud.check_for_alerts(entry, db)

    assert crud.is_ip_blocked(db, "127.0.0.1")

def test_blocked_ips_list():
    """
    Verify that blocked IP appears in blocked IP list.
    """
    db = next(override_get_db())
    blocked_ips = crud.get_blocked_ips(db)
    assert any(b.ip_address == "127.0.0.1" for b in blocked_ips)

def test_action_logs_exist():
    """
    Verify that blocking action is recorded in ActionLog.
    """
    db = next(override_get_db())
    logs = crud.get_action_logs(db)
    assert any("Block IP" in log.action for log in logs)
