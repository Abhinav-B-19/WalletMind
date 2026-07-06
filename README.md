# WalletMind

WalletMind is an AI-first financial intelligence platform that turns raw bank statements into explainable financial outcomes in minutes.

It combines deterministic financial computation with multi-agent orchestration, Google ADK function tooling, and MCP interoperability.

## Architecture Image

![WalletMind Architecture Overview](assets/diagrams/walletmind-architecture-overview.png)

## Feature Screenshots

Core product screenshots:

- Landing Page: `assets/screenshots/landing-page.png`
- Dashboard: `assets/screenshots/dashboard.png`
- Upload: `assets/screenshots/upload.png`
- Agent Playground: `assets/screenshots/agent-playground.png`
- Coordinator Timeline: `assets/screenshots/coordinator-timeline.png`
- Financial Health: `assets/screenshots/health-card.png`
- Budget Recommendations: `assets/screenshots/budget-card.png`
- Spending Insights: `assets/screenshots/insights-card.png`
- Monthly Report: `assets/screenshots/report-card.png`
- AI Assistant: `assets/screenshots/assistant-card.png`
- REST Swagger: `assets/screenshots/swagger-rest.png`
- MCP Swagger: `assets/screenshots/swagger-mcp.png`

Required judge screenshot checklist is documented at `docs/screenshots/README.md`.

## Demo Assets

This repository currently ships static PNG screenshots for judge validation.
Animated demo GIFs can be added later under `assets/screenshots/`.

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

## Live Demo Endpoints

Local development defaults:

- Frontend URL: `http://127.0.0.1:5173`
- Backend URL: `http://127.0.0.1:8000`
- Backend API docs: `http://127.0.0.1:8000/docs`
- MCP URL: `http://127.0.0.1:8100`
- MCP API docs: `http://127.0.0.1:8100/docs`

## Future Work

- Export-ready PDF monthly reports.
- Multi-statement trend and seasonality analysis.
- Goal simulation and what-if planning.
- Collaboration features for households and advisors.

## License

This project is licensed under `LICENSE`.
