import os
import json
import subprocess
import threading
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.websocket_router import router as ws_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Office Environment Simulation Backend")

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

@app.post("/api/agents/seed")
async def seed_agents():
    profile_path = os.path.join(os.path.dirname(__file__), "..", "config", "profiles.json")
    if not os.path.exists(profile_path):
        return {"status": "error", "message": "profiles.json not found."}

    with open(profile_path, "r", encoding="utf-8-sig") as f:
        profiles_data = json.load(f)

    seeded_agents = []
    for agent_id, profile in profiles_data.items():
        relationships = profile.get("relationships", {})
        seeded_agents.append({
            "agent_id": agent_id,
            "name": profile.get("name"),
            "relationship_boundaries": len(relationships)
        })

    return {"status": "seeded", "message": f"{len(seeded_agents)} Agents initialized.", "agents": seeded_agents}

def launch_unity_simulation():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    build_path = os.path.normpath(os.path.join(base_dir, "..", "..", "frontend", "Builds", "office-sim-v0.1.0.app"))

    time.sleep(10.0)
    if os.path.exists(build_path):
        try:
            print(f"🎮 Launching Unity simulation window")
            subprocess.Popen(["open", "-a", build_path])
        except Exception as e:
            print(f"⚠️ Error launching Unity build: {e}")
    else:
        print(f"⚠️ Unity build not found in: {build_path}")

if __name__ == "__main__":
    import uvicorn

    if os.environ.get("RUN_MAIN_FROM_WERKZEUG") is None and os.environ.get("UVICORN_ALREADY_RUNNING") is None:
        os.environ["UVICORN_ALREADY_RUNNING"] = "1"
        launcher_thread = threading.Thread(target=launch_unity_simulation, daemon=True)
        launcher_thread.start()

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)