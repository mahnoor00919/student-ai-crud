# Student Record Management – AI-Driven Natural-Language CRUD

Transforms a classic student-record UI into an AI-powered application where users can type natural-language commands such as:

- *“Create Ali Khan, roll number 23, age 21, email ali@gmail.com.”*
- *“Show all students.”*
- *“Find student 23.”*
- *“Change student 23’s email to new@gmail.com.”*
- *“Delete student 23.”*

## Architecture

```
User → Frontend (manual CRUD + AI chat)
         ↓
FastAPI  POST /ai/chat
         ↓
LangGraph (state, validation, routing)
         ↓
LLM (structured intent + field extraction)
         ↓
Controlled CRUD Tools  (create/get/update/delete)
         ↓
StudentService → SQLite
         ↓
Response → Frontend (table auto-refreshes)
```

**Core principle:** The LLM understands intent; LangGraph decides & orchestrates; FastAPI/service performs; tools never let the LLM touch the database directly.

## Project layout

```
student-ai-crud/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/student.py    # SQLAlchemy + Pydantic
│   │   ├── services/            # Business CRUD
│   │   ├── routers/             # /students + /ai/chat
│   │   ├── tools/crud_tools.py  # Controlled tools
│   │   └── graph/               # LangGraph workflow
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── README.md
```

## Required `.env` variables

Copy `backend/.env.example` → `backend/.env` and set:

| Variable           | Description                                      |
|--------------------|--------------------------------------------------|
| `OPENAI_API_KEY`   | API key for the LLM provider                     |
| `OPENAI_BASE_URL`  | Base URL (default OpenAI; works with compatible endpoints) |
| `OPENAI_MODEL`     | Model name (e.g. `gpt-4o-mini`)                  |
| `DATABASE_URL`     | SQLAlchemy URL (default `sqlite:///./students.db`) |

**Never put secrets in frontend code.**

## Run the application

```bash
# 1. Backend
cd student-ai-crud/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# edit .env with your OPENAI_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** – the frontend is served by FastAPI.

API docs: **http://localhost:8000/docs**

## Run tests

```bash
cd student-ai-crud/backend
source .venv/bin/activate
pytest tests/ -v
```

Tests cover:
- REST CRUD (create, list, get, update, delete, validation, 404, duplicate roll)
- Controlled tools (create, read, update, delete with confirmation, not-found, ambiguous name)

## Natural-language flow

1. User types a command in the AI chat box.
2. `POST /ai/chat` receives `{ message, thread_id }`.
3. LangGraph node **extract_intent** calls the LLM with a strict JSON schema → `IntentResult` (CREATE / READ / READ_ALL / UPDATE / DELETE / CONFIRM_DELETE / … + extracted fields).
4. **merge_pending** merges follow-up answers into an incomplete CREATE (or pending DELETE).
5. Router decides:
   - Missing required fields → ask clarification (state kept per `thread_id`).
   - Complete CREATE → `create_student` tool.
   - READ / READ_ALL / UPDATE → corresponding tool.
   - DELETE → resolve target; if unique, ask for confirmation (never delete immediately).
   - CONFIRM_DELETE → execute delete with `confirm=True`.
6. Tools call `StudentService` (Pydantic + DB constraints). LLM never sees SQL.
7. Final natural-language response is returned; frontend refreshes the table on success.

### Multi-turn example

```
User: Create Ali Khan.
AI:   I need the following information: roll_number, age, email. I already have: name=Ali Khan.
User: Roll 23, age 21, email ali@gmail.com.
AI:   Student 'Ali Khan' (roll 23) created successfully.
```

### Safety

- Missing fields → no DB write; ask for them.
- Ambiguous name match → list matches; require roll number.
- DELETE always requires explicit confirmation.
- Pydantic + unique roll constraint + service-layer checks.

## Manual CRUD

The original form/table UI is preserved and talks to the same REST endpoints (`POST/GET/PUT/DELETE /students`). Both UIs stay in sync.
