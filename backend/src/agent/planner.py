import json
import re
from typing import List, Dict, Any, Optional
from src.api.schemas import AgentProfile, NetworkCommand


class CognitivePlanner:
    def __init__(self, agent_id: str, llm_provider, profile: Optional[AgentProfile] = None, memory_stream=None):
        self.agent_id = agent_id
        self.llm_provider = llm_provider
        self.profile = profile
        self.memory_stream = memory_stream
        self.macro_plan: List[Dict[str, str]] = []
        self.current_narrative_goal: str = "Awaiting day start."

    async def generate_daily_plan(self) -> List[Dict[str, str]]:
        role = getattr(self.profile, 'role', "Employee") if self.profile else "Employee"
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"

        sys_prompt = (
            f"You are {getattr(self.profile, 'name', self.agent_id)}, working as a {role}. "
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

    async def determine_next_actions(self, current_location: str, available_targets: List[str],
                                     current_time: str = "09:00", global_event: dict = None) -> List[NetworkCommand]:
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        needs = self.profile.needs.model_dump() if self.profile else {}
        role = getattr(self.profile, 'role', "Worker") if self.profile else "Worker"
        assigned_chair = getattr(self.profile, 'assignedChairId',
                                 f"office_chair_{self.agent_id.split('_')[-1]}") if self.profile else f"office_chair_{self.agent_id.split('_')[-1]}"

        override_instruction = ""
        if global_event:
            target_room = global_event["room"]
            desc = global_event["description"]
            override_instruction = (
                f"\n\n--- CRITICAL SCHEDULE OVERRIDE ---\n"
                f"Current time is {current_time}. You have a CRITICAL business event: '{desc}' in location '{target_room}'.\n"
                f"This is your top priority. Your action MUST be 'Interact' with '{target_room}'.\n"
                f"You are not allowed to do anything else. Duration MUST be between 10 and 20 minutes."
            )

        if "chill" in current_location.lower():
            thought_format_instruction = (
                "CRITICAL THOUGHT FORMAT: Since you are in a chill zone, formulate your 'thought' as a direct spoken statement directed out loud to the people around you. "
                "Use type 'Idle' to stay and socialize. Do not 'Interact' with the chill room again to avoid standing behind walls."
            )
        else:
            thought_format_instruction = (
                "CRITICAL THOUGHT FORMAT: Write your 'thought' parameter in a natural, organic role-play style as an internal monologue. "
                "Never mention technical variables."
            )

        sys_prompt = (
            f"You are {self.agent_id}, a {personality} person working as {role}.\n"
            f"Time: {current_time}.\n"
            f"Goal: '{self.current_narrative_goal}'.\n"
            f"Needs levels (1.0 is full, 0.0 empty): {needs}.\n\n"
            f"Location: '{current_location}'.\n"
            f"Base physical targets: {available_targets}.\n"
            f"Allowed Implicit Targets (You CAN interact with these even if not in base targets):\n"
            f"- Your assigned desk: '{assigned_chair}'. Boses use 'boss_chair', workers use 'office_chair_X'.\n"
            f"- Large conference seating: 'conference_chair_X' (X from 0 to 20)\n"
            f"- Small conference seating: 'conference_small_X' (X from 0 to 10)\n"
            f"Toilets: 'toilet_0', 'toilet_1'. If your bladder or physiological need is critically low, you MUST target a toilet immediately.\n"
            f"Allowed 'type' values: ['Interact', 'Idle'].\n"
            f"- 'Duration' MUST BE STRICTLY AN INTEGER BETWEEN 10 AND 20 MINUTES.\n"
            f"{thought_format_instruction}"
            f"{override_instruction}"
        )

        user_prompt = (
            "Generate the next 1 to 2 actions. "
            "Output strictly as a JSON array of objects: "
            "[{'type': 'Interact|Idle', 'target_id': 'string', 'duration': float, 'thought': 'string'}]"
        )

        raw_res = await self.llm_provider.get_completion(sys_prompt, user_prompt, require_json=True)

        commands = []
        try:
            data_list = raw_res.get("commands", raw_res) if isinstance(raw_res, dict) else raw_res

            for item in data_list:
                command = NetworkCommand(**item)

                if command.type not in ["Interact", "Idle"]:
                    command.type = "Idle"
                    command.target_id = ""

                command.duration = max(10.0, min(20.0, float(command.duration)))

                is_valid_implicit = bool(
                    re.match(r"^(office_chair_\d+|conference_chair_\d+|conference_small_\d+|boss_chair)$",
                             command.target_id))

                if command.type == "Interact" and command.target_id not in available_targets and not is_valid_implicit:
                    command.type = "Idle"
                    command.target_id = ""

                commands.append(command)

            if commands:
                self.current_narrative_goal = f"Executing: {commands[-1].thought}"

        except Exception as e:
            print(f"⚠️ Failed to parse LLM actions for {self.agent_id}: {e}")
            commands.append(NetworkCommand(type="Idle", target_id="", duration=10.0,
                                           thought="I am focusing on my professional tasks."))

        return commands

    async def evaluate_stimulus(self, stimulus_data: dict, spatial_modifiers: list) -> str:
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        stress = getattr(self.profile, 'current_stress_level', 0.0) if self.profile else 0.0

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

        if isinstance(res, dict) and 'new_narrative_goal' in res:
            self.current_narrative_goal = res['new_narrative_goal']

        importance_score = 5.0
        try:
            score_sys_prompt = "You are a cognitive evaluation module for an office simulation agent. Your task is to assess how impactful a given event is on the agent's mental state and productivity."
            score_user_prompt = (
                f"On a scale from 1 to 10, how important and memorable is the following event for a person with the profile: {personality}?\n"
                f"Event: {stimulus_data}\n"
                f"Return ONLY the number, without any additional text."
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

        return res

    async def answer_question(self, question: str) -> str:
        personality = ", ".join(self.profile.personality_traits) if self.profile else "neutral"
        role = getattr(self.profile, 'role', "Employee") if self.profile else "Employee"

        relevant_memories_text = "No records or relevant memories found."
        if self.memory_stream:
            memories = self.memory_stream.retrieve_memories(self.agent_id, question, limit=4)
            if memories:
                relevant_memories_text = "\n".join([f"- {m.page_content}" for m in memories])

        sys_prompt = (
            f"Your name is {getattr(self.profile, 'name', self.agent_id)}, and you work as a {role}. "
            f"Your personality: {personality}.\n\n"
            f"CRITICAL CONSTRAINT: You must answer the question based ONLY and EXCLUSIVELY on the real provided memories listed below. "
            f"Do not invent facts, do not use outside knowledge. If the memories section is empty, "
            f"you MUST explicitly state that you do not know or have no record of it.\n\n"
            f"Here are your exclusive memories related to this question:\n{relevant_memories_text}\n\n"
            f"Respond naturally from your own first-person perspective in 1-3 sentences maximum."
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
            return "I am currently focused on my office workflow and don't have details on that matter."