import sys
import json
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

from fastapi.testclient import TestClient
from backend.app.main import app

def test_ui_endpoint():
    client = TestClient(app)
    
    # Simulate the EXACT payload the React frontend sends when a user clicks 'Generate'
    # For mat_g3_na_q2_5, easiest profile
    axis_values = json.dumps({
        "max_difference": 0.0,
        "number_difficulty": 0.0
    })
    
    response = client.get(
        f"/api/matatag/lab/generate?node_id=mat_g3_na_q2_5&axis_values={axis_values}&format_preference=auto"
    )
    
    print("Status:", response.status_code)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_ui_endpoint()
