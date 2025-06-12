from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .models import TrafficMetadata, Alert
from .schemas import TrafficEntry

def create_traffic_entry(db: Session, entry: TrafficEntry):
    db_entry = TrafficMetadata(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def get_summary_metrics(db: Session, filter_ip: str = None, filter_method: str = None):
    base_query = db.query(TrafficMetadata)

    if filter_ip:
        base_query = base_query.filter(TrafficMetadata.source_ip == filter_ip)
    if filter_method:
        base_query = base_query.filter(TrafficMetadata.method == filter_method)

    total_requests = base_query.count()

    top_ips = base_query.with_entities(
        TrafficMetadata.source_ip, func.count().label("count")
    ).group_by(TrafficMetadata.source_ip).order_by(func.count().desc()).limit(5).all()
    top_ips = [list(row) for row in top_ips]

    method_counts = base_query.with_entities(
        TrafficMetadata.method, func.count().label("count")
    ).group_by(TrafficMetadata.method).all()
    method_counts = [list(row) for row in method_counts]

    response_codes = base_query.with_entities(
        TrafficMetadata.response_code, func.count()
    ).group_by(TrafficMetadata.response_code).all()
    response_codes = [list(row) for row in response_codes]

    traffic_last_hour = base_query.with_entities(
        func.strftime('%H:%M', TrafficMetadata.timestamp), func.count()
    ).filter(
        TrafficMetadata.timestamp >= datetime.utcnow() - timedelta(hours=1)
    ).group_by(func.strftime('%H:%M', TrafficMetadata.timestamp)).all()
    traffic_last_hour = [list(row) for row in traffic_last_hour]

    return {
        "total_requests": total_requests,
        "top_ips": top_ips,
        "methods": method_counts,
        "response_codes": response_codes,
        "traffic_trend_last_hour": traffic_last_hour
    }

def create_alert(db: Session, alert_type: str, description: str, source_ip: str):
    alert = Alert(
        id=str(uuid4()),
        timestamp=datetime.utcnow(),
        alert_type=alert_type,
        description=description,
        source_ip=source_ip,
        severity="High"
    )
    print("✅ ALERT SAVED:", alert_type, description, source_ip)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def get_alerts(db: Session, limit: int = 50):
    return db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()

def get_recent_alerts(db: Session, limit: int = 5):
    return db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()

