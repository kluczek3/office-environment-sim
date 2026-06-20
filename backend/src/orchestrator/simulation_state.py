class SimulationOrchestrator:
    def __init__(self):
        self.productivity_index = 100.0  # Base level
        self.active_agents = set()
        self.available_targets = []
        self.agent_locations = {}

    def add_agent(self, agent_id: str):
        self.active_agents.add(agent_id)

    def remove_agent(self, agent_id: str):
        if agent_id in self.active_agents:
            self.active_agents.remove(agent_id)

    def update_agent_location(self, agent_id: str, location: str) -> list:
        self.agent_locations[agent_id] = location
        co_located_agents = []
        
        if location not in ["spawn_point", "unknown_location"] and ("chill" in location or "conference" in location):
            for other_id, loc in self.agent_locations.items():
                if other_id != agent_id and loc == location:
                    co_located_agents.append(other_id)
                    
        return co_located_agents

    def setup_environment(self, init_data: dict):
        targets = set()
        
        if "zones" in init_data:
            for zone in init_data["zones"]:
                targets.add(zone)
        
        if "agents" in init_data:
            for agent in init_data["agents"]:
                if "assignedChairId" in agent:
                    targets.add(agent["assignedChairId"])
                    
        self.available_targets = list(targets)
        print(f"🌍 Updated simulation map. Available locations: {len(self.available_targets)}")

    def get_available_targets(self) -> list:
        return self.available_targets
    
    def get_active_global_event(self, agent_id: str, role: str, current_time_str: str) -> dict:
        if current_time_str == "13:00":
            if role == "Boss" or agent_id == "agent_1":
                return {
                    "room": "conference_0", 
                    "description": "Huge meeting (conference_0; chairs: conference_big_X; whiteboard: whiteboard_1)"
                }
            else:
                return {
                    "room": "conference_1", 
                    "description": "Small presentation (conference_1; chairs: conference_small_X; blackboard: blackboard_1)"
                }
        return None

    def process_event(self, event_type: str, agent_id: str, data: dict):
        """Main event loop logic to coordinate memory logging and LLM triggers."""
        # Check if this interaction contains a high-cognitive-load rumor
        if event_type == "interaction" and "shock_value" in data:
            cognitive_load = float(data.get("shock_value", 0)) * 2
            self.update_productivity(cognitive_load)
            return {"status": "requires_evaluation", "load": cognitive_load}
        return {"status": "ignored"}
        
    def update_productivity(self, cognitive_load: float):
        """Drops overall productivity if agents are distracted by heavy cognitive load/rumors."""
        self.productivity_index -= cognitive_load
        if self.productivity_index < 0:
            self.productivity_index = 0