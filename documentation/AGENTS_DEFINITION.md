# Specification and Definition of Simulation Agents

## 1. Definition and Role of Agents
In the context of our office environment simulation, **agents are generative, autonomous digital entities** (Generative Agents) that represent virtual employees. Their main goal is not to achieve a pre-defined endpoint (as in classic video games), but to credibly reflect human behavior (human-like social dynamics). Agents serve as the vectors through which we study the propagation of information (e.g., rumors) and the formation of social structures in the workplace.

## 2. Psychological Profile and Internal State
Each agent is unique. This diversity (heterogeneity) determines how an individual interprets the environment and reacts to stimuli.

*   **Personality Traits:** Agents possess stable character attributes (e.g., introvert, extrovert, lazy, ambitious, "office gossip"). These attributes act as filters (base prompts) for the Large Language Model (LLM), shaping their demeanor and priorities.
*   **Emotions and Needs:** The agent's state is dynamic and relies on a cognitive model (often inspired by Maslow's Hierarchy of Needs). Stress levels, fatigue, or the need for socialization directly impact their behavior.
*   **Relationship Network:** Agents maintain a relationship graph with other employees (ranging from hostility to close friendship). These relationships evolve based on the history of shared interactions and determine the level of trust (crucial when sharing sensitive rumors). Stored in a JSON file (`backend/config/profiles.json`) parsed via Pydantic model at runtime for easy modification.

## 3. Available Actions and Environmental Interactions
Agents navigate the Unity office space, making decisions based on their current state and goals. The pool of available actions includes:

*   Working (at their own desk)
*   Printing documents
*   Conversing with a co-worker
*   Resting (sitting on a chair/couch in the relaxation zone)
*   Going to the bathroom
*   Going to the kitchen / for coffee
*   Presenting (in front of a group)
*   Attending a conference / team meeting

**Spatial Affordances (Environmental Impact):** 
The office space actively influences agents' behavior through invisible modifiers assigned to specific Unity zones. For example, entering the "Kitchen" zone adds an `Informality_On` modifier to the LLM prompt, encouraging casual speech and the sharing of secrets. Conversely, the "Conference Room" imposes a frame of professionalism, artificially restricting or completely blocking the spread of informal rumors while inside.

## 4. Cognitive Architecture
The agent's "brain" is based on the centralized use of an LLM, integrated with advanced memory management and planning modules:

1.  **Memory Stream:** A comprehensive database recording all agent experiences in natural language. The architecture is hierarchical—divided into working memory (short-term, e.g., *recentmem*) for the current context, and long-term memory (*longmem*).
2.  **Reflection Module:** A mechanism that periodically synthesizes accumulated memories into higher-order, abstract conclusions (so-called *reflection trees*). It also utilizes the *Summarize-and-Forget* mechanism—before moving to long-term memory, memories are grouped semantically, summarized, and repetitive events are forgotten, optimizing the vector database. Implemented by grouping recent docs on `day_ended` trigger.
3.  **Self-monitoring:** An asynchronous process maintaining a narrative summary of recent events relevant to the agent's main goal. This prevents "losing the thread" while executing time-distributed tasks. It is implemented inherently within the `planner.py` through sequential synthesis of recent actions.
4.  **Planning and Action Module:** A component that translates the agent's knowledge, needs, and LLM guidelines into specific, sequential animation calls and pathfinding in the Unity engine.

## 5. Decision-Making Mechanics and Productivity
Agents do not react based on simple conditional instructions (if-else) but utilize analytical cognitive processes:

*   **Memory Retrieval & LLM Injection:** In response to a stimulus, the system does not send the entire history to the LLM. It uses a scoring function that sums three weights: **Recency** (exponential time decay), **Importance** (distinguishes eating breakfast from a major argument), and **Relevance** (calculated as exponential of negative euclidean distance of embeddings). Only key memories are sorted, retrieved, and automatically injected into the system prompt of the Large Language Model whenever `evaluate_stimulus` is called, ensuring consistent behavior without amnesia.
*   **Top-down Planning:** Agents plan their day top-down. A daily outline is generated in large blocks (from 9 AM to 5 PM).
*   **Recursive macro-to-micro breakdown:** Each 4-hour macro block string is sent through an LLM to generate sequences of microscopic subtasks containing restricted, parsed actions for the Unity engine (`move_to`,`sit_down`,`interact`).
*   **Option-Action Selection:** To optimize API querying costs, a cognitive controller first selects a high-level "option" (e.g., main goal: "have a conversation with John"). Until the end condition is met, lower-level actions (e.g., pathfinding to John, playing gesture animations) are managed by faster Unity scripts without continuously pinging the LLM.
*   **Multi-stage Evaluation Rules:** In high social risk situations (e.g., deciding whether to share a post on a virtual forum), the decision goes through stages: initial filtering (rejecting completely mismatched options), comprehensive evaluation (assessing engagement potential), and a final logical decision.
*   **Productivity Index Tied to Cognitive Load:** Cognitive distraction directly impacts work efficiency. When an agent's *recentmem* is cluttered with strong, new rumors, the iterative planning system prioritizes "Conversation" actions over "Work" actions. This translates to a physical, visible drop in the overall office productivity bar, driven purely by the agents' cognitive distraction rather than hard-coded timers.

## 6. Communication and Emergent Behaviors
*   **Information Tagging ("Gossip Virality"):** Rumors and official strategies are treated as data packages with hidden metadata (e.g., `ShockValue: 0-10` and `Confidentiality: 0-10`). An introverted agent might block the propagation of a highly confidential rumor, whereas an "office gossip" agent's evaluation algorithm will push a high-shock-value rumor to the very top of their daily priorities.
*   **Emergent Dynamics:** Communication occurs fully in natural language. Thanks to the combination of free will, memory streams, and spatial affordances, the system exhibits **emergent behaviors**. These include the unscripted, spontaneous formation of cliques, the natural isolation of individuals with extreme views, and the distortion of information (the "telephone game" effect) as it propagates from desk to desk.