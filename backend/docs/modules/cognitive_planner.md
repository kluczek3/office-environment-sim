# Module: Cognitive Planner
**Path:** `backend/src/agent/planner.py`

## Role
Translates the agent's knowledge, current needs, and environmental context into actionable choices. Evaluates environmental stimuli and applies psychological profile filters.

## Current State
*   **Status:** Partially Implemented.
*   **Implemented:**
    *   Class structure instantiated with an `agent_id` and an injected `LLMProvider`.
    *   `generate_daily_plan()`: Triggers prompt blocks asking the LLM context to slice the day into macroblocks yielding JSON.
    *   `evaluate_stimulus()`: Evaluates triggers alongside spatial modifiers via the LLM to output a JSON-formatted engagement intent.
*   **Pending Implementation:**
    *   Developing the full multi-stage logic layer (initial filtering based on traits -> engagement logic output).
    *   Hardening the JSON structured parsing instead of plain prompt instructions to ensure Unity parse safety.
