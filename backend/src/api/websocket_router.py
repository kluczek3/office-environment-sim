import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
from src.orchestrator.simulation_state import SimulationOrchestrator
from src.agent.planner import CognitivePlanner
from src.llm.provider import LLMProvider
from src.api.schemas import AgentProfile
from src.agent.memory_stream import MemoryStream
import os

router = APIRouter()
orchestrator = SimulationOrchestrator()

LOCAL_MODEL = True

if LOCAL_MODEL:
    llm_provider = LLMProvider(model_name="llama3")
else:
    llm_provider = LLMProvider()
    openai_key = os.getenv("OPENAI_API_KEY", "API_KEY")
    llm_provider.switch_to_cloud(provider="openai", api_key=openai_key)

global_memory_stream = MemoryStream()
active_planners: Dict[str, CognitivePlanner] = {}

def load_agent_profile(agent_id: str) -> Optional[AgentProfile]:
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "profiles.json")
        if not os.path.exists(config_path):
            return None
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            prof_data = data.get(agent_id)
            if prof_data:
                return AgentProfile(**prof_data)
        return None
    except Exception:
        return None

class ConnectionManager:
    def __init__(self):
        # We store the associated agent_id with each websocket connection to handle disconnects
        self.active_connections: Dict[WebSocket, Optional[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = None

    def bind_agent(self, websocket: WebSocket, agent_id: str):
        self.active_connections[websocket] = agent_id
        orchestrator.add_agent(agent_id)
        if agent_id not in active_planners:
            profile = load_agent_profile(agent_id)
            active_planners[agent_id] = CognitivePlanner(agent_id, llm_provider, profile=profile, memory_stream=global_memory_stream)

    def disconnect(self, websocket: WebSocket):
        agent_id = self.active_connections.get(websocket)
        if agent_id:
            orchestrator.remove_agent(agent_id)
            # Optionally remove from active_planners, or keep for persistence
        if websocket in self.active_connections:
            del self.active_connections[websocket]

    async def broadcast(self, message: str):
        for connection in self.active_connections.keys():
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Parse Unity events
            try:
                payload = json.loads(data)
                event_type = payload.get("type", "unknown")
                agent_id = payload.get("agent_id")
                event_data = payload.get("data", {})
                
                if agent_id:
                    manager.bind_agent(websocket, agent_id)
                
                # Forward to Orchestrator based on the request
                orchestrator_result = orchestrator.process_event(
                    event_type=event_type, 
                    agent_id=agent_id, 
                    data=event_data
                )
                
                # Retrieve the cognitive planner for the agent
                planner = active_planners.get(agent_id)

                # Route events to the planner or basic handling
                if event_type == "spatial_trigger":
                    response = {"status": "processed", "action": "update_modifiers", "agent_id": agent_id, **orchestrator_result}
                elif event_type == "day_ended":
                    if planner:
                         # Trigger reflection on day end
                         await planner.memory_stream.summarize_and_forget(agent_id, llm_provider)
                    response = {"status": "processed", "action": "reflection_triggered", "agent_id": agent_id}
                elif event_type == "interaction":
                    if planner:
                        # Evaluate stimulus through LLM when there's an interaction
                        spatial_modifiers = event_data.get("modifiers", [])
                        plan_result = await planner.evaluate_stimulus(event_data, spatial_modifiers)
                        try:
                            decision = json.loads(plan_result)
                        except json.JSONDecodeError:
                            decision = {"raw": plan_result}
                    else:
                        decision = {}
                        
                    response = {"status": "processed", "action": "evaluate_stimulus", "agent_id": agent_id, "decision": decision, **orchestrator_result}
                else:
                    response = {"status": "received", "event": payload, **orchestrator_result}

                await manager.broadcast(json.dumps(response))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid format"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
