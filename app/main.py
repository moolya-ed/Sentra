from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text  # ✅ for SELECT 1 fix
from pydantic import BaseModel
from . import models, database, crud, schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Sentra - DDoS Detection System",
    version="1.0.0",
    description="Monitors traffic, detects anomalies, blocks IPs."
)

def get_db():
    return database.get_db()

@app.middleware("http")
async def block_ip_middleware(request: Request, call_next):
    db = next(get_db())
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host
    if crud.is_ip_blocked(db, client_ip):
        return JSONResponse(status_code=403, content={"detail": f"IP {client_ip} is blocked"})
    return await call_next(request)

@app.api_route("/system/status", methods=["GET"], include_in_schema=False)
def system_status(request: Request):
    service = request.query_params.get("service", "all")
    allowed_services = ["db", "api", "all"]
    if service not in allowed_services:
        raise HTTPException(status_code=404, detail=f"Service '{service}' Not Found")
    status = {"service": service}
    if service in ["db", "all"]:
        try:
            with database.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            status["db"] = "ok"
        except Exception as e:
            status["db"] = f"error: {str(e)}"
    if service in ["api", "all"]:
        status["api"] = "ok"
    return status

@app.post("/traffic/log")
def log_traffic(entry: schemas.TrafficEntry, db: Session = Depends(get_db)):
    record = crud.create_traffic_entry(db, entry)
    alerts = crud.check_for_alerts(entry, db)
    return {
        "message": "Traffic logged",
        "record_id": record.id,
        "alerts_triggered": [a.description for a in alerts]
    }

@app.get("/analytics/traffic-summary")
def traffic_summary(ip: str = None, method: str = None, db: Session = Depends(get_db)):
    metrics = crud.get_summary_metrics(db, filter_ip=ip, filter_method=method)
    alerts = crud.get_recent_alerts(db, limit=5)
    metrics["recent_alerts"] = [{
        "timestamp": a.timestamp.isoformat(),
        "type": a.alert_type,
        "description": a.description,
        "source_ip": a.source_ip
    } for a in alerts]
    return metrics

@app.get("/blocked-ips")
def blocked_ips(db: Session = Depends(get_db)):
    ips = crud.get_blocked_ips(db)
    return [{"ip_address": ip.ip_address, "blocked_until": ip.blocked_until.isoformat()} for ip in ips]

@app.get("/")
def root():
    return {"message": "✅ Sentra backend is running!"}

class UnblockRequest(BaseModel):
    ip: str

@app.post("/unblock-ip")
def unblock_ip(req: UnblockRequest, db: Session = Depends(get_db)):
    crud.unblock_ip(db, req.ip)
    return {"message": f"✅ IP {req.ip} unblocked"}

@app.get("/admin/action-logs")
def get_action_logs(db: Session = Depends(get_db)):
    logs = crud.get_action_logs(db)
    return [{"timestamp": log.timestamp.isoformat(), "action": log.action, "target": log.target, "reason": log.reason} for log in logs]

@app.get("/admin/alerts")
def get_all_alerts(db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).order_by(models.Alert.timestamp.desc()).all()
    return [{"timestamp": a.timestamp.isoformat(), "type": a.alert_type, "description": a.description, "source_ip": a.source_ip} for a in alerts]
