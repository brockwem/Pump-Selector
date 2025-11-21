import os, io
from fastapi import FastAPI, Body, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from app.data.loader import load_data
from app.engine.select import Curve, interp, hydraulic_power_kw, ft_to_m, to_m3s_gpm, pick_motor_hp, find_bep_Q, score_candidate
from app.pdf.datasheet import generate_pdf

API_KEY = os.getenv("API_KEY","changeme-very-secret")
DATA_DIR = os.getenv("DATA_DIR","./sample_data")
CURVEPACK_VERSION = os.getenv("CURVEPACK_VERSION","curvepack_demo")
families, pricing, curves = load_data(DATA_DIR)

app = FastAPI(title="HydraulicSelectionService", version="1.0.0")

@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/version")
def version(): return {"service":"hydraulics","api":app.version,"curvepack":CURVEPACK_VERSION}

class DutyValue(BaseModel):
    value: float; unit: str
class Duty(BaseModel):
    Q: DutyValue; H: DutyValue
class Weights(BaseModel):
    bep: float = 0.40; eff: float = 0.25; speed: float = 0.10; price: float = 0.15; lead: float = 0.10
class SelectRequest(BaseModel):
    duty: Duty; sg: float = 1.0
    speedPreference: List[int] = Field(default_factory=lambda:[1750,3500])
    tolerances: Dict[str,float] = Field(default_factory=lambda:{"head_pct":3.0})
    weights: Weights = Weights()
    pumpsInParallel: int = 1
    returnPlotData: bool = True

def unitize_Q(value, unit):
    u=unit.lower()
    if u=='gpm': return value
    if u in ['m3/h','m3h']: return value*4.402867539
    if u in ['l/s','ls']: return value*15.8503
    raise HTTPException(status_code=400, detail=f"Unsupported flow unit: {unit}")
def unitize_H(value, unit):
    u=unit.lower()
    if u in ['ft','feet']: return value
    if u=='m': return value/0.3048
    raise HTTPException(status_code=400, detail=f"Unsupported head unit: {unit}")

@app.post("/hydraulics/select")
def select(req: SelectRequest, x_api_key: Optional[str] = Header(default=None)):
    if x_api_key != API_KEY: raise HTTPException(status_code=401, detail="Unauthorized")
    Q_req_gpm = unitize_Q(req.duty.Q.value, req.duty.Q.unit)
    H_req_ft = unitize_H(req.duty.H.value, req.duty.H.unit)
    head_tol = req.tolerances.get('head_pct',3.0)/100.0
    results=[]
    for (fid, sp), curve in curves.items():
        if sp not in req.speedPreference: continue
        # interpolate at duty
        try: Hc, Ec, Pc, Nc = interp(curve, Q_req_gpm, method="pchip")
        except Exception: continue
        if abs(Hc - H_req_ft)/max(1.0,H_req_ft) > head_tol: continue
        if not Pc or Pc <= 0:
            Q_m3s = to_m3s_gpm(Q_req_gpm); H_m = ft_to_m(Hc)
            Ph_kw = hydraulic_power_kw(Q_m3s, H_m, rho=998.2*req.sg)
            Pc = Ph_kw / (max(Ec/100.0,0.01)*0.98) * 1.34102
        Q_m3s = to_m3s_gpm(Q_req_gpm); H_m = ft_to_m(Hc)
        Ph_kw = hydraulic_power_kw(Q_m3s, H_m, rho=998.2*req.sg)
        shaft_kw = Ph_kw / (max(Ec/100.0,0.01)*0.98)
        motor_kw_apply = shaft_kw / 0.93
        motor_hp = pick_motor_hp(motor_kw_apply)
        Q_bep = find_bep_Q(curve)
        bep_offset = abs(Q_req_gpm - Q_bep)/max(Q_bep,1.0)*100.0
        pb, lt = pricing.get(fid, ("PB3","LT3"))
        S = score_candidate(bep_offset, Ec, sp, pb, lt)
        results.append({
            "family_id": fid, "model": f"{fid}-{int(curve.Dref_mm)}", "speed_rpm": sp,
            "impeller_d_mm": curve.Dref_mm, "eta_pct": round(Ec,1), "bep_offset_pctQ": round(bep_offset,1),
            "head": {"value": round(Hc,1), "unit": "ft"}, "power": {"value": round(Pc,1), "unit": "hp"},
            "npshr_ft": round(Nc,1) if Nc is not None else None,
            "motor_pick": {"rating_hp": motor_hp, "standard": "NEMA"},
            "price_band": pb, "lead_time": lt, "score": round(S,3)
        })
    results.sort(key=lambda x: x['score'], reverse=True)
    payload={"versionTag": CURVEPACK_VERSION, "candidates": results[:5]}
    if req.returnPlotData and results:
        any_key=list(curves.keys())[0]; c=curves[any_key]
        payload["plotData"]={"Q":c.Q,"H":c.H,"Eff":c.Eff,"Power":c.P,"NPSHr":c.NPSHr}
    return JSONResponse(payload)

class PDFRequest(BaseModel):
    selection: dict; branding: Optional[dict] = None; quote: Optional[dict] = None
@app.post("/pdf")
def pdf(req: PDFRequest, x_api_key: Optional[str] = Header(default=None)):
    if x_api_key != API_KEY: raise HTTPException(status_code=401, detail="Unauthorized")
    buf = io.BytesIO()
    meta={"title": (req.branding or {}).get("title","Pump Selection Datasheet"),
          "curvepack": CURVEPACK_VERSION, "quote_id": (req.quote or {}).get("id","N/A")}
    flat={"family_id": req.selection.get("family_id"), "model": req.selection.get("model"),
          "speed_rpm": req.selection.get("speed_rpm"), "impeller_d_mm": req.selection.get("impeller_d_mm"),
          "eta_pct": req.selection.get("eta_pct"), "bep_offset_pctQ": req.selection.get("bep_offset_pctQ"),
          "head_ft": (req.selection.get("head") or {}).get("value"),
          "power_hp": (req.selection.get("power") or {}).get("value"),
          "npshr_ft": req.selection.get("npshr_ft"), "motor_hp": (req.selection.get("motor_pick") or {}).get("rating_hp"),
          "price_band": req.selection.get("price_band"), "lead_time": req.selection.get("lead_time"),
          "score": req.selection.get("score")}
    generate_pdf(buf, flat, meta); buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition":"attachment; filename=datasheet.pdf"})
