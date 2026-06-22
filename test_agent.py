import asyncio
import websockets
import json

URI = "ws://localhost:8000/ws/simulation"

async def test_qa():
    async with websockets.connect(URI) as websocket:
        print("✅ Połączono z serwerem symulacji (WebSocket)!")

        # --- 1. INICJALIZACJA AGENTA ---
        # Musimy najpierw wysłać zdarzenie daystarted, aby serwer wygenerował "mózg" (CognitivePlanner) dla agenta_0
        print("\n⏳ Inicjalizacja mózgu agenta_0...")
        day_started_msg = {
            "type": "daystarted",
            "agent_id": "system",
            "timestamp": 123456789.0,
            "data": {
                "agents": [
                    {"agentId": "agent_0", "role": "Boss", "assignedChairId": "boss_chair_0"}
                ],
                "zones": ["conference_0", "chill_0"]
            }
        }
        await websocket.send(json.dumps(day_started_msg))
        await asyncio.sleep(2) # Dajemy serwerowi 2 sekundy na podpięcie LLMa

        # --- 2. ZAPYTANIE DO LLM (QA ENGINE) ---
        pytanie = "Hi! How are you doing today?"
        print(f"\n💬 Zadaję pytanie: '{pytanie}'")
        
        qa_msg = {
            "type": "ask_question",
            "agent_id": "system",
            "timestamp": 123456793.0,
            "data": {
                "targetAgentId": "agent_0",
                "question": pytanie
            }
        }
        await websocket.send(json.dumps(qa_msg))
        
        # --- 3. ODBIÓR ODPOWIEDZI ---
        print("⏳ Czekam na wygenerowanie odpowiedzi przez LLM (to może chwilę potrwać)...")
        response = await websocket.recv()
        
        # Formatowanie JSONa do czytelnej postaci
        parsed_response = json.loads(response)
        print(f"\n🤖 Odpowiedź serwera:\n{json.dumps(parsed_response, indent=2, ensure_ascii=False)}")
        print(f"\n🗣️ Czysty tekst agenta: {parsed_response.get('answer')}")

if __name__ == "__main__":
    asyncio.run(test_qa())