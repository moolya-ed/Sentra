from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Traffic Response Service Running"}

@app.get("/status")
async def status():
    return {"status": "OK"}
