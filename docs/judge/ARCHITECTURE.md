# Architecture (Judge-Friendly)

This document explains WalletMind architecture from request entry to data persistence.

## Overall Architecture

```mermaid
flowchart TD
    UI[React Frontend\nDashboard + Agent Playground] --> REST[FastAPI REST Layer]
    UI --> MCPClient[MCP Client/Host]
    MCPClient --> MCPServer[Standalone MCP Server]

    REST --> Coordinator[CoordinatorAgent]
    Coordinator --> Agents[Specialized Agents]
    Agents --> Tools[ADK Function Tools]
    Tools --> Services[WalletMind Services]
    Services --> DB[(SQLite/PostgreSQL via SQLAlchemy)]

    MCPServer --> MCPRegistry[MCP Tool Registry]
    MCPRegistry --> MCPAdapter[WalletMind MCP Adapter]
    MCPAdapter --> Coordinator
```

## FastAPI Layer

FastAPI provides versioned REST APIs at `/api/v1`.

Responsibilities:

- Input validation (Pydantic schemas).
- Routing for statements, assistant, AI health, and coordinator execution.
- Dependency injection for services and coordinator runtime.

## Coordinator Layer

`CoordinatorAgent` is the orchestration entry point for intelligent execution.

Responsibilities:

- Parse user intent and route execution mode.
- Decide single-agent vs multi-agent strategy.
- Aggregate specialized agent outputs.
- Produce decision metadata and execution trace.

### Coordinator Workflow

```mermaid
flowchart TD
    Req[Request: query + inputs] --> Resolve[Resolve statement context]
    Resolve --> Decide[Coordinator decision logic]
    Decide -->|single| One[Run selected specialized agent]
    Decide -->|multi| Many[Run health+insights+budget+report+assistant]
    One --> Aggregate[Aggregate response payload]
    Many --> Aggregate
    Aggregate --> Resp[Return API/MCP response]
```

## Specialized Agent Layer

Specialized agents encapsulate one financial domain each:

- `ProcessingAgent`
- `HealthAgent`
- `InsightsAgent`
- `BudgetAgent`
- `ReportAgent`
- `AssistantAgent`

### Specialized Agent Topology

```mermaid
flowchart LR
    Coordinator[CoordinatorAgent] --> Processing[ProcessingAgent]
    Coordinator --> Health[HealthAgent]
    Coordinator --> Insights[InsightsAgent]
    Coordinator --> Budget[BudgetAgent]
    Coordinator --> Report[ReportAgent]
    Coordinator --> Assistant[AssistantAgent]

    Processing --> T1[processing_tool]
    Health --> T2[health_tool]
    Insights --> T3[insights_tool]
    Budget --> T4[budget_tool]
    Report --> T5[report_tool]
    Assistant --> T6[assistant_tool]
```

## ADK Function Tools Layer

Function Tools are the deterministic invocation boundary between agents and business services.

### Function Tool Flow

```mermaid
sequenceDiagram
    participant A as Specialized Agent
    participant F as ADK FunctionTool
    participant S as WalletMind Service
    participant D as Database

    A->>F: invoke(args)
    F->>S: validated payload
    S->>D: query/compute/persist
    D-->>S: records/results
    S-->>F: domain result
    F-->>A: standardized tool payload
```

## WalletMind Services Layer

Domain services execute business and analytics logic:

- statement ingestion and processing
- transaction retrieval
- financial health computation
- spending insight generation
- budget recommendation generation
- monthly report assembly
- retrieval-grounded assistant responses

## Database Layer

SQLAlchemy-backed storage persists:

- users
- statements
- transactions
- analysis artifacts

## MCP Architecture

MCP runs independently from main FastAPI app and reuses WalletMind capabilities through adapter/registry composition.

### MCP Architecture Diagram

```mermaid
flowchart TD
    Host[MCP Consumer Host] --> MCPHTTP[/mcp/* endpoints]
    MCPHTTP --> Infra[MCPInfrastructureServer]
    Infra --> Registry[MCPToolRegistry]
    Infra --> Adapter[WalletMindMCPAdapter]
    Adapter --> Tools[Registered WalletMind Tools]
    Tools --> Coordinator[CoordinatorAgent]
```

## REST + MCP Coexistence

Both interfaces coexist without changing business logic.

```mermaid
flowchart LR
    UI[Frontend] --> REST[FastAPI /api/v1]
    Ext[External MCP Host] --> MCP[MCP /mcp]
    REST --> Core[Shared Services + Agents]
    MCP --> Core
```

## Execution Timeline Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant P as Agent Playground
    participant API as /api/v1/agents/execute
    participant C as CoordinatorAgent
    participant SA as Specialized Agents
    participant T as Function Tools

    U->>P: Execute analysis
    P->>API: POST request
    API->>C: build context + execute
    C->>SA: orchestrate single/multi execution
    SA->>T: invoke domain tools
    T-->>SA: structured results
    SA-->>C: agent outputs
    C-->>API: aggregated payload + trace
    API-->>P: response envelope
    P-->>U: timeline + cards + status
```
