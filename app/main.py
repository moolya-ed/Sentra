from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from . import models, database, crud, schemas
from .database import SessionLocal, engine
from datetime import datetime, timedelta

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sentra - DDoS Detection System",
    version="1.0.0",
    description="Backend API to log, analyze, and detect suspicious traffic patterns in real time."
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/system/status", summary="System Status Check")
def system_status(service: str = Query(default="all")):
    allowed_services = ["db", "api", "all"]
    if service not in allowed_services:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    return {"status": "ok", "service": service}

@app.post("/traffic/log", summary="Log Incoming Traffic")
def log_traffic(entry: schemas.TrafficEntry, db: Session = Depends(get_db)):
    traffic_record = crud.create_traffic_entry(db, entry)
    alerts = check_for_alerts(entry, db)
    return {
        "message": "Traffic logged",
        "record_id": traffic_record.id,
        "alerts_triggered": [alert.description for alert in alerts]
    }

@app.get(
    "/analytics/traffic-summary",
    summary="Real-Time Traffic Metrics",
    description="View analytics like total requests, top IPs, method usage, response codes, hourly trends, and recent alerts."
)
def traffic_summary(
    ip: str = Query(default=None, description="Filter by source IP"),
    method: str = Query(default=None, description="Filter by HTTP method"),
    db: Session = Depends(get_db)
):
    metrics = crud.get_summary_metrics(db, filter_ip=ip, filter_method=method)
    alerts = crud.get_recent_alerts(db, limit=5)
    metrics["recent_alerts"] = [
        {
            "timestamp": alert.timestamp.isoformat(),
            "type": alert.alert_type,
            "description": alert.description,
            "source_ip": alert.source_ip
        }
        for alert in alerts
    ]
    return metrics

def check_for_alerts(entry: schemas.TrafficEntry, db: Session):
    from .models import TrafficMetadata
    alerts = []

    spike_threshold = 5
    recent_count = db.query(TrafficMetadata).filter(
        TrafficMetadata.source_ip == entry.source_ip,
        TrafficMetadata.timestamp >= datetime.utcnow() - timedelta(minutes=1)
    ).count()

    if recent_count >= spike_threshold:
        alert = crud.create_alert(
            db, "Traffic Spike", f"{recent_count} requests in last 1 min", entry.source_ip
        )
        alerts.append(alert)

    suspicious_agents = ["sqlmap", "nmap", "malicious-bot"]
    if any(agent in entry.user_agent.lower() for agent in suspicious_agents):
        alert = crud.create_alert(
            db, "Suspicious User-Agent", f"Detected suspicious agent: {entry.user_agent}", entry.source_ip
        )
        alerts.append(alert)

    suspicious_urls = ["/admin", "/etc/passwd", "/config", "/wp-login.php"]
    if entry.url.lower() in suspicious_urls:
        alert = crud.create_alert(
            db, "Sensitive URL Access", f"Attempted access: {entry.url}", entry.source_ip
        )
        alerts.append(alert)

    return alerts
