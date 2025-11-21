from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import datetime
def generate_pdf(path_or_buf, selection: dict, meta: dict):
    c = canvas.Canvas(path_or_buf, pagesize=LETTER)
    w,h = LETTER; y=h-50
    c.setFont("Helvetica-Bold",14); c.drawString(50,y,meta.get("title","Pump Selection Datasheet")); y-=20
    c.setFont("Helvetica",9)
    c.drawString(50,y,f"Generated: {datetime.utcnow().isoformat()}Z"); y-=14
    c.drawString(50,y,f"Curvepack: {meta.get('curvepack','unknown')}"); y-=14
    c.drawString(50,y,f"Quote ID: {meta.get('quote_id','N/A')}"); y-=22
    c.setFont("Helvetica-Bold",11); c.drawString(50,y,"Selected Pump"); y-=14; c.setFont("Helvetica",9)
    for k in ["family_id","model","speed_rpm","impeller_d_mm","eta_pct","bep_offset_pctQ","head_ft","power_hp","npshr_ft","motor_hp","price_band","lead_time","score"]:
        c.drawString(60,y,f"{k}: {selection.get(k)}"); y-=12
    c.showPage(); c.save()
