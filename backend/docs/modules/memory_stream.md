# Module: Memory Stream
**Path:** `backend/src/agent/memory_stream.py`

## Role
Acts as the central cognitive database for an agent. It stores natural language experiences and allows the retrieval of highly relevant context. It divides knowledge functionally and implements mechanisms to prevent DB bloating (forgetting).

## Current State
*   **Status:** Partially Implemented.
*   **Implemented:**
    *   FAISS (via LangChain's Community wrapper) client deployment using CPU-compiled architecture to ensure cross-platform compatibility removing hard C++ compiler requirements on Windows.
    *   Embeddings instantiated utilizing lightweight, fast, local computational embeddings (`HuggingFaceEmbeddings` -> `all-MiniLM-L6-v2`).
    *   Basic document addition function `add_memory` embedding timestamp and importance metadata into `langchain_core.documents.Document`.
    *   Basic document textual similarity retrieval function `retrieve_memories`.
    *   Setup for the `summarize_and_forget` mechanism that triggers upon crossing memory thresholds.
*   **Pending Implementation:**
    *   Applying mathematical manual ranking over the array vectors to combine similarity scores with `Recency` and `Importance` metadata attributes natively.
    *   Fleshing out the LLM prompt inside `summarize_and_forget` to produce a compressed reflection narrative and executing the FAISS deletions natively.
