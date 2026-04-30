import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.llm.provider import LLMProvider
from langchain_core.messages import HumanMessage, SystemMessage

@pytest.fixture
def provider():
    with patch('src.llm.provider.ChatOllama'):
        return LLMProvider()

@pytest.mark.asyncio
async def test_get_completion(provider):
    provider.llm.ainvoke = AsyncMock()
    provider.llm.ainvoke.return_value = MagicMock(content="Test response")
    
    response = await provider.get_completion("System prompt", "User prompt")
    
    assert response == "Test response"
    provider.llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_get_completion_json(provider):
    mock_parser = MagicMock()
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value={"test": "json"})
    
    with patch('src.llm.provider.JsonOutputParser', return_value=mock_parser):
        provider.llm.__or__ = MagicMock(return_value=mock_chain)
        
        response = await provider.get_completion("System prompt", "User prompt", require_json=True)
        
        assert response == {"test": "json"}
        mock_chain.ainvoke.assert_called_once()
