import random


class SimulationOrchestrator:
    def __init__(self):
        self.productivity_index = 100.0
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

    def get_available_targets(self) -> list:
        return self.available_targets

    def get_active_global_event(self, agent_id: str, role: str, current_time_str: str) -> dict:
        agent_idx = 0
        parts = agent_id.split('_')
        if len(parts) > 1 and parts[-1].isdigit():
            agent_idx = int(parts[-1])

        is_boss = (agent_id == "agent_0")

        if "09:00" <= current_time_str < "10:00":
            if not is_boss:
                return {
                    "room": f"chill_{random.randint(0, 2)}",
                    "description": "Morning coffee routine. Grab a coffee and chat with others before work."
                }
            else:
                return {
                    "room": "boss_chair",
                    "description": "Morning routine. Go to your boss_chair and review strategic documents."
                }

        elif "10:30" <= current_time_str < "11:30":
            if not is_boss:
                if agent_id == "agent_1":
                    return {
                        "room": "blackboard_1",
                        "description": "Small team sync. You are presenting the report at the blackboard."
                    }
                elif agent_idx > 2 and agent_idx < 9:
                    return {
                        "room": f"conference_small_{agent_idx}",
                        "description": "Small team sync. Listen to agent_1's presentation."
                    }
            else:
                return {
                    "room": "boss_chair",
                    "description": "Team is syncing. Stay at your boss_chair and manage the company."
                }

        elif "12:00" <= current_time_str < "13:00":
            chill_room = f"chill_{agent_idx % 3}"
            return {
                "room": chill_room,
                "description": "Lunch break time. Go to a chill area, eat, and relax."
            }

        elif "13:00" <= current_time_str < "14:00":
            if is_boss:
                return {
                    "room": "blackboard_0",
                    "description": "Company-wide presentation. You are presenting the new strategy at the blackboard."
                }
            else:
                return {
                    "room": f"conference_chair_{agent_idx}",
                    "description": "Mandatory company meeting. Sit at your designated conference chair and listen to the Boss."
                }

        elif "15:00" <= current_time_str < "15:30":
            if agent_id == "agent_2":
                return {
                    "room": "chill_1",
                    "description": "You just heard a huge rumor about company layoffs! Find someone in the chill zone to tell them."
                }

        return None

    def process_event(self, event_type: str, agent_id: str, data: dict):
        if event_type == "interaction" and "shock_value" in data:
            cognitive_load = float(data.get("shock_value", 0)) * 2
            self.update_productivity(cognitive_load)
            return {"status": "requires_evaluation", "load": cognitive_load}
        return {"status": "ignored"}

    def update_productivity(self, cognitive_load: float):
        self.productivity_index -= cognitive_load
        if self.productivity_index < 0:
            self.productivity_index = 0