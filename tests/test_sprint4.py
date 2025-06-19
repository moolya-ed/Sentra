import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models, crud, database
from app.main import app, get_db

# ✅ 1️⃣ Use file-based SQLite for threads
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# ✅ 2️⃣ Delete old test.db if exists
if os.path.exists("test.db"):
    os.remove("test.db")

# ✅ 3️⃣ Create engine & session
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ 4️⃣ Make sure both modules use same SessionLocal
database.SessionLocal = TestingSessionLocal
crud.SessionLocal = TestingSessionLocal

# ✅ 5️⃣ Create tables ON that file DB
models.Base.metadata.create_all(bind=engine)

# ✅ 6️⃣ Override FastAPI DB dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_block_ip_logic():
    for _ in range(105):
        res = client.post("/traffic/log", json={
            "source_ip": "192.168.1.101",
            "method": "GET",
            "url": "/home",
            "headers": "test",
            "user_agent": "normal-agent",
            "request_size": 10,
            "response_code": 200,
            "response_time_ms": 20
        })
        assert res.status_code == 200

    res = client.get("/blocked-ips")
    assert res.status_code == 200
    assert any(ip["ip_address"] == "192.168.1.101" for ip in res.json())


def test_action_logs_logic():
    res = client.post("/unblock-ip", json={"ip": "192.168.1.101"})
    assert res.status_code == 200

    res = client.get("/admin/action-logs")
    assert res.status_code == 200
    logs = res.json()
    actions = [log["action"] for log in logs]
    assert "Block IP" in actions
    assert "Unblock IP" in actions
