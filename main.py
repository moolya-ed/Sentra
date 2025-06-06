from fastapi import FastAPI
from backendap.capture_app import app as capture_app
from backendap.analysis_app import app as analysis_app
from db.traffic_db import init_db

init_db()

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Main API Running. Available endpoints: /capture/, /analysis/"}

app.mount("/capture", capture_app)
app.mount("/analysis", analysis_app)
