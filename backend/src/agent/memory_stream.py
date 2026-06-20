from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from datetime import datetime
import uuid
import math

class MemoryStream:
    def __init__(self):
        # FAISS requires explicit embeddings. We use a lightweight local model from sentence-transformers.
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        # Initialize an empty FAISS vectorstore using a dummy text to initialize the dimension
        self.vectorstore = FAISS.from_texts(["init"], embedding=self.embeddings)
        self.vectorstore.delete([list(self.vectorstore.docstore._dict.keys())[0]]) # Clear the dummy text

    def add_memory(self, agent_id: str, text: str, importance: float):
        """Adds a memory to the vector store with associated metadata."""
        timestamp = datetime.now().timestamp()
        
        doc = Document(
            page_content=text,
            metadata={
                "agent_id": agent_id,
                "importance": importance,
                "timestamp": timestamp
            }
        )
        self.vectorstore.add_documents([doc])

    def retrieve_memories(self, agent_id: str, query: str, limit: int = 5):
        """Retrieves memories, potentially based on scoring weights (Recency, Importance, Relevance)."""
        # Retrieve top k based on textual similarity (Relevance)
        try:
            results_with_scores = self.vectorstore.similarity_search_with_score(
                query,
                k=20,
                filter={"agent_id": agent_id}
            )
        except Exception as e:
            results_with_scores = []
            
        current_time = datetime.now().timestamp()
        
        scored_memories = []
        for doc, distance in results_with_scores:
            # Distance (L2) -> inverse relevance
            relevance = math.exp(-distance)
            
            importance = doc.metadata.get("importance", 5.0) / 10.0
            timestamp = doc.metadata.get("timestamp", current_time)
            
            hours_passed = max(0.0, (current_time - timestamp) / 3600.0)
            recency = math.exp(-0.1 * hours_passed) # Decay function

            w1, w2, w3 = 1.0, 1.0, 1.0
            final_score = (relevance * w1) + (importance * w2) + (recency * w3)
            
            scored_memories.append((final_score, doc))
        
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_memories[:limit]]

    async def summarize_and_forget(self, agent_id: str, llm_provider):
        """Routine to group semantic memories, summarize, and clean old data."""
        # Retrieve agent's memories directly from the docstore
        agent_docs = {uid: doc for uid, doc in self.vectorstore.docstore._dict.items() if doc.metadata.get("agent_id") == agent_id}
        
        if len(agent_docs) > 10:
            # Sort by time to keep only recent ones or group
            sorted_docs = sorted(agent_docs.items(), key=lambda x: x[1].metadata.get("timestamp", 0))
            
            # Take earliest documents to summarize
            to_summarize = sorted_docs[:10]
            texts = [doc.page_content for uid, doc in to_summarize]
            
            summary_prompt = "Summarize the following memories into 2-3 high-level insights or reflection trees."
            user_text = "\n".join(texts)
            
            summary = await llm_provider.get_completion(summary_prompt, user_text)
            
            # Add reflection node to memory
            self.add_memory(agent_id=agent_id, text=f"Reflection: {summary}", importance=8.0)
            
            # Delete old memories from vector store
            ids_to_delete = [uid for uid, doc in to_summarize]
            self.vectorstore.delete(ids_to_delete)
