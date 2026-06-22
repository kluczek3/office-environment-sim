import pytest
from unittest.mock import MagicMock, patch
from src.agent.memory_stream import MemoryStream

@pytest.fixture
def mock_faiss():
    with patch('src.agent.memory_stream.FAISS') as mock_faiss_class:
        mock_instance = mock_faiss_class.from_texts.return_value
        yield mock_instance

@patch('src.agent.memory_stream.HuggingFaceEmbeddings')
def test_add_memory(mock_embeddings, mock_faiss):
    stream = MemoryStream()
    stream.add_memory(agent_id="agent_1", text="Saw a pigeon", importance=3.5)
    
    mock_faiss.add_documents.assert_called_once()
    doc_arg = mock_faiss.add_documents.call_args[0][0][0]
    assert doc_arg.page_content == "Saw a pigeon"
    assert doc_arg.metadata["agent_id"] == "agent_1"
    assert doc_arg.metadata["importance"] == 3.5

@patch('src.agent.memory_stream.HuggingFaceEmbeddings')
def test_retrieve_memories(mock_embeddings, mock_faiss):
    mock_faiss.similarity_search.return_value = ["mock_document"]
    
    stream = MemoryStream()
    results = stream.retrieve_memories(agent_id="agent_1", query="birds", limit=2)
    
    mock_faiss.similarity_search.assert_called_once_with(
        "birds",
        k=2,
        filter={"agent_id": "agent_1"}
    )
    assert results == ["mock_document"]
