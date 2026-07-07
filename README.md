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

## Why WalletMind

Traditional finance apps mostly visualize transactions. WalletMind adds orchestration, explainability, and actionable recommendations:

- Coordinator-based intent routing with explicit execution strategy.
- Specialized AI agents for health, insights, budget, report, assistant, and processing.
- Deterministic Function Tools to preserve auditable business logic boundaries.
- Shared core reused by both REST and MCP, avoiding logic duplication.
- Judge-facing transparency via Agent Playground timeline and per-agent result cards.

## Architecture (Code-Derived)

### Overall System Architecture

```mermaid
flowchart TD
    FE[React Frontend\nLanding Dashboard Upload Settings\nAgent Playground Judge Hub] --> REST[FastAPI REST /api/v1]
    REST --> COORD[CoordinatorAgent]
    COORD --> AGENTS[Specialized Agents]
    AGENTS --> TOOLS[ADK Function Tools]
    TOOLS --> SERVICES[WalletMind Services]
    SERVICES --> DB[(SQLite or PostgreSQL via SQLAlchemy)]

    MCP_CLIENT[External MCP Client or Host] --> MCP_SERVER[MCP Infrastructure Server /mcp]
    MCP_SERVER --> MCP_REG[MCP Tool Registry]
    MCP_REG --> MCP_ADAPTER[WalletMind MCP Adapter]
    MCP_ADAPTER --> COORD
```

### ADK Runtime Diagram

```mermaid
flowchart TD
    RUNTIME[WalletMindAdkRuntimeFactory]
    RUNTIME --> SESSION[Session Service Factory]
    RUNTIME --> MEMORY[Memory Service Factory]
    RUNTIME --> WORKFLOW[Workflow Factory]
    WORKFLOW --> ROOT[Root Workflow\nwalletmind_bootstrap]
    RUNTIME --> RUNNER[google.adk Runner wrapped by WalletMindRunner]

    MAIN[backend.app.main create_app] --> COORD[CoordinatorAgent]
    MAIN --> REG[AgentRegistry]
    REG --> SA[Specialized Agents]
```

### Coordinator Decision Flow

```mermaid
flowchart TD
    REQ[Request: query + user/session + inputs] --> INTENT[Intent Detection]
    INTENT --> CAP[Capability Resolution]
    CAP --> MODE{Execution Mode}
    MODE -->|single| SINGLE[Single Agent Selection]
    MODE -->|multi| MULTI[Ordered Multi-Agent Plan]
    SINGLE --> EXEC[Agent Execution via Registry]
    MULTI --> EXEC
    EXEC --> AGG[Aggregate Results + Trace + Metadata]
    AGG --> RESP[API or MCP Response Envelope]
```

### Specialized Agent Diagram

```mermaid
flowchart LR
    C[CoordinatorAgent] --> P[ProcessingAgent]
    C --> H[HealthAgent]
    C --> I[InsightsAgent]
    C --> B[BudgetAgent]
    C --> R[ReportAgent]
    C --> A[AssistantAgent]

    P --> PT[processing_tool]
    H --> HT[health_tool]
    I --> IT[insights_tool]
    B --> BT[budget_tool]
    R --> RT[report_tool]
    A --> AT[assistant_tool]
```

### Function Tool Diagram

```mermaid
flowchart TD
    AGENT[Specialized Agent] --> FT[ADK FunctionTool]
    FT --> SVC[WalletMind Service]
    SVC --> DB[(Database)]
```

### MCP Architecture

```mermaid
flowchart TD
    EC[External Client] --> MS[MCP Server]
    MS --> MR[MCP Tool Registry]
    MR --> MA[WalletMind MCP Adapter]
    MA --> CO[CoordinatorAgent]
    CO --> SA[Specialized Agents]
    SA --> SV[WalletMind Services]
```

### REST + MCP Shared Core

```mermaid
flowchart LR
    REST[REST /api/v1] --> COORD[Coordinator]
    MCP[MCP /mcp/tools/*/execute] --> COORD
    COORD --> CORE[Shared Core: Agents + Tools + Services]
```

### Frontend Architecture

```mermaid
flowchart TD
    PAGES[Landing Dashboard Upload Settings\nAgent Playground Judge Hub] --> API[Axios API Client + React Query]
    API --> REST[FastAPI /api/v1]
    REST --> COORD[Coordinator]
    COORD --> RESULTS[Aggregated and Per-Agent Results]
    RESULTS --> TIMELINE[Interactive Timeline + Cards]
```

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

## Technology Stack

| Layer            | Technology                          | Purpose                                          |
| ---------------- | ----------------------------------- | ------------------------------------------------ |
| Frontend         | React + TypeScript + Vite           | Product UI and judge workflow                    |
| State/Data       | React Query + Axios                 | Data fetching and cache lifecycle                |
| Backend API      | FastAPI + Pydantic                  | Versioned API contracts                          |
| Persistence      | SQLAlchemy                          | Statement, transaction, and analysis persistence |
| AI Runtime       | Google ADK + Gemini                 | Coordinator and specialized-agent reasoning      |
| Tool Boundary    | ADK FunctionTool                    | Deterministic service invocation                 |
| Protocol Interop | MCP                                 | Tool discovery and execution for AI hosts        |
| Testing          | Pytest + Vitest + Testing Library   | Backend, MCP, ADK, and frontend quality gates    |
| Deployment       | Render + Vercel + GitHub Actions CI | Repeatable delivery workflow                     |

## Security and Configuration

- Session middleware with signed cookies and configurable policy.
- CORS allowlist loaded from environment variables.
- Request context binding for per-request state.
- Environment-driven AI configuration and model controls.
- Session-scoped AI key management with validation and status endpoints.

See: [docs/security/security.md](docs/security/security.md)

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

Frontend: `http://localhost:5173`

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

### Judge Routes

- Agent Playground: `http://localhost:5173/app/agent-playground`
- Judge Hub: `http://localhost:5173/app/judge`

## Evaluation and Evidence

| Requirement       | Evidence                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------- |
| Google ADK        | `backend/app/adk/`, `backend/app/agents/`                                                   |
| Coordinator       | `backend/app/agents/coordinator_agent.py`                                                   |
| Multi-Agent       | `backend/app/agents/*_agent.py`                                                             |
| Function Tools    | `backend/app/tools/`                                                                        |
| MCP               | `backend/app/mcp/`                                                                          |
| REST API          | `backend/app/routers/`, `backend/app/api/router.py`                                         |
| Frontend Judge UX | `frontend/src/pages/app-agent-playground-page.tsx`, `frontend/src/pages/judge-hub-page.tsx` |
| Tests             | `tests/core/`, `tests/api/`, `frontend/src/**/*.test.tsx`                                   |

## Judge Resources

| Resource                                                   | Description                                    |
| ---------------------------------------------------------- | ---------------------------------------------- |
| [Quick Start](docs/judge/QUICK_START.md)                   | Fast local run path for judges                 |
| [Architecture](docs/judge/ARCHITECTURE.md)                 | Code-derived architecture and diagrams         |
| [Rubric Mapping](docs/judge/RUBRIC_MAPPING.md)             | Rubric-to-evidence matrix                      |
| [API Examples](docs/judge/API_EXAMPLES.md)                 | Copy/paste REST and MCP requests               |
| [Evaluation Summary](docs/judge/EVALUATION_SUMMARY.md)     | Capstone concepts checklist                    |
| [Demo Guide](docs/judge/DEMO_GUIDE.md)                     | Scenario walkthrough for recording and judging |
| [Notebook](notebooks/walletmind_capstone_submission.ipynb) | Kaggle-facing narrative notebook               |

## Deployment

- Backend deployment spec: [render.yaml](render.yaml)
- Frontend deployment config: [frontend/vercel.json](frontend/vercel.json)
- CI pipeline: [.github/workflows/ci.yml](.github/workflows/ci.yml)

## License

This project is licensed under the [MIT License](LICENSE).
