import json
import re
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

    async def determine_next_actions(self, current_location: str, available_targets: List[str], current_time: str = "09:00", global_event: dict = None) -> List[NetworkCommand]:
        """
        The core loop. Translates the current macro goal and environment into strict Engine Commands.
        """
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        needs = self.profile.needs.model_dump() if self.profile else {}
        
        override_instruction = ""
        if global_event:
            target_room = global_event["room"]
            desc = global_event["description"]
            override_instruction = (
                f"\n\n--- CRITICAL SCHEDULE OVERRIDE ---\n"
                f"Current time is {current_time}. You have a CRITICAL business event: '{desc}' in location '{target_room}'.\n"
                f"This is your top priority at this moment! All other plans are secondary.\n"
                f"- If you are NOT in '{target_room}' (your current location is '{current_location}'), your next action MUST be 'Move' to '{target_room}'.\n"
                f"- If you ARE already in '{target_room}', your action MUST be 'Interact' with this object or 'Idle' (listening to the presentation).\n"
                f"You are not allowed to go anywhere else while this event is happening."
            )

        sys_prompt = (
            f"You are agent {self.agent_id}, a {personality} person.\n"
            f"Your current time is: {current_time}.\n"
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
            f"{override_instruction}"
        )
        
        user_prompt = (
            "Based on your current goal and environment, generate the next 1 to 2 actions. "
            "Output strictly as a JSON array of objects matching this schema: "
            "[{'type': 'Move|Interact|Idle', 'target_id': 'string', 'duration': float, 'thought': 'string'}]"
        )
        
        raw_res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)
        
        commands = []
        try:
            data_list = raw_res.get("commands", raw_res) if isinstance(raw_res, dict) else raw_res
            
            for item in data_list:
                command = NetworkCommand(**item)
                if command.type == "Move" and command.target_id not in available_targets:
                    command.thought += " (Wait, I don't know where that is. I will Idle instead)."
                    command.type = "Idle"
                    command.target_id = ""
                    command.duration = 5.0
                
                commands.append(command)
                
            if commands:
                self.current_narrative_goal = f"Executing: {commands[-1].thought}"
                
        except Exception as e:
            print(f"⚠️ Failed to parse LLM actions for {self.agent_id}: {e}")
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
            
        importance_score = 5.0
        try:
            score_sys_prompt = "You are a cognitive evaluation module for an office simulation agent. Your task is to assess how impactful a given event is on the agent's mental state and productivity."
            score_user_prompt = (
                f"On a scale from 1 to 10, how important and memorable is the following event for a person with the profile: {personality}?\n"
                f"Event: {stimulus_data}\n"
                f"Return ONLY the number (e.g., 3, 7, or 10), without any additional text."
            )
            raw_score = await self.llm_provider.get_completion(score_sys_prompt, score_user_prompt, require_json=False)
            
            match = re.search(r'\d+', str(raw_score))
            if match:
                importance_score = float(match.group())
                importance_score = min(max(importance_score, 1.0), 10.0)
                
        except Exception as e:
            print(f"⚠️ Could not dynamically evaluate the importance of the memory for {self.agent_id}: {e}")

        if self.memory_stream:
            self.memory_stream.add_memory(
                self.agent_id, 
                f"Experienced: {stimulus_data}. Reaction: {res.get('decision', 'Ignored')}", 
                importance=importance_score
            )
            print(f"🧠 [Memory] Saved memory for {self.agent_id} with importance: {importance_score}/10")
            
        return res

    async def answer_question(self, question: str) -> str:
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        role = self.profile.role if hasattr(self.profile, 'role') else "Employee"
        
        relevant_memories_text = "No relevant memories found."
        
        if self.memory_stream:
            memories = self.memory_stream.retrieve_memories(self.agent_id, question, limit=4)
            if memories:
                relevant_memories_text = "\n".join([f"- {m.page_content}" for m in memories])

        sys_prompt = (
            f"Your name is {self.profile.name if self.profile else self.agent_id}, and you work as a {role}. "
            f"Your personality: {personality}. "
            f"You are an agent in an office simulation. A user has just approached you and asked you a question.\n\n"
            f"Here are your most important memories related to this question:\n{relevant_memories_text}\n\n"
            f"Answer the user's question naturally from your own perspective. "
            f"Keep your answers concise (1-3 sentences). If you don't know something based on your memories, admit it according to your personality."
        )
        
        try:
            answer = await self.llm_provider.get_completion(sys_prompt, question, require_json=False)
            
            if self.memory_stream:
                self.memory_stream.add_memory(
                    self.agent_id, 
                    f"Question asked: '{question}'. My answer: '{answer}'", 
                    importance=4.0
                )
                
            return answer
        except Exception as e:
            print(f"⚠️ Error generating QA response for {self.agent_id}: {e}")
            return "Sorry, I got distracted. What were we talking about?"
