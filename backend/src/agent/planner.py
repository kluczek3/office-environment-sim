import json
from typing import List, Dict, Any, Optional
from src.api.schemas import AgentProfile, NetworkCommand

class CognitivePlanner:
    """
    The 'Brain' of the agent. Responsible for translating high-level goals 
    into low-level Unity engine commands (Move, Interact, Idle).
    """
    def __init__(self, agent_id: str, llm_provider, profile: Optional[AgentProfile] = None, memory_stream = None):
        self.agent_id = agent_id
        self.llm_provider = llm_provider
        self.profile = profile
        self.memory_stream = memory_stream
        
        # High-level goals
        self.macro_plan: List[Dict[str, str]] = []
        self.current_narrative_goal: str = "Awaiting day start."

    async def generate_daily_plan(self) -> List[Dict[str, str]]:
        """
        Top-down planning: creates large time blocks for the agent.
        """
        role = self.profile.role if hasattr(self.profile, 'role') else "Employee"
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        
        sys_prompt = (
            f"You are {self.profile.name if self.profile else self.agent_id}, working as a {role}. "
            f"Your personality: {personality}. "
            "Create a broad daily schedule covering 9 AM to 5 PM."
        )
        user_prompt = (
            "Return exactly 5 daily macro blocks. Must be a valid JSON array of objects with keys: "
            "'time' (e.g., '09:00'), 'task' (e.g., 'Morning meeting'), 'duration_minutes'."
        )
        
        res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        
        if isinstance(res, list):
            self.macro_plan = res
        elif isinstance(res, dict) and 'plan' in res:
            self.macro_plan = res['plan']
            
        return self.macro_plan

    async def determine_next_actions(self, current_location: str, available_targets: List[str]) -> List[NetworkCommand]:
        """
        The core loop. Translates the current macro goal and environment into strict Engine Commands.
        This is called by the WebSocket Router when the agent finishes their previous task.
        """
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        needs = self.profile.needs.model_dump() if self.profile else {}
        
        # Build strict rules for the LLM so it doesn't hallucinate target IDs or action types
        sys_prompt = (
            f"You are agent {self.agent_id}, a {personality} person.\n"
            f"Your current macro-level goal is: '{self.current_narrative_goal}'.\n"
            f"Your physical needs fulfillment levels (1.0 is full, 0.0 is empty): {needs}.\n\n"
            
            f"--- ENVIRONMENT RULES ---\n"
            f"You are currently at: '{current_location}'.\n"
            f"You can only interact with or move to the following known targets: {available_targets}.\n\n"
            
            f"--- ENGINE COMMAND RULES ---\n"
            f"You must output a sequence of immediate actions to progress your goal. "
            f"Allowed 'type' values strictly limited to: ['Move', 'Interact', 'Idle'].\n"
            f"- Move: requires 'target_id' from the available targets list. 'duration' must be 0.\n"
            f"- Interact: requires 'target_id' (must be at your location) and 'duration' in seconds.\n"
            f"- Idle: 'target_id' is empty. Requires 'duration' in seconds (e.g., waiting, listening).\n"
            f"Always include a brief inner 'thought' explaining your reasoning."
        )
        
        user_prompt = (
            "Based on your current goal and environment, generate the next 1 to 2 actions. "
            "Output strictly as a JSON array of objects matching this schema: "
            "[{'type': 'Move|Interact|Idle', 'target_id': 'string', 'duration': float, 'thought': 'string'}]"
        )
        
        raw_res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        
        # Parse the LLM output into Pydantic models for safety
        commands = []
        try:
            # Handle cases where LLM wraps array in a dict, e.g. {"commands": [...]}
            data_list = raw_res.get("commands", raw_res) if isinstance(raw_res, dict) else raw_res
            
            for item in data_list:
                command = NetworkCommand(**item)
                # Validation fallback: ensure target_id is valid if it's a Move command
                if command.type == "Move" and command.target_id not in available_targets:
                    command.thought += " (Wait, I don't know where that is. I will Idle instead)."
                    command.type = "Idle"
                    command.target_id = ""
                    command.duration = 5.0
                
                commands.append(command)
                
            # Update internal monologue
            if commands:
                self.current_narrative_goal = f"Executing: {commands[-1].thought}"
                
        except Exception as e:
            print(f"⚠️ Failed to parse LLM actions for {self.agent_id}: {e}")
            # Fallback action to prevent simulation freeze
            commands.append(NetworkCommand(type="Idle", target_id="", duration=5.0, thought="I am confused."))

        return commands

    async def evaluate_stimulus(self, stimulus_data: dict, spatial_modifiers: list) -> str:
        """
        Multistage evaluation: processing an unexpected event (like being spoken to or an emergency).
        """
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        stress = self.profile.current_stress_level if self.profile else 0.0
        
        relevant_memories_text = "No relevant memories."
        if self.memory_stream:
            query = str(stimulus_data)
            memories = self.memory_stream.retrieve_memories(self.agent_id, query, limit=3)
            if memories:
                relevant_memories_text = "\n".join([f"- {m.page_content}" for m in memories])

        sys_prompt = (
            f"You are agent {self.agent_id}, a {personality} person with a stress level of {stress}. "
            f"Unexpected Event: {stimulus_data}. Physical environment modifiers: {spatial_modifiers}.\n"
            f"Relevant past memories:\n{relevant_memories_text}"
        )
        
        user_prompt = (
            "Do you engage with this event or ignore it? If it changes your current plans, "
            "explain what your new focus is. Output JSON with a 'decision' and 'new_narrative_goal' key."
        )
        
        res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        
        # If the LLM decides the event is important, we change the agent's current focus
        if isinstance(res, dict) and 'new_narrative_goal' in res:
            self.current_narrative_goal = res['new_narrative_goal']
            
        if self.memory_stream:
            self.memory_stream.add_memory(self.agent_id, f"Experienced: {stimulus_data}. Reaction: {res.get('decision', 'Ignored')}", importance=7.0)
            
        return res
