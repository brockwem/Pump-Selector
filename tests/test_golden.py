from fastapi.testclient import TestClient
from app.main import app, API_KEY
import json
client = TestClient(app)
def test_golden_cases():
    with open("sample_data/golden_cases.json") as f:
        cases = json.load(f)
    for c in cases:
        r = client.post("/hydraulics/select", json=c["request"], headers={"x-api-key": API_KEY})
        assert r.status_code == 200
        data = r.json()
        if c["expected"] == "FAIL":
            assert len(data.get("candidates",[])) == 0
        else:
            assert len(data.get("candidates",[])) > 0
