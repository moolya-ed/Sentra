# app/models.py

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime

Base = declarative_base()

class TrafficMetadata(Base):
    __tablename__ = "traffic_metadata"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=func.now())
    source_ip = Column(String)
    method = Column(String)
    url = Column(String)
    headers = Column(String)
    user_agent = Column(String)
    request_size = Column(Integer)
    response_code = Column(Integer)
    response_time_ms = Column(Integer)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_ip = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String)
    description = Column(String)
    severity = Column(String)

class BlockedIP(Base):
    __tablename__ = "blocked_ips"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = Column(String, unique=True, index=True)
    blocked_until = Column(DateTime)


class ActionLog(Base):
    __tablename__ = "action_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String)
    target = Column(String)
    reason = Column(String)
