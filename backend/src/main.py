from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.websocket_router import router as ws_router

app = FastAPI(title="Office Environment Simulation Backend")

# Allow CORS for potential web dashboards or Unity components
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)

@app.get("/api/system/health")
async def health_check():
    return {"status": "ok", "message": "Simulation backend is running."}

import os
import json

@app.post("/api/agents/seed")
async def seed_agents():
    """Initializes workforce persona and graph boundaries from configuration."""
    profile_path = os.path.join(os.path.dirname(__file__), "..", "config", "profiles.json")
    if not os.path.exists(profile_path):
        return {"status": "error", "message": "profiles.json not found."}
        
    with open(profile_path, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)
        
    seeded_agents = []
    # Seed relationships and initialize them for simulation
    for agent_id, profile in profiles_data.items():
        relationships = profile.get("relationships", {})
        seeded_agents.append({
            "agent_id": agent_id,
            "name": profile.get("name"),
            "relationship_boundaries": len(relationships)
        })
        
    return {"status": "seeded", "message": f"{len(seeded_agents)} Agents initialized.", "agents": seeded_agents}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
