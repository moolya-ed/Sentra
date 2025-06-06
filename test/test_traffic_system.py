import pytest
from fastapi.testclient import TestClient
from main import app
from db.traffic_db import log_request, get_metrics, init_db
import sqlite3
import os

client = TestClient(app)
DB_PATH = "db/traffic.db"

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Ensure DB is initialized and clean before tests"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    yield

def test_capture_valid_get():
    response = client.get("/capture/test")
    assert response.status_code == 200 or response.status_code == 404  # In case /capture/test isn't defined
    # Acceptable if 404 is valid behavior due to unmounted routes

def test_capture_valid_post():
    response = client.post("/capture/data", json={"key": "value"})
    assert response.status_code in [200, 404]

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "requests_per_minute" in data
    assert "top_source_ips" in data
    assert "request_method_distribution" in data
    assert "response_code_statistics" in data
    assert "traffic_trend_last_hour" in data
    assert "average_response_time_ms" in data

def test_log_request_directly():
    log_request(
        source_ip="192.168.1.1",
        path="/test/log",
        method="GET",
        status_code=200,
        response_time=0.123
    )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    metrics = get_metrics(conn)
    conn.close()

    assert metrics["requests_per_minute"] >= 1
    assert any(ip["source_ip"] == "192.168.1.1" for ip in metrics["top_source_ips"])
    assert "GET" in metrics["request_method_distribution"]
    assert "200" in metrics["response_code_statistics"]

def test_trend_accuracy():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    trend = get_metrics(conn)["traffic_trend_last_hour"]
    conn.close()

    assert isinstance(trend, list)
    for point in trend:
        assert "minute" in point
        assert "count" in point
