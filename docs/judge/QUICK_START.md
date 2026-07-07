# Quick Start (Under 5 Minutes)

This guide gets judges from clone to first coordinator run quickly.

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm 10+
- macOS or Linux shell

## Environment Variables

Create `.env` in repository root:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
TEMPERATURE=0.2
MAX_OUTPUT_TOKENS=1024
SESSION_SECRET_KEY=walletmind-dev-session-secret-change-me
```

Notes:

- `GOOGLE_API_KEY` is also accepted as an alias for `GEMINI_API_KEY`.
- Frontend `VITE_API_BASE_URL` should point to backend host only (no `/api/v1` suffix).

Optional `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 1) Start Backend

```bash
cd WalletMind
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app.main
```

Backend URL: `http://127.0.0.1:8000`
REST docs: `http://127.0.0.1:8000/docs`

## 2) Start Frontend

Open a second terminal:

```bash
cd WalletMind/frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## 3) Start MCP Server

Open a third terminal:

```bash
cd WalletMind
source .venv/bin/activate
python -m backend.app.mcp.server
```

MCP URL: `http://127.0.0.1:8100`
MCP docs: `http://127.0.0.1:8100/docs`

## 4) Execute First Analysis (UI)

1. Open `http://localhost:5173/app/statements/upload`.
2. Upload `sample_data/upload-test.csv`.
3. Open `http://localhost:5173/app/agent-playground`.
4. Select a processed statement.
5. Run default query in multi-agent mode.

Expected UI evidence:

- Coordinator summary appears.
- Timeline shows ordered execution states.
- Per-agent result cards render for completed agents.

## 5) Execute First Analysis (API)

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/agents/execute' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Analyze spending and propose budget actions",
    "user_id": "judge-user",
    "session_id": "judge-session",
    "inputs": {
      "statement_uuid": "<processed-statement-uuid>"
    }
  }'
```

Expected response includes:

- `success: true`
- `data.decision_record.execution_mode` (`single` or `multi`)
- `data.execution_trace`
- `data.individual_agent_results`

## 6) Validate MCP Tool Exposure

```bash
curl -X GET 'http://127.0.0.1:8100/mcp/tools'
```

Expected tools include:

- `analyze_finances`
- `processing_tool`
- `health_tool`
- `insights_tool`
- `budget_tool`
- `report_tool`
- `assistant_tool`

## Troubleshooting

- Backend fails to start: check `.env` values and Python venv activation.
- Frontend cannot reach backend: verify `VITE_API_BASE_URL` and CORS allowlist.
- No processed statement available: upload and process statement first, then retry coordinator.
- MCP tools missing: ensure MCP server started with the same repository and environment.
