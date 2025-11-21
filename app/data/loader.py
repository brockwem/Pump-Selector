import os, csv
from dataclasses import dataclass
from typing import Dict, List
from ..engine.select import Curve
@dataclass
class FamilyMeta:
    family_id: str; name: str; stages: int; allowed_speeds: List[int]
    Dref_mm: float; Dmin_mm: float; Dmax_mm: float
    Q_shutoff: float; Q_runout: float; H_shutoff: float; max_power_hp: float
def read_csv(path):
    rows=[]; 
    with open(path, newline='') as f:
        r=csv.DictReader(f)
        for row in r: rows.append(row)
    return rows
def load_data(data_dir: str):
    families_path = os.path.join(data_dir,'families.csv')
    fam_rows = read_csv(families_path)
    families: Dict[str, FamilyMeta] = {}
    for r in fam_rows:
        speeds=[int(s) for s in r['allowed_speeds_rpm'].split('|')]
        families[r['family_id']] = FamilyMeta(
            family_id=r['family_id'], name=r['name'], stages=int(r['stages']),
            allowed_speeds=speeds, Dref_mm=float(r['Dref_mm']), Dmin_mm=float(r['Dmin_mm']), Dmax_mm=float(r['Dmax_mm']),
            Q_shutoff=float(r['Q_shutoff']), Q_runout=float(r['Q_runout']), H_shutoff=float(r['H_shutoff']),
            max_power_hp=float(r['max_power_hp'])
        )
    pricing={}
    pr_path=os.path.join(data_dir,'pricing.csv')
    if os.path.exists(pr_path):
        for r in read_csv(pr_path):
            pricing[r['family_id']]=(r['price_band'], r['lead_time_class'])
    curves={}
    for fid,meta in families.items():
        for sp in meta.allowed_speeds:
            cpath = os.path.join(data_dir, f'curves_{fid}_{sp}.csv')
            if not os.path.exists(cpath): continue
            rows=read_csv(cpath)
            Q=[float(x['Q']) for x in rows]; H=[float(x['H']) for x in rows]
            E=[float(x['Eff_pct']) for x in rows]
            P=[float(x.get('Power_hp',0.0)) for x in rows]
            N=None
            if 'NPSHr_ft' in rows[0]: N=[float(x['NPSHr_ft']) for x in rows]
            curves[(fid,sp)] = Curve(Q=Q,H=H,Eff=E,P=P,NPSHr=N,speed_rpm=sp,Dref_mm=meta.Dref_mm,family_id=fid)
    return families, pricing, curves
