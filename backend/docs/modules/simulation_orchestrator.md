# Module: Simulation Orchestrator
**Path:** `backend/src/orchestrator/simulation_state.py`

## Role
Maintains the global, macro-level view of the office. Tracks productivity metrics, global events, and dictates when individual agents need to be queried versus when background math handles tasks. 

## Current State
*   **Status:** Partially Implemented.
*   **Implemented:**
    *   Base `SimulationOrchestrator` class tracking the `productivity_index` and active workforce set.
    *   The core event loop parsing logic inside `process_event()`, checking event types.
    *   The basic math defining how aggregated cognitive load drops the global productivity metrics (`update_productivity()` based on rumor `shock_value`).
    *   Hard floor setup to prevent productivity returning integers below 0%.
*   **Pending Implementation:**
    *   Injecting global company strategies into the system simultaneously across vast internal memory streams.
