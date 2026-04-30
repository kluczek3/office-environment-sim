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

@app.post("/api/agents/seed")
async def seed_agents():
    # TODO: Implement workforce persona and graph boundaries initialization
    return {"status": "seeded", "message": "Agents initialized."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
