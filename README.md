# WalletMind

AI-powered Personal Financial Intelligence Platform

![Google ADK](https://img.shields.io/badge/Google%20ADK-Multi--Agent-blue)
![Model Context Protocol](https://img.shields.io/badge/MCP-Enabled-0ea5e9)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-059669)
![React](https://img.shields.io/badge/React-Frontend-2563eb)
![TypeScript](https://img.shields.io/badge/TypeScript-UI-1d4ed8)
![Python](https://img.shields.io/badge/Python-Backend-16a34a)
![Google Gemini](https://img.shields.io/badge/Gemini-Reasoning-f59e0b)
![License: MIT](https://img.shields.io/badge/License-MIT-10b981)

WalletMind transforms raw bank statements into explainable financial intelligence using a coordinator-led multi-agent architecture built with Google ADK and exposed through both REST and MCP.

## System Architecture

![WalletMind Architecture](assets/diagrams/walletmind-architecture-overview.png)

Architecture highlights:

- Coordinator for intent routing and orchestration strategy.
- Agent Registry for capability-to-agent discovery.
- Specialized agents for health, insights, budget, report, assistant, and processing.
- ADK Function Tools as deterministic execution boundaries.
- Shared WalletMind service layer as the single source of business logic.
- REST APIs for product workflows and MCP endpoints for AI-host interoperability.
- Persistent storage through SQLAlchemy-backed data models.

## Product Preview

### Landing Page

![Landing Page](assets/screenshots/landing-page.png)

### Dashboard

![Dashboard](assets/screenshots/dashboard.png)

### Statement Upload

![Statement Upload](assets/screenshots/upload.png)

### Agent Playground

![Agent Playground](assets/screenshots/agent-playground.png)

### Judge Hub

![Judge Hub](assets/screenshots/judge-hub.png)

### Execution Timeline

![Execution Timeline](assets/screenshots/coordinator-timeline.png)

### Financial Health

![Financial Health](assets/screenshots/health-card.png)

### Budget

![Budget](assets/screenshots/budget-card.png)

### Insights

![Insights](assets/screenshots/insights-card.png)

### Monthly Report

![Monthly Report](assets/screenshots/report-card.png)

### AI Assistant

![AI Assistant](assets/screenshots/assistant-card.png)

### REST Swagger

![REST Swagger](assets/screenshots/swagger-rest.png)

### MCP Swagger

![MCP Swagger](assets/screenshots/swagger-mcp.png)

## Why WalletMind?

Traditional finance apps visualize historical transactions. WalletMind reasons about finances.

- Coordinator-led orchestration routes each request to the right capability mix.
- Multi-agent execution decomposes complex financial analysis into specialized tasks.
- Deterministic tools keep outputs auditable and grounded in real statement data.
- Explainable recommendations show decision traces, not opaque answers.
- REST + MCP enable both product UX and standards-based AI-host integration.

## Key Features

- [x] Google ADK multi-agent system
- [x] Coordinator Agent orchestration layer
- [x] Specialized domain agents
- [x] Agent Registry discovery model
- [x] Function Tool execution boundary
- [x] Standalone MCP server
- [x] Versioned REST APIs
- [x] Agent Playground with timeline
- [x] Judge Hub navigation experience
- [x] Explainable financial analysis
- [x] Budget recommendations
- [x] Monthly financial reports
- [x] Retrieval-grounded AI Assistant

## Google AI Agents Concepts Demonstrated

| Concept | Implementation |
| --- | --- |
| Google ADK | Coordinator + specialized ADK agents |
| Multi-Agent | Coordinator capability routing and aggregation |
| Function Tools | WalletMind Function Tool layer in `backend/app/tools/` |
| MCP | Standalone MCP server + adapter + registry |
| Shared Services | Single source of business logic in WalletMind services |
| Explainability | Decision records, timeline traces, and per-agent outputs |

## AI Execution Flow

```mermaid
flowchart TD
	U[User Query] --> C[Coordinator Agent]
	C --> D[Capability Discovery]
	D --> A[Specialized Agents]
	A --> T[ADK Function Tools]
	T --> S[WalletMind Services]
	S --> DB[(Database)]
```

## Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | React + TypeScript + Vite | Interactive financial product UX |
| State/Data | React Query + Axios | Async API state and request orchestration |
| Backend API | FastAPI + Pydantic | Versioned API contracts and validation |
| Persistence | SQLAlchemy | Statement, transaction, and analysis storage |
| AI Runtime | Google ADK + Gemini | Planner-driven agent reasoning |
| Tool Boundary | ADK FunctionTool | Deterministic service invocation contracts |
| Protocol Interop | Model Context Protocol (MCP) | Tool discovery and execution for AI hosts |
| Testing | Pytest + Vitest + Testing Library | Backend and frontend quality gates |

## Quick Start

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app.main
```

Backend: `http://127.0.0.1:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`

### MCP

```bash
cd ..
source .venv/bin/activate
python -m backend.app.mcp.server
```

MCP: `http://127.0.0.1:8100`

### Swagger

- REST Swagger: `http://127.0.0.1:8000/docs`
- MCP Swagger: `http://127.0.0.1:8100/docs`

### Agent Playground

- `http://127.0.0.1:5173/app/agent-playground`

### Judge Hub

- `http://127.0.0.1:5173/app/judge`

## Demo Flow

1. Upload Statement
2. Dashboard
3. Agent Playground
4. Coordinator Decision
5. Execution Timeline
6. Judge Hub
7. REST Swagger
8. MCP Swagger

## Judge Resources

| Resource | Description |
| --- | --- |
| [📘 Quick Start](docs/judge/QUICK_START.md) | Fastest local setup path for evaluation. |
| [🏗 Architecture](docs/judge/ARCHITECTURE.md) | System design, diagrams, and execution topology. |
| [🎯 Rubric Mapping](docs/judge/RUBRIC_MAPPING.md) | Direct mapping from judging criteria to evidence. |
| [🧪 API Examples](docs/judge/API_EXAMPLES.md) | Copy-paste REST and MCP validation requests. |
| [📑 Evaluation Summary](docs/judge/EVALUATION_SUMMARY.md) | Compact capstone evidence cheat sheet. |
| [▶ Demo Guide](docs/judge/DEMO_GUIDE.md) | Scenario-driven walkthrough for live judging. |
| [✅ Judge Checklist](docs/judge/JUDGE_CHECKLIST.md) | Fast verification checklist during review. |

## Future Roadmap

- Export-ready PDF reporting.
- Multi-statement trend and seasonality intelligence.
- Goal simulation and what-if planning depth.
- Extended collaboration flows for households/advisors.
- Optional advanced MCP service integrations.

## License

This project is licensed under the [MIT License](LICENSE).
