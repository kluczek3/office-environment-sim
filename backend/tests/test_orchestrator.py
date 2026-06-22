import pytest
from src.orchestrator.simulation_state import SimulationOrchestrator

def test_initial_productivity():
    orchestrator = SimulationOrchestrator()
    assert orchestrator.productivity_index == 100.0

def test_process_event_rumor():
    orchestrator = SimulationOrchestrator()
    event_data = {"shock_value": 5.0}
    
    result = orchestrator.process_event("RUMOR_RECEIVED", "agent_1", event_data)
    
    assert result["status"] == "requires_evaluation"
    assert result["load"] == 10.0
    assert orchestrator.productivity_index == 90.0

def test_process_event_ignored():
    orchestrator = SimulationOrchestrator()
    
    result = orchestrator.process_event("WALKING", "agent_1", {})
    
    assert result["status"] == "ignored"
    assert orchestrator.productivity_index == 100.0

def test_productivity_floor():
    orchestrator = SimulationOrchestrator()
    
    orchestrator.update_productivity(150.0)
    assert orchestrator.productivity_index == 0.0  # Should not go below 0
