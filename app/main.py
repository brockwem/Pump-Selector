# app/main.py
import os
from fastapi import FastAPI

app = FastAPI(title="Pump Selector", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Pump Selector API running. See /docs."}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {
        "service": "hydraulics",
        "api": "1.0.0",
        "curvepack": os.getenv("CURVEPACK_VERSION", "demo")
    }
