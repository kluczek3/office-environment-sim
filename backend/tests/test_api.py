import pytest
from fastapi.testclient import TestClient
from src.main import app
import json

client = TestClient(app)

def test_health_check():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Simulation backend is running."}

def test_seed_agents():
    response = client.post("/api/agents/seed")
    assert response.status_code == 200
    assert response.json()["status"] == "seeded"

def test_websocket_spatial_trigger():
    with client.websocket_connect("/ws/simulation") as websocket:
        event = {
            "type": "spatial_trigger",
            "agent_id": "agent_1",
            "timestamp": 12345.6,
            "data": {"zone": "Kitchen"}
        }
        websocket.send_text(json.dumps(event))
        data = websocket.receive_text()
        response = json.loads(data)
        
        assert response["status"] == "processed"
        assert response["action"] == "update_modifiers"
        assert response["agent_id"] == "agent_1"

def test_websocket_invalid_json():
    with client.websocket_connect("/ws/simulation") as websocket:
        websocket.send_text("this is not json")
        data = websocket.receive_text()
        response = json.loads(data)
        
        assert response.get("error") == "Invalid format"
