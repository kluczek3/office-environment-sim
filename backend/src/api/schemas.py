from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal, Union, Any


class AgentRelationship(BaseModel):
    target_agent_id: str
    trust_level: float = Field(default=0.5, ge=0.0, le=1.0)
    interaction_count: int = 0
    notes: str = ""

class AgentNeeds(BaseModel):
    physiological: float = Field(default=1.0, ge=0.0, le=1.0, description="Basic survival needs (energy, thirst).")
    safety: float = Field(default=1.0, ge=0.0, le=1.0, description="Need for security and stability.")
    social: float = Field(default=1.0, ge=0.0, le=1.0, description="Need for love, belonging, and interaction.")
    esteem: float = Field(default=1.0, ge=0.0, le=1.0, description="Need for respect, self-esteem, and status.")
    self_actualization: float = Field(default=1.0, ge=0.0, le=1.0, description="Desire to become the most that one can be.")

class AgentProfile(BaseModel):
    agent_id: str
    name: str
    personality_traits: List[str]
    current_stress_level: float = 0.0
    needs: AgentNeeds = Field(default_factory=AgentNeeds)
    relationships: Dict[str, AgentRelationship] = Field(default_factory=dict)


# --- FRONTEND -> BACKEND ---

class AgentInitInfo(BaseModel):
    agentId: str
    role: str
    assignedChairId: str

class InitializationData(BaseModel):
    agents: List[AgentInitInfo]
    zones: List[str]

class UserQuestionData(BaseModel):
    targetAgentId: str
    question: str

class InitEventRequest(BaseModel):
    type: Literal["daystarted"]
    agent_id: str
    timestamp: float
    data: InitializationData

class QuestionEventRequest(BaseModel):
    type: Literal["ask_question"]
    agent_id: str
    timestamp: float
    data: UserQuestionData

class ActionRequestEvent(BaseModel):
    type: Literal["request_commands"]
    agent_id: str
    timestamp: float
    data: Optional[Dict[str, Any]] = None 

IncomingEvent = Union[InitEventRequest, QuestionEventRequest, ActionRequestEvent]



class NetworkCommand(BaseModel):
    type: str
    target_id: str
    duration: float
    thought: str

class BackendResponse(BaseModel):
    type: str = "commands"
    agent_id: str
    answer: str = ""
    commands: List[NetworkCommand]