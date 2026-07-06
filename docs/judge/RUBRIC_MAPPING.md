# Rubric Mapping

This matrix maps evaluation requirements to concrete implementation evidence.

| Requirement                 | Implementation                                           | Evidence                                                                                                                         |
| --------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Agent System                | `CoordinatorAgent` + specialized agents                  | `backend/app/agents/coordinator_agent.py`, `backend/app/agents/`                                                                 |
| Google ADK Runtime          | ADK runtime/session/memory/workflow factories            | `backend/app/adk/runtime.py`, `backend/app/adk/workflow.py`, `backend/app/adk/session.py`, `backend/app/adk/memory.py`           |
| ADK Agent Model             | `google.adk.Agent` in coordinator and specialized agents | `backend/app/agents/coordinator_agent.py`, `backend/app/agents/*_agent.py`                                                       |
| Function Tools              | ADK FunctionTool wrappers for each capability            | `backend/app/tools/`                                                                                                             |
| MCP Server                  | Standalone MCP infrastructure app                        | `backend/app/mcp/server.py`                                                                                                      |
| MCP Tool Registry           | Transport-level registration/discovery/execute registry  | `backend/app/mcp/registry.py`                                                                                                    |
| MCP Adapter                 | WalletMind tool bootstrap into MCP                       | `backend/app/mcp/adapter.py`                                                                                                     |
| REST API                    | Versioned FastAPI composition                            | `backend/app/api/router.py`, `backend/app/routers/`                                                                              |
| Coordinator Endpoint        | Orchestration endpoint                                   | `POST /api/v1/agents/execute`, `backend/app/routers/agents.py`                                                                   |
| Multi-Agent Orchestration   | Decision + parallel/sequential specialized execution     | `backend/app/agents/coordinator_agent.py`                                                                                        |
| Existing Financial Platform | Health/insights/budget/report services reused            | `backend/app/services/health/`, `backend/app/services/analysis/`, `backend/app/services/budget/`, `backend/app/services/report/` |
| Assistant Capability        | Retrieval-grounded assistant workflow                    | `backend/app/services/assistant/`, `backend/app/agents/assistant_agent.py`                                                       |
| Frontend Judge UX           | Agent Playground timeline + cards + demo defaults        | `frontend/src/pages/app-agent-playground-page.tsx`                                                                               |
| Dashboard Experience        | Financial dashboard pages and components                 | `frontend/src/features/ai-dashboard/`                                                                                            |
| Test Coverage (ADK)         | ADK runtime and workflow tests                           | `tests/core/adk/`                                                                                                                |
| Test Coverage (Agents)      | Coordinator + specialized agent tests                    | `tests/core/agents/`                                                                                                             |
| Test Coverage (MCP)         | MCP server/adapter/registry/config tests                 | `tests/core/mcp/`                                                                                                                |
| Test Coverage (Frontend)    | UI and route tests including Agent Playground            | `frontend/src/**/*.test.tsx`, `frontend/src/**/*.test.ts`                                                                        |

## Evidence Notes

- MCP auto-registration evidence is validated in `tests/core/mcp/test_server.py::test_walletmind_tools_auto_registered_in_sprint_2_2`.
- API execution evidence is validated in `tests/api/test_agents_execute_api.py`.
- Frontend timeline/toast/default behavior is validated in `frontend/src/pages/app-agent-playground-page.test.tsx`.
