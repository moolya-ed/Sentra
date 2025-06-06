from fastapi import FastAPI, Request
from db.traffic_db import log_request
import time

app = FastAPI()

@app.middleware("http")
async def capture_traffic(request: Request, call_next):
    start = time.time()
    body = await request.body()
    response = await call_next(request)
    duration = (time.time() - start) * 1000

    log_request(
        source_ip=request.client.host,
        source_port=request.client.port,
        timestamp=time.time(),
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent", ""),
        request_size=len(body),
        response_code=response.status_code,
        response_time=duration
    )
    return response

@app.get("/")
def home():
    return {"message": "Traffic Capture Service Running"}


@app.get("/test")
async def test():
    return {"message": "GET /test received"}

@app.post("/abc")
async def abc():
    return {"message": "POST /abc received"}

@app.get("/foo")
async def foo():
    return {"message": "GET /foo received"}

