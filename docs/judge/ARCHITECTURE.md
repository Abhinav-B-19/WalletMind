# Architecture (Judge-Friendly)

This document describes WalletMind architecture directly from implementation.

## 1) Overall System Architecture

```mermaid
flowchart TD
    UI[React Frontend\nDashboard + Upload + Agent Playground + Judge Hub] --> REST[FastAPI /api/v1]
    UI --> MCPHOST[MCP Client or Host]
    MCPHOST --> MCPSERVER[Standalone MCP Server /mcp/*]

    REST --> COORD[CoordinatorAgent]
    COORD --> SPEC[Specialized Agents]
    SPEC --> TOOLS[ADK Function Tools]
    TOOLS --> SERVICES[WalletMind Services]
    SERVICES --> DB[(SQLite/PostgreSQL via SQLAlchemy)]

    MCPSERVER --> REG[MCP Tool Registry]
    REG --> ADAPTER[WalletMind MCP Adapter]
    ADAPTER --> COORD
```

## 2) ADK Runtime and App Bootstrapping

The FastAPI app creates and wires:

- ADK runtime via `WalletMindAdkRuntimeFactory`.
- Session and memory service factories.
- A workflow factory (current workflow graph is a bootstrap skeleton node).
- Agent registry and coordinator.

```mermaid
flowchart TD
    APP[backend.app.main create_app] --> RUNTIME[WalletMindAdkRuntimeFactory.create]
    RUNTIME --> SESSION[Session Service]
    RUNTIME --> MEMORY[Memory Service]
    RUNTIME --> WF[Workflow Factory]
    WF --> ROOT[walletmind_bootstrap]

    APP --> REG[AgentRegistry]
    REG --> SA[Processing/Health/Insights/Budget/Report/Assistant]
    APP --> COORD[CoordinatorAgent]
    COORD --> REG
```

## 3) Coordinator Decision Flow

`POST /api/v1/agents/execute` resolves statement context and calls coordinator orchestration.

```mermaid
flowchart TD
    REQ[Request: query + user/session + inputs] --> RESOLVE[Resolve statement_uuid]
    RESOLVE --> INTENT[Intent and capability detection]
    INTENT --> MODE{Execution mode}
    MODE -->|single| SINGLE[Select one specialized agent]
    MODE -->|multi| MULTI[Plan multi-agent execution]
    SINGLE --> EXEC[Execute agent(s) via registry]
    MULTI --> EXEC
    EXEC --> AGG[Aggregate outputs + trace + metadata]
    AGG --> RESP[ApiResponse envelope]
```

## 4) Specialized Agent Topology

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

## 5) Function Tool Boundary

Function Tools are deterministic wrappers from ADK agents into service calls.

```mermaid
sequenceDiagram
    participant SA as Specialized Agent
    participant FT as ADK FunctionTool
    participant S as WalletMind Service
    participant D as Database

    SA->>FT: invoke(args)
    FT->>S: validated payload
    S->>D: query/compute/persist
    D-->>S: data
    S-->>FT: result
    FT-->>SA: standardized payload
```

## 6) MCP Architecture

MCP server runs independently and reuses WalletMind capabilities through registry and adapter composition.

```mermaid
flowchart TD
    HOST[MCP Consumer Host] --> API[/mcp/* endpoints]
    API --> INFRA[MCPInfrastructureServer]
    INFRA --> TOOLS[MCP Tool Registry]
    INFRA --> ADAPTER[WalletMind MCP Adapter]
    ADAPTER --> WTOOLS[analyze_finances + WalletMind tools]
    WTOOLS --> COORD[CoordinatorAgent]
```

## 7) REST and MCP Shared Core

Both interfaces call the same orchestration and service layers.

```mermaid
flowchart LR
    REST[REST /api/v1] --> CORE[Coordinator + Agents + Tools + Services]
    MCP[MCP /mcp/tools/*] --> CORE
```

## 8) Frontend Architecture

```mermaid
flowchart TD
    ROUTES[React Routes] --> PAGES[Dashboard + Upload + Agent Playground + Judge Hub + Settings]
    PAGES --> API[Axios Client + React Query]
    API --> BACKEND[FastAPI /api/v1]
    BACKEND --> COORD[Coordinator response payload]
    COORD --> UI[Timeline + status + per-agent cards]
```

## Execution Timeline (What Judges See)

```mermaid
sequenceDiagram
    participant U as User
    participant AP as Agent Playground
    participant API as /api/v1/agents/execute
    participant C as Coordinator
    participant SA as Specialized Agents
    participant T as Function Tools

    U->>AP: Run analysis
    AP->>API: POST request
    API->>C: execute(context)
    C->>SA: orchestrate single or multi
    SA->>T: call tool
    T-->>SA: result
    SA-->>C: outputs
    C-->>API: aggregate + trace
    API-->>AP: response envelope
    AP-->>U: timeline + cards + summary
```

## Key Implementation Files

- Coordinator: `backend/app/agents/coordinator_agent.py`
- Agent endpoint: `backend/app/routers/agents.py`
- Runtime factory: `backend/app/adk/runtime.py`
- Workflow factory: `backend/app/adk/workflow.py`
- Specialized agents: `backend/app/agents/*_agent.py`
- Function tools: `backend/app/tools/`
- MCP server: `backend/app/mcp/server.py`
- MCP adapter and registry: `backend/app/mcp/adapter.py`, `backend/app/mcp/registry.py`
- Frontend orchestration UI: `frontend/src/pages/app-agent-playground-page.tsx`
- Frontend judge hub: `frontend/src/pages/judge-hub-page.tsx`
