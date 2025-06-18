# app/main.py

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel  # ✅ NEW: for JSON request body
from . import models, database, crud, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sentra - DDoS Detection System",
    version="1.0.0",
    description="Backend API to log, analyze, detect suspicious traffic patterns, and auto-block IPs."
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.middleware("http")
async def block_ip_middleware(request: Request, call_next):
    db = SessionLocal()
    try:
        client_ip = request.headers.get("X-Forwarded-For") or request.client.host
        if crud.is_ip_blocked(db, client_ip):
            return JSONResponse(status_code=403, content={"detail": f"IP {client_ip} is blocked"})
        response = await call_next(request)
        return response
    finally:
        db.close()

@app.get("/system/status")
def system_status(service: str = Query(default="all")):
    allowed_services = ["db", "api", "all"]
    if service not in allowed_services:
        raise HTTPException(status_code=404, detail=f"Service '{service}' Not Found")
    return {"status": "ok", "service": service}

@app.post("/traffic/log")
def log_traffic(entry: schemas.TrafficEntry, db: Session = Depends(get_db)):
    traffic_record = crud.create_traffic_entry(db, entry)
    alerts = crud.check_for_alerts(entry, db)
    return {
        "message": "Traffic logged",
        "record_id": traffic_record.id,
        "alerts_triggered": [alert.description for alert in alerts]
    }

@app.get("/analytics/traffic-summary")
def traffic_summary(
    ip: str = Query(default=None),
    method: str = Query(default=None),
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
        } for alert in alerts
    ]
    return metrics

@app.get("/blocked-ips")
def blocked_ips(db: Session = Depends(get_db)):
    ips = crud.get_blocked_ips(db)
    return [{"ip_address": ip.ip_address, "blocked_until": ip.blocked_until.isoformat()} for ip in ips]

@app.get("/")
def read_root():
    return {"message": "✅ Sentra backend is running!"}

# ✅ NEW: JSON version for unblock
class UnblockRequest(BaseModel):
    ip: str

@app.post("/unblock-ip")
def unblock_ip(request: UnblockRequest, db: Session = Depends(get_db)):
    crud.unblock_ip(db, request.ip)
    return {"message": f"✅ IP {request.ip} unblocked"}
