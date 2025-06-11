from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TrafficEntry(BaseModel):
    timestamp: Optional[datetime] = None
    source_ip: str
    method: str
    url: str
    headers: str
    user_agent: str
    request_size: int
    response_code: int
    response_time_ms: int

    class Config:
        orm_mode = True
