# Module: API & Websocket Router
**Path:** `backend/src/main.py`, `backend/src/api/websocket_router.py`

## Role
Handles all incoming and outgoing communication with the Unity frontend and potential external dashboards. It manages persistent WebSocket connections required for a real-time simulation.

## Current State
*   **Status:** Partially Implemented.
*   **Implemented:**
    *   FastAPI application creation and CORS setup.
    *   Basic REST endpoints layout (`/api/system/health`, `/api/agents/seed`).
    *   `ConnectionManager` class for managing active WebSocket connections.
    *   Data validation schemas (`AgentAction`, `UnityEvent`) via Pydantic (`src/api/schemas.py`).
    *   WebSocket endpoint (`/ws/simulation`) configured to route events based on `type` (e.g., `spatial_trigger`, `interaction`) and handle invalid formats.
    *   Wired incoming WebSocket payloads directly to the `SimulationOrchestrator` for real-time processing and broadcasting results back to Unity.
    *   Wired routed WebSocket events to instantiate/trigger physical calls to `CognitivePlanner` via LLM Provider (evaluation happens asynchronously during "interaction" events).
    *   Handled graceful disconnects to remove missing agents from active simulation states.
*   **Pending Implementation:**
    *   Further detailed mapping between `SimulationOrchestrator` state and specific Unity `data` parameters.
