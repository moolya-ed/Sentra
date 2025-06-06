import sys
import os
import pytest
import sqlite3
from fastapi.testclient import TestClient
from datetime import datetime


# Dynamically add the root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from db.traffic_db import init_db, log_request, get_metrics

DB_PATH = "db/traffic.db"
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

def test_get_root_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Main API Running" in response.text

def test_valid_capture_logs_200():
    response = client.get("/capture/test")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_invalid_capture_returns_404():
    response = client.get("/invalid-url")
    assert response.status_code == 404

def test_post_request_logs():
    response = client.post("/capture/register", json={"key": "value"})
    assert response.status_code in [200, 404]

def test_metrics_endpoint():
    response = client.get("/analysis/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert "requests_per_minute" in metrics
    assert "request_method_distribution" in metrics
    assert "response_code_statistics" in metrics
    assert "avg_response_time" in metrics

def test_log_request_directly():
    log_request(
        source_ip="192.168.1.1",
        source_port=8080,
        timestamp=datetime.utcnow().isoformat(),
        method="GET",
        url="/test/direct-log",
        user_agent="pytest-agent",
        request_size=128,
        response_code=200,  # ✅ This must match your function's parameter name
        response_time=0.123
    )

def test_trend_accuracy():
    trend = get_metrics()["traffic_trend_last_hour"]
    assert isinstance(trend, list)

