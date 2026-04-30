import json
from typing import List
from src.api.schemas import AgentProfile

class CognitivePlanner:
    def __init__(self, agent_id: str, llm_provider, profile: AgentProfile = None, memory_stream = None):
        self.agent_id = agent_id
        self.llm_provider = llm_provider
        self.profile = profile
        self.memory_stream = memory_stream
        self.macro_plan = []

    async def generate_daily_plan(self) -> str:
        """Top-down planning: creates large time blocks for the agent."""
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        sys_prompt = f"You are agent {self.agent_id}, a {personality} person. Create a daily schedule covering 9 AM to 5 PM with broad hourly goals."
        user_prompt = "Return exactly 5 daily macro blocks in JSON format."
        res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        self.macro_plan = res
        return res

    async def breakdown_plan(self, macro_block: dict) -> List[dict]:
        """Recursive breakdown: converts macro blocks into specific engine actions."""
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        sys_prompt = (
            f"You are agent {self.agent_id}, a {personality} person. "
            f"Deconstruct the macro action: '{macro_block}'. "
            "Output an array of specific, sequential engine actions. "
            "Allowed actions: ['move_to', 'sit_down', 'stand_up', 'interact', 'work', 'speak']."
        )
        user_prompt = "Return the micro actions strictly as JSON list."
        res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        # Update monitoring narrative based on the new breakdown
        self.narrative_summary = f"Currently executing: {macro_block}"
        return res

    async def self_monitor(self) -> str:
        """Asynchronous self-monitoring to maintain a narrative summary of recent events."""
        if not self.memory_stream or not hasattr(self, 'narrative_summary'):
            return "No narrative context"
        sys_prompt = f"You are agent {self.agent_id}. Your current main goal is: {self.narrative_summary}. Synthesize recent events to ensure you stay on task."
        user_prompt = "Provide a 1-sentence internal monologue of your status. Output JSON with a 'status' key."
        res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        if isinstance(res, dict) and 'status' in res:
            self.narrative_summary = res['status']
        return res

    async def evaluate_stimulus(self, stimulus_data: dict, spatial_modifiers: list) -> str:
        """
        Multistage evaluation: processing an event using LLM when cognitively necessary.
        Injects spatial affordances (e.g. 'Informality_On' in kitchen) during evaluation.
        """
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        stress = self.profile.current_stress_level if self.profile else 0.0
        needs = self.profile.needs.model_dump() if self.profile else {}
        
        relevant_memories_text = "No relevant memories."
        if self.memory_stream:
            query = str(stimulus_data)
            memories = self.memory_stream.retrieve_memories(self.agent_id, query, limit=5)
            if memories:
                relevant_memories_text = "\n".join([f"- {m.page_content}" for m in memories])

        sys_prompt = (
            f"You are agent {self.agent_id}, a {personality} person with a current stress level of {stress}. "
            f"Your current needs fulfillment levels (0.0 to 1.0, where 1.0 is fully satisfied) are: {needs}. Take these into account when making decisions. "
            f"Event: {stimulus_data}. Current physical environment modifiers: {spatial_modifiers}.\n"
            f"Relevant past memories:\n{relevant_memories_text}"
        )
        user_prompt = "Given your personality traits, stress level, needs fulfillment, memories, and environment, do you engage or ignore the stimulus? Output JSON."
        res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        
        # After evaluating, log the event to memory
        if self.memory_stream:
            self.memory_stream.add_memory(self.agent_id, f"Experienced event: {stimulus_data}", importance=5.0)
            
        return res
