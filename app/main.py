# app/main.py

import os
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Pump Selector",
    version="1.1.0",
    description="Hydraulic pump selection demo API",
)

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
        "api": "1.1.0",
        "curvepack": os.getenv("CURVEPACK_VERSION", "demo"),
    }


# --- New selector models ---

class DutyPoint(BaseModel):
    flow: float
    head: float

class SelectRequest(BaseModel):
    duty: DutyPoint

class Curve(BaseModel):
    flow: List[float]
    head: List[float]
    eff: List[float]
    npshr: List[float]

class Candidate(BaseModel):
    pump_id: str
    speed_rpm: int
    duty: DutyPoint
    curve: Curve

class SelectResponse(BaseModel):
    candidates: List[Candidate]


# --- Example pump data (fake but realistic curves) ---

SAMPLE_PUMPS = [
    {
        "pump_id": "P-100",
        "speed_rpm": 1780,
        "curve": {
            "flow":  [0, 100, 200, 300, 400, 500],
            "head":  [120, 118, 112, 102, 90, 75],
            "eff":   [0.45, 0.60, 0.72, 0.76, 0.73, 0.65],
            "npshr": [8.0, 8.1, 8.3, 8.7, 9.4, 10.5],
        },
        "bep_flow": 300.0,
    },
    {
        "pump_id": "P-200",
        "speed_rpm": 1780,
        "curve": {
            "flow":  [0, 150, 250, 350, 450, 550],
            "head":  [140, 132, 120, 108, 95, 80],
            "eff":   [0.40, 0.55, 0.70, 0.75, 0.71, 0.60],
            "npshr": [7.5, 7.8, 8.5, 9.0, 9.8, 11.0],
        },
        "bep_flow": 350.0,
    },
]


def _score_pump(flow_req: float, pump: dict) -> float:
    """Simple scoring: how close is requested flow to BEP"""
    return abs(flow_req - pump["bep_flow"])


# --- The real selector endpoint ---

@app.post("/hydraulics/select", response_model=SelectResponse)
def select_pump(payload: SelectRequest) -> SelectResponse:
    flow_req = payload.duty.flow

    # score pumps and sort
    ranked = sorted(
        SAMPLE_PUMPS,
        key=lambda p: _score_pump(flow_req, p)
    )

    candidates = []
    for pump in ranked:
        candidates.append(
            Candidate(
                pump_id=pump["pump_id"],
                speed_rpm=pump["speed_rpm"],
                duty=payload.duty,
                curve=Curve(**pump["curve"]),
            )
        )

    return SelectResponse(candidates=candidates)
