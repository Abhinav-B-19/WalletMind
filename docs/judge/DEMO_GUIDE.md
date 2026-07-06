# Demo Guide

This walkthrough is optimized for judge evaluation and storytelling.

## Scenario 1: End-to-End Product Experience

### Purpose

Show the full user value chain from file upload to explainable AI output.

### Steps

1. Open upload page: `http://localhost:5173/app/statements/upload`.
2. Upload a sample statement (`sample_data/upload-test.csv`).
3. Open dashboard: `http://localhost:5173/app/dashboard`.
4. Inspect financial health, budget, insights, and report cards.
5. Open Agent Playground: `http://localhost:5173/app/agent-playground`.
6. Execute the default multi-agent run.
7. Inspect coordinator summary, timeline, and per-agent cards.
8. Open Assistant page and ask a follow-up financial question.

### Expected Outcome

- Statement enters processed status and drives downstream analysis.
- Dashboard visualizations render correctly.
- Agent Playground timeline and cards match coordinator output.
- Assistant returns grounded financial responses.

## Scenario 2: MCP Tool Execution

### Purpose

Demonstrate standards-based AI capability exposure through MCP.

### Steps

1. Start MCP server (`python -m backend.app.mcp.server`).
2. Open MCP docs: `http://127.0.0.1:8100/docs`.
3. Call `GET /mcp/tools`.
4. Verify tool list includes WalletMind tools.
5. Execute `POST /mcp/tools/analyze_finances/execute` with valid payload.

### Expected Outcome

- MCP endpoint returns tool registry metadata.
- Execution endpoint returns coordinator-backed result payload.
- Demonstrates REST + MCP coexistence without logic duplication.

## Scenario 3: Coordinator Endpoint

### Purpose

Validate orchestration API contract and routing behavior.

### Steps

1. Open REST docs: `http://127.0.0.1:8000/docs`.
2. Execute `POST /api/v1/agents/execute`.
3. Use a query and `statement_uuid` in `inputs`.
4. Observe aggregated response envelope.

### Expected Outcome

- Response includes coordinator decision record.
- Contains per-agent execution outputs and status metadata.
- Endpoint works without modifying existing service contracts.

## Scenario 4: Multi-Agent Orchestration

### Purpose

Show decomposition of one request into specialized agent execution.

### Steps

1. Open Agent Playground.
2. Select multi-agent mode.
3. Run query: "Provide health, spending insights, budget actions, and monthly summary".
4. Expand timeline and per-agent cards.

### Expected Outcome

- Coordinator triggers specialized agents (health/insights/budget/report/assistant).
- Timeline clearly shows sequence and statuses.
- Output cards provide isolated, explainable sub-results.
