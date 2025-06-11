from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from . import models, database, crud, schemas
from .database import SessionLocal, engine

# Create DB tables
models.Base.metadata.create_all(bind=engine)

# App metadata shown in Swagger UI
app = FastAPI(
    title="Sentra - DDoS Detection System",
    version="1.0.0",
    description="Backend API to log, analyze, and detect suspicious traffic patterns in real time."
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------
# 1️⃣ SYSTEM STATUS CHECK (GET)
# ------------------------------
@app.get(
    "/system/status",
    summary="System Status Check",
    description="Check the system health or a specific component like database or API. Returns 404 for unknown services."
)
def system_status(service: str = Query(default="all", description="Service to check (e.g., db, api)")):
    allowed_services = ["db", "api", "all"]
    if service not in allowed_services:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    return {"status": "ok", "service": service}

# ------------------------------
# 2️⃣ TRAFFIC LOGGER (POST)
# ------------------------------
@app.post(
    "/traffic/log",
    summary="Log Incoming Traffic",
    description="Submit traffic metadata (IP, method, user agent, etc.) to be stored for DDoS analysis."
)
def log_traffic(entry: schemas.TrafficEntry, db: Session = Depends(get_db)):
    return crud.create_traffic_entry(db, entry)

# ------------------------------
# 3️⃣ TRAFFIC METRICS SUMMARY (GET)
# ------------------------------
@app.get(
    "/analytics/traffic-summary",
    summary="Real-Time Traffic Metrics",
    description="View analytics like total requests, top IPs, method usage, response codes, and hourly trends. Optional filters by IP or method."
)
def traffic_summary(
    ip: str = Query(default=None, description="Filter by source IP"),
    method: str = Query(default=None, description="Filter by HTTP method"),
    db: Session = Depends(get_db)
):
    return crud.get_summary_metrics(db, filter_ip=ip, filter_method=method)
