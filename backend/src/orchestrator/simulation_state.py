class SimulationOrchestrator:
    def __init__(self):
        self.productivity_index = 100.0  # Base level
        self.active_agents = set()

    def add_agent(self, agent_id: str):
        self.active_agents.add(agent_id)

    def remove_agent(self, agent_id: str):
        if agent_id in self.active_agents:
            self.active_agents.remove(agent_id)

    def process_event(self, event_type: str, agent_id: str, data: dict):
        """Main event loop logic to coordinate memory logging and LLM triggers."""
        # E.g. Check if this is a high-cognitive-load rumor
        if event_type == "RUMOR_RECEIVED":
            cognitive_load = float(data.get("shock_value", 0)) * 2
            self.update_productivity(cognitive_load)
            return {"status": "requires_evaluation", "load": cognitive_load}
        return {"status": "ignored"}
        
    def update_productivity(self, cognitive_load: float):
        """Drops overall productivity if agents are distracted by heavy cognitive load/rumors."""
        self.productivity_index -= cognitive_load
        if self.productivity_index < 0:
            self.productivity_index = 0

