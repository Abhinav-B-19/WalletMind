# Quick Start (Under 5 Minutes)

This guide gets judges from clone to first multi-agent run quickly.

## Prerequisites

- Python 3.12+ (project virtual environment recommended)
- Node.js 20+
- npm 10+
- macOS/Linux terminal

## Environment Variables

Backend `.env` (at repository root):

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
TEMPERATURE=0.2
MAX_OUTPUT_TOKENS=2048
```

Frontend optional `.env` in `frontend/`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Backend Setup + Run

```bash
cd WalletMind
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app.main
```

Backend default URL: `http://127.0.0.1:8000`

## Frontend Setup + Run

Open a second terminal:

```bash
cd WalletMind/frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`

## Run MCP Server (Independent)

Open a third terminal:

```bash
cd WalletMind
source .venv/bin/activate
python -m backend.app.mcp.server
```

MCP default URL: `http://127.0.0.1:8100`

## Open Swagger + Playground

- REST Swagger: `http://127.0.0.1:8000/docs`
- MCP Swagger: `http://127.0.0.1:8100/docs`
- Agent Playground: `http://localhost:5173/app/agent-playground`
- Dashboard: `http://localhost:5173/app/dashboard`

## Execute First Analysis

### Option A: UI (Recommended)

1. Upload a sample statement from upload page.
2. Open Agent Playground.
3. Keep demo defaults (query + first processed statement + multi-agent).
4. Click Execute.

### Option B: API

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/agents/execute' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Analyze my spending and suggest improvements",
    "user_id": "judge-user",
    "session_id": "judge-session",
    "inputs": {
      "statement_uuid": "<processed-statement-uuid>"
    }
  }'
```

## Expected Result

- Coordinator response returns `execution_mode` as `single` or `multi`.
- Agent Playground renders:
  - Coordinator summary
  - Execution timeline
  - Per-agent result cards (health/insights/budget/report/assistant)
- Dashboard pages show consistent data for the selected statement.
- MCP `/mcp/tools` returns WalletMind tools (including `analyze_finances`).
