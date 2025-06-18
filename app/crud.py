# app/crud.py

from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .models import TrafficMetadata, Alert, BlockedIP, ActionLog
from .schemas import TrafficEntry
from .config import SPIKE_THRESHOLD, BLOCK_DURATION_MINUTES, settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email_alert(subject: str, body: str):
    """Send email using Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.ALERT_RECEIVER
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, settings.ALERT_RECEIVER, msg.as_string())

        print(f"✅ EMAIL SENT: {subject}")
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")


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

    return {
        "total_requests": base_query.count(),
        "top_ips": [list(row) for row in base_query.with_entities(
            TrafficMetadata.source_ip, func.count().label("count")
        ).group_by(TrafficMetadata.source_ip).order_by(func.count().desc()).limit(5).all()],
        "methods": [list(row) for row in base_query.with_entities(
            TrafficMetadata.method, func.count().label("count")
        ).group_by(TrafficMetadata.method).all()],
        "response_codes": [list(row) for row in base_query.with_entities(
            TrafficMetadata.response_code, func.count()
        ).group_by(TrafficMetadata.response_code).all()],
        "traffic_trend_last_hour": [list(row) for row in base_query.with_entities(
            func.strftime('%H:%M', TrafficMetadata.timestamp), func.count()
        ).filter(
            TrafficMetadata.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).group_by(func.strftime('%H:%M', TrafficMetadata.timestamp)).all()]
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
    db.add(alert)
    db.commit()
    db.refresh(alert)
    print(f"⚠️ ALERT CREATED: {alert_type} | {description}")
    return alert


def get_recent_alerts(db: Session, limit: int = 5):
    return db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()


def block_ip(db: Session, ip: str):
    blocked_until = datetime.utcnow() + timedelta(minutes=BLOCK_DURATION_MINUTES)
    existing = db.query(BlockedIP).filter_by(ip_address=ip).first()
    if existing:
        existing.blocked_until = blocked_until
    else:
        db_ip = BlockedIP(ip_address=ip, blocked_until=blocked_until)
        db.add(db_ip)

    log = ActionLog(action="Block IP", target=ip, reason="Rate limit exceeded or suspicious activity")
    db.add(log)
    db.commit()

    send_email_alert(
        f"🚨 Sentra Alert: IP Blocked [{ip}]",
        f"The IP address {ip} was blocked until {blocked_until} due to suspicious activity."
    )
    print(f"✅ IP BLOCKED: {ip} until {blocked_until}")


def unblock_ip(db: Session, ip: str):
    db.query(BlockedIP).filter(BlockedIP.ip_address == ip).delete()
    db.add(ActionLog(action="Unblock IP", target=ip, reason="Manual unblock"))
    db.commit()
    print(f"✅ IP UNBLOCKED: {ip}")


def is_ip_blocked(db: Session, ip: str):
    record = db.query(BlockedIP).filter(
        BlockedIP.ip_address == ip,
        BlockedIP.blocked_until > datetime.utcnow()
    ).first()
    return record is not None


def get_blocked_ips(db: Session):
    return db.query(BlockedIP).all()


def get_action_logs(db: Session, limit=50):
    return db.query(ActionLog).order_by(ActionLog.timestamp.desc()).limit(limit).all()


def check_for_alerts(entry: TrafficEntry, db: Session):
    alerts = []
    print(f"➡️ Checking IP={entry.source_ip} UA={entry.user_agent} URL={entry.url}")

    # ✅ 1) Spike detection
    if not is_ip_blocked(db, entry.source_ip):
        recent_count = db.query(TrafficMetadata).filter(
            TrafficMetadata.source_ip == entry.source_ip,
            TrafficMetadata.timestamp >= datetime.utcnow() - timedelta(minutes=1)
        ).count()
        print(f"📊 Recent count: {recent_count}")

        if recent_count >= SPIKE_THRESHOLD:
            alert = create_alert(db, "Traffic Spike",
                                 f"{recent_count} requests in last 1 min",
                                 entry.source_ip)
            alerts.append(alert)
            block_ip(db, entry.source_ip)

    # ✅ 2) Suspicious User-Agent detection
    if any(bot in entry.user_agent.lower() for bot in ["sqlmap", "nmap", "malicious-bot"]):
        alert = create_alert(db, "Suspicious User-Agent",
                             f"Detected suspicious agent: {entry.user_agent}",
                             entry.source_ip)
        alerts.append(alert)
        if not is_ip_blocked(db, entry.source_ip):
            block_ip(db, entry.source_ip)

    # ✅ 3) Sensitive URL detection
    if entry.url.lower() in ["/admin", "/etc/passwd", "/config", "/wp-login.php"]:
        alert = create_alert(db, "Sensitive URL Access",
                             f"Attempted access: {entry.url}",
                             entry.source_ip)
        alerts.append(alert)
        if not is_ip_blocked(db, entry.source_ip):
            block_ip(db, entry.source_ip)

    return alerts
