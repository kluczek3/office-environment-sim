# Office Environment Simulation - Backend

This is the Python-based Generative Agent-Based Modeling (GABM) backend for the Office Environment Simulation. It serves as the "brain" for the autonomous agents navigating the Unity frontend, handling Large Language Model (LLM) reasoning, memory streams via Vector Databases, and cognitive planning.

## Prerequisites

Before running the backend, ensure you have the following installed:

1. **Python 3.9+**: The core language for the backend.
2. **Ollama**: Required to run the local LLM (`ChatOllama`). You can download it from [ollama.com](https://ollama.com/).

## Installation

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Setup Local LLM (Ollama)

By default, the backend is configured to use a local model via Ollama. You need to make sure Ollama is running and the necessary model is pulled.

1. Open a terminal and start Ollama (if not already running as a background service).
2. Pull the default model (e.g., `llama3`):
   ```bash
   ollama pull llama3
   ```
   *(Note: If you change the default model in `src/llm/provider.py`, make sure to pull that specific model).*

## Running the Server

Start the FastAPI application using Uvicorn:

```bash
cd backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

- The API will be available at: `http://localhost:8000`
- The interactive OpenAPI documentation (Swagger UI) is available at: `http://localhost:8000/docs`

## Connecting to the Simulation (Unity)

The main communication bridge between this backend and the Unity frontend is a WebSocket connection.

- **WebSocket Endpoint**: `ws://localhost:8000/ws/simulation`

Unity should connect to this endpoint to push environment triggers (e.g., spatial affordances, agent interactions) and receive high-level cognitive intents for pathfinding and animations.

## Testing

The project uses `pytest` for the testing framework. To run the automated test suite and ensure all modules are functioning correctly:

```bash
cd backend
pytest
```
*Note: Make sure your virtual environment is activated and you have installed testing dependencies via `pip install -r requirements.txt`.*

## Documentation

For an in-depth view of the architecture and module states, refer to the `docs/` directory:
- [Architecture Overview](docs/architecture.md)
- [Module Statuses](docs/modules/)
