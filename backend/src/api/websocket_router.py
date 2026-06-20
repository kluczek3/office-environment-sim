import json
import os
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

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
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            prof_data = data.get(agent_id)
            if prof_data:
                return AgentProfile(**prof_data)
        return None
    except Exception as e:
        print(f"⚠️ Failed to load profile for {agent_id}: {e}")
        return None


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
        event = IncomingEvent.model_validate_json(raw_json)
        
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
        # TODO: Here you will integrate the planner's QA generation logic
        # e.g., answer_text = await planner.answer_question(question)
        answer_text = f"My localized LLM will process: '{question}' based on my MemoryStream."
    
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

        available_targets = ["boss_chair_0", "office_chair_1", "chill_0", "conference_0"] # MOCK

        orchestrator.process_event(
            event_type=event.type,
            agent_id=agent_id,
            data=event.data if event.data else {}
        )

        current_loc = event.data.get("current_location", "unknown_location") if event.data else "spawn_point"

        commands_list = await planner.determine_next_actions(
            current_location=current_loc, 
            available_targets=available_targets
        )
        
        # Mocking the action for now to ensure Unity compatibility
        commands_list.append(
            NetworkCommand(
                type="Idle",
                target_id="",
                duration=3.0,
                thought="Thinking about my next action..."
            )
        )
    else:
        commands_list.append(NetworkCommand(type="Idle", target_id="", duration=3.0, thought="No brain found."))

    response = BackendResponse(
        type="commands",
        agent_id=agent_id,
        commands=commands_list
    )
    await manager.broadcast_response(response)
