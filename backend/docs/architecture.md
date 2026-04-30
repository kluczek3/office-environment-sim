# Backend Architecture Overview

The backend of the Generative Agent-Based Modeling (GABM) office simulation is implemented in Python and acts as the "brain" for the autonomous agents navigating the Unity frontend.

## High-Level Design

The architecture is built on a **hybrid approach**, offloading physical pathfinding and animations to Unity, while delegating high-level cognitive processes (decision-making, memory retrieval, reflection) to Large Language Models (LLMs) via Python.

### Communication (Frontend <-> Backend)
*   **Protocol:** Real-time WebSockets (FastAPI).
*   **Data Flow:** 
    *   **Unity -> Python**: Environmental triggers, spatial affordances, interaction events (e.g., "Agent entered Kitchen").
    *   **Python -> Unity**: High-level intents and macro-options (e.g., "Agent starting conversation with Agent B").

### Core Technologies
1.  **FastAPI:** High-performance async web framework handling REST and WebSockets.
2.  **LangChain:** Orchestration framework for LLMs. Facilitates prompt templating, dynamic modifications (spatial affordance injections), and structured output parsing.
3.  **ChatOllama:** Primary local LLM runner for deep reasoning without cloud API costs (highly modular and switchable to cloud APIs like Gemini/ChatGPT via LangChain abstractions).
4.  **FAISS (Facebook AI Similarity Search):** Local Vector Database engine used for the agent `MemoryStream`, efficiently storing and retrieving semantic experiences via embeddings generated locally.

### Data Flow Lifecycle (Stimulus Processing)
1.  **Stimulus Input:** Unity sends an event via WebSocket.
2.  **Orchestrator:** The `SimulationOrchestrator` captures the event, determining if it requires cognitive processing (saving LLM queries).
3.  **Memory Retrieval:** If cognitive processing is needed, the `MemoryStream` queries the FAISS index. Retrieval scores are determined by *Recency*, *Importance*, and *Relevance*.
4.  **LLM Evaluation:** The `CognitivePlanner` passes the context and spatial modifiers to the `LLMProvider`.
5.  **Action Dispatch:** The LLM's structured JSON decision is dispatched back to Unity via WebSocket.
6.  **Reflection (Async):** Periodically, the system triggers the *Summarize-and-Forget* process to optimize vector storage and update long-term strategies.
