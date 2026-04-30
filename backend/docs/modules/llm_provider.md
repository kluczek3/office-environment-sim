# Module: LLM Provider
**Path:** `backend/src/llm/provider.py`

## Role
An abstraction layer wrapping Large Language Model operations. This ensures that the main cognitive logic doesn't care whether the system is using a local Llama model via Ollama or a remote API like Google Gemini. It utilizes LangChain for structural consistency.

## Current State
*   **Status:** Partially Implemented.
*   **Implemented:**
    *   `LLMProvider` class definition.
    *   Default initialization utilizing `ChatOllama` for local, cost-effective inference.
    *   Dynamic integration of alternative providers via `switch_to_cloud` method (supporting OpenAI `gpt-4-turbo` and Google `gemini-pro`).
    *   Standardized asynchronous completion method (`get_completion`) using LangChain's message structure.
    *   LangChain Output Parsers integrations to guarantee structured JSON output explicitly on the model level (`require_json=True` flag).
    *   Extracting prompt templates into a standalone configuration repository (`src/llm/config/prompts.py`) to prevent hard-coding.
*   **Pending Implementation:**
    *   Integration of `LLMProvider` with the remaining services.
