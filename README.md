# WalletMind

WalletMind is an AI-first financial intelligence platform that turns raw bank statements into explainable financial outcomes in minutes.

It combines deterministic financial computation with multi-agent orchestration, Google ADK function tooling, and MCP interoperability.

## Architecture Image

Architecture diagram placeholder:

- `assets/diagrams/walletmind-architecture-placeholder.png`

## Feature Screenshots

Screenshot placeholders:

- Landing Page: `assets/screenshots/landing-page-placeholder.png`
- Dashboard: `assets/screenshots/ai-dashboard-placeholder.png`
- Financial Health: `assets/screenshots/financial-health-placeholder.png`
- AI Assistant: `assets/screenshots/assistant-placeholder.png`
- Monthly Report: `assets/screenshots/monthly-report-placeholder.png`

Required judge screenshot checklist is documented at `docs/screenshots/README.md`.

## Demo GIF Placeholders

- Upload to Dashboard flow: `assets/screenshots/demo-upload-to-dashboard-placeholder.gif`
- Agent Playground orchestration: `assets/screenshots/demo-agent-playground-placeholder.gif`
- MCP tool execution: `assets/screenshots/demo-mcp-placeholder.gif`

## Project Overview

WalletMind workflow:

1. Upload and process statement files.
2. Normalize transactions into a consistent schema.
3. Run health score, insights, budget, and report engines.
4. Route analysis through coordinator-led single or multi-agent execution.
5. Present transparent outputs in dashboard cards and execution timelines.

## Quick Start

### 1. Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app.main
```

Backend: `http://127.0.0.1:8000`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### 3. MCP Server

```bash
cd ..
source .venv/bin/activate
python -m backend.app.mcp.server
```

MCP: `http://127.0.0.1:8100`

For the full judge flow, use `docs/judge/QUICK_START.md`.

## Project Structure

```text
backend/                  FastAPI APIs, agents, ADK runtime, MCP server, tools
frontend/                 React UI, dashboard, assistant, agent playground
walletmind/               Shared domain logic and services
tests/                    Backend validation suites
docs/                     Architecture, implementation, deployment, judge pack
assets/                   Branding, diagrams, screenshots, notebook assets
sample_data/              Demo statement files for quick evaluation
storage/                  Runtime db/uploads/cache/session artifacts
```

## Technology Stack

- Frontend: React, TypeScript, Vite, React Query, Tailwind.
- Backend: FastAPI, Pydantic, SQLAlchemy.
- AI Runtime: Google Gemini + Google ADK.
- Agent Tooling: ADK FunctionTool-based wrappers.
- Protocol Layer: Standalone MCP infrastructure server.
- Testing: Pytest, Vitest, Testing Library.

## AI Architecture

WalletMind AI architecture centers on coordinator-orchestrated execution:

- `CoordinatorAgent` as orchestration control plane.
- Specialized agents for health, insights, budget, report, assistant, and processing.
- ADK Function Tools as deterministic boundaries to domain services.
- MCP adapter and registry exposing capabilities through `/mcp/*` APIs.
- Shared service layer for business logic reuse across REST and MCP.

Detailed judge-friendly architecture and diagrams: `docs/judge/ARCHITECTURE.md`.

## Judge Docs

- Hub: `docs/judge/README.md`
- Quick Start: `docs/judge/QUICK_START.md`
- Demo Walkthrough: `docs/judge/DEMO_GUIDE.md`
- Architecture + Diagrams: `docs/judge/ARCHITECTURE.md`
- Rubric Mapping: `docs/judge/RUBRIC_MAPPING.md`
- API Examples: `docs/judge/API_EXAMPLES.md`
- Judge Checklist: `docs/judge/JUDGE_CHECKLIST.md`
- Evaluation Summary: `docs/judge/EVALUATION_SUMMARY.md`

## Deployment

Production split deployment:

- Backend API on Render
- Frontend SPA on Vercel
- PostgreSQL on Neon

Repository includes deployment references in `render.yaml`, `frontend/vercel.json`, and `docs/deployment/deployment.md`.

## Future Work

- Export-ready PDF monthly reports.
- Multi-statement trend and seasonality analysis.
- Goal simulation and what-if planning.
- Collaboration features for households and advisors.

## License

This project is licensed under `LICENSE`.
- Frontend can load but API requests fail:
  - Verify `VITE_API_BASE_URL` targets Render backend URL.

### Live Demo Placeholders

- Frontend URL: `<vercel-frontend-url>`
- Backend URL: `<render-backend-url>`
- API docs: `<render-backend-url>/docs`
