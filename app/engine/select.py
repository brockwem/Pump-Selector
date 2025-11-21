from dataclasses import dataclass
from typing import List, Optional, Tuple
from .pchip import pchip_interpolate, lin_interp
@dataclass
class Curve:
    Q: List[float]; H: List[float]; Eff: List[float]; P: List[float]
    NPSHr: Optional[List[float]] = None
    speed_rpm: int = 1750
    Dref_mm: float = 317.0
    family_id: str = ""
def to_m3s_gpm(gpm: float) -> float: return gpm * 0.00378541178 / 60.0
def ft_to_m(ft: float) -> float: return ft * 0.3048
def hydraulic_power_kw(Q_m3s, H_m, rho=998.2, g=9.80665): return (rho*g*Q_m3s*H_m)/1000.0
def pick_motor_hp(kW_apply: float) -> int:
    need = 1.15 * kW_apply
    hp=[1,2,3,5,7,10,15,20,25,30,40,50,60,75,100]
    kw=[0.75,1.5,2.2,3.7,5.6,7.5,11.2,15,18.7,22.4,30,37.3,45,55.9,74.6]
    for i,v in enumerate(kw):
        if v >= need: return hp[i]
    return 100
def interp(curve: Curve, Qx: float, method="pchip"):
    Q,H,E,P = curve.Q,curve.H,curve.Eff,curve.P
    if method=="pchip":
        Hx=pchip_interpolate(Q,H,Qx); Ex=pchip_interpolate(Q,E,Qx)
        Px=pchip_interpolate(Q,P,Qx) if P else None
    else:
        k=None
        for i in range(len(Q)-1):
            if Q[i]<=Qx<=Q[i+1]: k=i; break
        if k is None: raise ValueError("Q outside range")
        Hx=lin_interp(Q[k],H[k],Q[k+1],H[k+1],Qx)
        Ex=lin_interp(Q[k],E[k],Q[k+1],E[k+1],Qx)
        Px=lin_interp(Q[k],P[k],Q[k+1],P[k+1],Qx) if P else None
    NPS=None
    if curve.NPSHr:
        Qx2=min(max(Qx,curve.Q[0]),curve.Q[-1])
        NPS=pchip_interpolate(curve.Q,curve.NPSHr,Qx2)
    return Hx,Ex,Px,NPS
def find_bep_Q(curve: Curve) -> float:
    mi=max(range(len(curve.Eff)), key=lambda i: curve.Eff[i]); return curve.Q[mi]
def score_candidate(bep_offset_pct, eta_pct, speed_bias, price_band, lead_time) -> float:
    f_bep = max(0.0, min(1.0, 1.0 - (bep_offset_pct/35.0)))
    f_eta = max(0.0, min(1.0, (eta_pct-40.0)/(85.0-40.0)))
    f_speed = 1.0 if speed_bias==1750 else 0.6
    pmap={"PB1":1.0,"PB2":0.8,"PB3":0.6,"PB4":0.4,"PB5":0.2}
    lmap={"LT1":1.0,"LT2":0.8,"LT3":0.6,"LT4":0.4,"LT5":0.2}
    f_price=pmap.get(price_band,0.6); f_lead=lmap.get(lead_time,0.6)
    return 0.40*f_bep + 0.25*f_eta + 0.10*f_speed + 0.15*f_price + 0.10*f_lead
