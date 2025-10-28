# Human-in-the-Loop AI Supervisor (Frontdesk Test)

A local system that simulates an AI receptionist which escalates unknown questions to a human supervisor, follows up with the customer, and learns new answers.

## Stack
- LiveKit Agents (voice agent)
- FastAPI (supervisor/admin UI)
- SQLAlchemy + SQLite (persistence)

## Quick Start
1) Create `.env.local` in repo root:
```
GOOGLE_API_KEY=your_google_api_key
ELEVEN_API_KEY=your_elevenlabs_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
# ASSEMBLYAI_API_KEY=your_assemblyai_api_key
# CARTESIA_API_KEY=your_cartesia_api_key
# DATABASE_URL=sqlite:///./local.db
```

2) Install deps (uv or venv+pip)
- With uv:
```
uv run python -V  # ensures env
```
- Or venv+pip:
```
python -m venv .venv
. .venv/Scripts/Activate.ps1  # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -U pip
pip install fastapi uvicorn SQLAlchemy livekit-agents[silero,turn-detector] \
    livekit-plugins-noise-cancellation python-dotenv tzdata jinja2
```

3) Initialize the database:
```
python -m db.init_db
```

4) Run supervisor UI:
```
uvicorn web.app:app --reload
```
- Home: http://127.0.0.1:8000/
- Pending: http://127.0.0.1:8000/requests
- History: http://127.0.0.1:8000/history
- Learned: http://127.0.0.1:8000/knowledge

5) Run the voice agent (console):
```
uv run agent.py console
```
(Or `python agent.py console`)

The agent answers known questions from `prompt.py`. If unknown, it creates a Pending Help Request and logs a supervisor alert.

## What Happens When Supervisor Resolves
- Submit an answer in the UI (request detail → Resolve)
- System immediately logs a simulated text/callback to the caller
- Saves a new KnowledgeEntry (appears in “Learned Answers”)
- Sets request to `resolved`

If unanswered past timeout, a background task marks it `unresolved`.

## Data Model
- customers: id, external_id, display_name, phone_number, timestamps
- call_sessions: id, room_name (unique), customer_id, timestamps
- help_requests: id, call_session_id, customer_id, question, status, timeout_at, resolved_answer, timestamps
- supervisor_responses: id, help_request_id, answer, supervisor_id, timestamps
- knowledge_entries: id, question_canonical, answer, source_help_request_id, timestamps

## Configuration Notes
- STT providers supported by this setup: deepgram, assemblyai, cartesia
- Default in `agent.py`: `stt = "deepgram/nova-3:en"`
- Ensure corresponding API key is present in `.env.local`
- LLM: Google Gemini (`GOOGLE_API_KEY`)
- TTS: ElevenLabs (`ELEVEN_API_KEY`)

## Troubleshooting
- STT provider error: verify API key; try switching `stt` to `assemblyai` if Deepgram has regional timeouts
- CancelledError on shutdown of UI: handled gracefully (background sweeper stops on shutdown)
- DB issues: rerun `python -m db.init_db`

## Demo Script
1. Start UI: `uvicorn web.app:app --reload`
2. Start agent: `uv run agent.py console`
3. Ask something unknown → Pending request appears
4. Resolve in UI → see Learned entry and follow-up log
5. Ask again → agent should answer directly

## License
For evaluation/demo purposes.
