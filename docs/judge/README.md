# Judge Hub: WalletMind

WalletMind is an AI-first personal finance intelligence workspace that turns uploaded bank statements into explainable, actionable outputs in minutes.

This Judge Hub is designed for a 5-minute evaluation flow.

## Project Overview

WalletMind provides a complete statement-to-insight pipeline:

1. Upload a bank statement.
2. Parse and normalize transactions.
3. Generate financial health, insights, budget recommendations, and monthly report outputs.
4. Use a grounded AI assistant for follow-up questions.
5. Run multi-agent orchestration through a dedicated Agent Playground.

## Why WalletMind

- Demonstrates production-style AI engineering, not just prompt demos.
- Combines deterministic financial computation with LLM explanations.
- Exposes both REST APIs and MCP tools for modern AI integration patterns.
- Includes test coverage across ADK runtime, agents, MCP infrastructure, and frontend UX.

## Problem It Solves

Users often have transaction data but no structured intelligence. WalletMind converts raw statement files into:

- Measurable financial health scoring.
- Spend pattern diagnostics and trend insights.
- Actionable budget opportunities.
- Executive-style monthly reporting.
- Conversational, retrieval-grounded Q&A.

## Technology Stack

- Frontend: React, TypeScript, Vite, React Query, Tailwind.
- Backend: FastAPI, Pydantic, SQLAlchemy.
- AI Runtime: Google ADK (`google.adk.Agent`, ADK Function Tools).
- Agent System: Coordinator + specialized agents.
- Protocol Layer: Standalone MCP server with auto-registered WalletMind tools.
- Testing: Pytest (backend), Vitest + Testing Library (frontend).

## AI Architecture Summary

High-level flow:

- UI or API triggers analysis request.
- `CoordinatorAgent` routes execution strategy (single or multi-agent).
- Specialized agents invoke ADK Function Tools.
- Tools call deterministic WalletMind services.
- Results are aggregated and returned to API/UI and MCP consumers.

## Feature Highlights

- Statement upload and processing workflow.
- AI Dashboard (health, insights, budget, report cards).
- Agent Playground with coordinator timeline and per-agent cards.
- Financial Assistant with grounded responses.
- MCP endpoints for tool discovery and execution.

## Judge Document Index

- [Quick Start](./QUICK_START.md)
- [Demo Guide](./DEMO_GUIDE.md)
- [Architecture + Diagrams](./ARCHITECTURE.md)
- [Rubric Mapping](./RUBRIC_MAPPING.md)
- [API Examples](./API_EXAMPLES.md)
- [Evaluation Summary Cheat Sheet](./EVALUATION_SUMMARY.md)
- [Required Screenshot List](../screenshots/README.md)

## Fast Path For Judges

1. Follow [Quick Start](./QUICK_START.md).
2. Run Scenario 1 and Scenario 4 from [Demo Guide](./DEMO_GUIDE.md).
3. Review architecture diagrams in [Architecture](./ARCHITECTURE.md).
4. Validate rubric alignment in [Rubric Mapping](./RUBRIC_MAPPING.md).
