# Dokumentacja API: Komunikacja Backend <-> Frontend (Unity)

Głównym kanałem komunikacji pomiędzy silnikiem symulacji (np. Unity) a backendem kognitywnym jest dwukierunkowe połączenie **WebSocket**.

## 1. Połączenie

*   **Endpoint:** `ws://<host>:<port>/ws/simulation`
*   **Protokół:** WebSocket (komunikacja tekstowa, ładunki w formacie JSON)

## 2. Wiadomości od Frontendu (Z silnika do Backendu)

Frontend wysyła zdarzenia w standardowym formacie JSON, bazując na schemacie `UnityEvent`. Każda wiadomość musi zawierać przynajmniej `type` oraz `agent_id`.

**Format ogólny:**
```json
{
  "type": "string (typ_eventu)",
  "agent_id": "string (id_agenta)",
  "timestamp": 1612132312.0,
  "data": {
     // dodatkowe informacje, zmienne środowiskowe, parametry interakcji
  }
}
```

### Obsługiwane typy zdarzeń (Event Types):

#### A. Wpływ przestrzenny (`spatial_trigger`)
Wysyłane, gdy agent wejdzie do strefy o szczególnych zasadach (np. kuchnia, sala konferencyjna).
*   **Payload `data`**: Powinien zawierać tablicę `modifiers` (np. `["Informality_On"]`).

#### B. Interakcja z otoczeniem lub innym agentem (`interaction`)
Wysyłane, gdy zachodzi zdarzenie bodźcowe wymagające oceny pod kątem włączenia się do interakcji lub kontynuowania pracy.
*   **Payload `data`**: Opis bodźca, kto zapoczątkował, ewentualnie przekazywana wiadomość / plotka. Może również zawierać aktualne `modifiers` fizycznego miejsca.

#### C. Koniec skali czasu (`day_ended`)
Sygnał czasowy, który informuje backend, że dany agent kończy "cykl" i powinien podsumować wspomnienia (Summarize and Forget).
*   **Payload `data`**: Opcjonalne statystyki na koniec dnia.

---

## 3. Wiadomości od Backendu (Od Backendu do silnika)

Backend wysyła asynchroniczne odpowiedzi broadcastem w formacie JSON. Wyniki decyzyjne zależą między innymi od stanu agenta i indeksu obciążenia kognitywnego biura.

**Format ogólny (przykład po przetworzeniu `interaction`):**
```json
{
  "status": "processed",
  "action": "evaluate_stimulus",
  "agent_id": "agent_1",
  "decision": {
      // odpowiedź JSON wygenerowana przez model (np. czy agent ignoruje czy wchodzi w interakcję, z jaką kwestią dialogową)
  },
  "load": 5.0 // (Opcjonalnie) aktualny poziom obciążenia (cognitive load) po przetworzeniu eventu
}
```

### Typy reakcji backendu (Pola `action`):

*   **`update_modifiers`** - Potwierdzenie przyjęcia zmiennych środowiskowych. Brak generowania odpowiedzi z LLM w tej klatce.
*   **`reflection_triggered`** - Potwierdzenie przyjęcia requestu na koniec dnia, po zebraniu wniosków pamięci.
*   **`evaluate_stimulus`** - Zawiera obiekt `decision` (decyzja wygenerowana w ramach profilu agenta). Backend nakazuje silnikowi rozpoczęcie konkretnego zachowania.