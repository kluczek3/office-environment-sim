import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.planner import CognitivePlanner

@pytest.fixture
def mock_llm_provider():
    provider = MagicMock()
    provider.get_completion = AsyncMock()
    return provider

@pytest.mark.asyncio
async def test_generate_daily_plan(mock_llm_provider):
    mock_llm_provider.get_completion.return_value = '{"blocks": ["block1"]}'
    
    planner = CognitivePlanner(agent_id="agent_1", llm_provider=mock_llm_provider)
    plan = await planner.generate_daily_plan()
    
    assert plan == '{"blocks": ["block1"]}'
    mock_llm_provider.get_completion.assert_called_once()
    
@pytest.mark.asyncio
async def test_evaluate_stimulus(mock_llm_provider):
    mock_llm_provider.get_completion.return_value = '{"action": "ignore"}'
    
    planner = CognitivePlanner(agent_id="agent_2", llm_provider=mock_llm_provider)
    result = await planner.evaluate_stimulus(
        stimulus_data={"type": "conversation"}, 
        spatial_modifiers=["Informality_On"]
    )
    
    assert result == '{"action": "ignore"}'
    mock_llm_provider.get_completion.assert_called_once()
