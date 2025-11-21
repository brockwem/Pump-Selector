# Pump Selector — Standalone (Option A)
This is a standalone FastAPI service that reads pump curve CSVs, runs selection math, and returns JSON + 1-page PDF.
## Subscriptions
- Render/Railway/Fly.io (API hosting)
- Retool Cloud (internal UI)
- Optional S3 (later)
## Local run
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATA_DIR=./sample_data
export CURVEPACK_VERSION=curvepack_demo_2025-07-28
export API_KEY=changeme-very-secret
uvicorn app.main:app --reload --port 8080
## Test
curl http://localhost:8080/health
## Golden tests
pytest -q
