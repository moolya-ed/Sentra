from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.traffic_db import get_metrics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Traffic Analysis Service Running"}

@app.get("/metrics")
def metrics():
    return get_metrics()
