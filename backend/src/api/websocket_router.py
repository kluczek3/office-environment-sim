import json
import os
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError, TypeAdapter

from src.orchestrator.simulation_state import SimulationOrchestrator
from src.agent.planner import CognitivePlanner
from src.llm.provider import LLMProvider
from src.agent.memory_stream import MemoryStream

# Importing our newly defined schemas
from src.api.schemas import (
    AgentProfile,
    IncomingEvent,
    InitEventRequest,
    QuestionEventRequest,
    ActionRequestEvent,
    BackendResponse,
    NetworkCommand
)

router = APIRouter()
orchestrator = SimulationOrchestrator()

# ==========================================
# MODEL & SYSTEM INITIALIZATION
# ==========================================

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
    """Loads agent personality and profile from configuration file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "profiles.json")
        if not os.path.exists(config_path):
            return None
        with open(config_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            prof_data = data.get(agent_id)
            if prof_data:
                return AgentProfile(**prof_data)
        return None
    except Exception as e:
        print(f"⚠️ Failed to load profile for {agent_id}: {e}")
        return None

def save_agent_profile(agent_id: str, profile: AgentProfile):
    """Saves updated agent personality and relationships to the configuration file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "profiles.json")
        if not os.path.exists(config_path):
            print(f"⚠️ Could not find config file: {config_path}")
            return
            
        with open(config_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            
        data[agent_id] = profile.model_dump()
        
        with open(config_path, "w", encoding="utf-8-sig") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print(f"⚠️ Failed to save profile for {agent_id}: {e}")

# ==========================================
# CONNECTION MANAGER
# ==========================================

class ConnectionManager:
    """Manages global WebSocket connections with the Unity client."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("🟢 Unity simulation connected successfully!")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("🔴 Unity simulation disconnected.")

    async def broadcast_response(self, response: BackendResponse):
        """Broadcasts a Pydantic response object as JSON to all active Unity instances."""
        json_data = response.model_dump_json()
        for connection in self.active_connections:
            await connection.send_text(json_data)

manager = ConnectionManager()


# ==========================================
# ROUTER & EVENT LOOP
# ==========================================

@router.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            await process_incoming_message(raw_data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"⚠️ Unexpected error in websocket main loop: {e}")
        manager.disconnect(websocket)


async def process_incoming_message(raw_json: str):
    """Parses incoming JSON and routes it to the appropriate handler based on event type."""
    try:
        # Pydantic magically validates and instantiates the correct event class
        adapter = TypeAdapter(IncomingEvent)
        event = adapter.validate_json(raw_json)
        
        # Route the event
        if isinstance(event, InitEventRequest):
            await handle_day_started(event)
            
        elif isinstance(event, QuestionEventRequest):
            await handle_question(event)
            
        elif isinstance(event, ActionRequestEvent):
            await handle_action_request(event)

    except ValidationError as e:
        print("❌ Data validation error (Mismatch with C# contract):")
        print(e.json())
    except Exception as e:
        print(f"❌ Error processing message: {e}")


# ==========================================
# EVENT HANDLERS
# ==========================================

async def handle_day_started(event: InitEventRequest):
    """Handles simulation initialization, instantiating planners and agents."""
    print(f"🌅 Day started! Registered agents: {len(event.data.agents)}")
    
    orchestrator.setup_environment(event.data.model_dump())
    
    # Process through Orchestrator
    orchestrator.process_event(
        event_type=event.type,
        agent_id=event.agent_id,
        data=event.data.model_dump()
    )

    # Initialize planners for all agents sent by Unity
    for agent_info in event.data.agents:
        agent_id = agent_info.agentId
        
        if agent_id not in active_planners:
            orchestrator.add_agent(agent_id)
            profile = load_agent_profile(agent_id)
            
            # Create a localized "brain" for each agent
            active_planners[agent_id] = CognitivePlanner(
                agent_id=agent_id, 
                llm_provider=llm_provider, 
                profile=profile, 
                memory_stream=global_memory_stream
            )
            print(f"🧠 Cognitive Planner initialized for: {agent_id}")

    # Note: We do not send commands back immediately on day_started.
    # We wait for agents to request actions once they spawn.


async def handle_question(event: QuestionEventRequest):
    """Handles external QA requests directed at a specific agent."""
    target_id = event.data.targetAgentId
    question = event.data.question
    
    print(f"💬 Question to agent [{target_id}]: {question}")
    
    planner = active_planners.get(target_id)
    answer_text = "I have no brain initialized to answer this!"

    if planner:
        answer_text = await planner.answer_question(question)
    
    response = BackendResponse(
        type="qa_response",
        agent_id=target_id,
        answer=answer_text,
        commands=[]
    )
    await manager.broadcast_response(response)


async def handle_action_request(event: ActionRequestEvent):
    """Handles a request from an agent looking for their next task/command."""
    agent_id = event.agent_id
    print(f"🤖 Agent [{agent_id}] requests new commands.")
    
    planner = active_planners.get(agent_id)
    commands_list = []

    if planner:
        # Process context through orchestrator
        orchestrator.process_event(
            event_type=event.type,
            agent_id=agent_id,
            data=event.data if event.data else {}
        )

        available_targets = orchestrator.get_available_targets()
        if not available_targets:
             available_targets = ["spawn_point"]

        current_loc = event.data.get("current_location", "unknown_location") if event.data else "spawn_point"
        current_time = event.data.get("current_time", "09:00") if event.data else "09:00"
        co_located_agents = orchestrator.update_agent_location(agent_id, current_loc)
        
        if co_located_agents and planner.profile:
            for other_agent in co_located_agents:
                # Zainicjuj relację, jeśli wcześniej się nie znali
                if other_agent not in planner.profile.relationships:
                    from src.api.schemas import AgentRelationship
                    planner.profile.relationships[other_agent] = AgentRelationship(target_agent_id=other_agent, trust_level=0.5)
                
                rel = planner.profile.relationships[other_agent]
                
                if rel.trust_level < 1.0:
                    rel.trust_level = min(1.0, rel.trust_level + 0.05)
                    rel.interaction_count += 1
                    print(f"🤝 Interaction! {agent_id} spends time with {other_agent} in zone {current_loc}. Trust level: {rel.trust_level:.2f}")
            
            save_agent_profile(agent_id, planner.profile)

        agent_role = planner.profile.role if planner.profile and hasattr(planner.profile, 'role') else "Worker"
        
        active_event = orchestrator.get_active_global_event(agent_id, agent_role, current_time)

        commands_list = await planner.determine_next_actions(
            current_location=current_loc, 
            available_targets=available_targets,
            current_time=current_time,
            global_event=active_event
        )
        
    else:
        commands_list.append(NetworkCommand(type="Idle", target_id="", duration=3.0, thought="No brain found."))

    response = BackendResponse(
        type="commands",
        agent_id=agent_id,
        commands=commands_list
    )
    await manager.broadcast_response(response)
