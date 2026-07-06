# Google AI Agents Capstone - WalletMind

## 1. Project Overview

WalletMind is an AI Multi-Agent Financial Intelligence Platform built with Google ADK.
It combines deterministic financial services, ADK function tools, specialized agents,
and a coordinator agent to provide explainable financial orchestration without moving
core business logic away from the existing service layer.

## 2. Problem Statement

Traditional financial dashboards are limited because they are static and require
users to manually navigate multiple views to answer financial questions.

AI agent orchestration improves this experience by:

- Mapping intent to capabilities
- Running focused agent pipelines for each goal
- Returning transparent decision records and traces
- Preserving deterministic service guarantees for trust and auditability

## 3. Architecture

FastAPI
-> ADK Runner
-> ADK Workflow
-> Coordinator Agent
-> Capability-based Agent Registry
-> Specialized ADK Agents
-> Google ADK Function Tools
-> Existing WalletMind Services
-> Database

Layer roles:

- FastAPI: API transport and request validation
- ADK Runner: runtime orchestration entrypoint
- ADK Workflow: execution graph abstraction
- Coordinator Agent: intent and capability routing orchestration
- Agent Registry: capability-driven agent discovery
- Specialized Agents: passive, single-tool execution units
- Function Tools: typed delegation boundary to business services
- Services: deterministic financial intelligence source of truth
- Database: persistence only behind services

## 4. Specialized Agents

### ProcessingAgent

- Responsibilities: statement processing orchestration trigger
- Capabilities: processing, statement, ingestion
- Function Tool: processing_tool
- WalletMind Service: StatementProcessingService

### HealthAgent

- Responsibilities: health-score analysis execution
- Capabilities: health, financial_health, score, risk
- Function Tool: health_tool
- WalletMind Service: FinancialHealthService

### InsightsAgent

- Responsibilities: spending-insight execution
- Capabilities: insights, spending, analytics
- Function Tool: insights_tool
- WalletMind Service: SpendingInsightsService

### BudgetAgent

- Responsibilities: budget recommendation execution
- Capabilities: budget, planning, savings
- Function Tool: budget_tool
- WalletMind Service: BudgetService

### ReportAgent

- Responsibilities: monthly report execution
- Capabilities: report, monthly_report, summary
- Function Tool: report_tool
- WalletMind Service: FinancialReportService

### AssistantAgent

- Responsibilities: conversational financial assistant execution
- Capabilities: assistant, financial_advice, chat
- Function Tool: assistant_tool
- WalletMind Service: FinancialAssistantService

## 5. Coordinator

The CoordinatorAgent is the only orchestration intelligence component.

It handles:

- Intent recognition
- Capability routing
- Agent discovery
- Workflow descriptor generation
- Execution trace generation
- Decision record generation
- Aggregation
- Failure isolation

It does not perform:

- Financial calculations
- Direct business-service calls
- Database access
- Prompt engineering for business logic

## 6. Google ADK Usage

WalletMind uses official ADK 2.x primitives:

- Runner
- Workflow
- Agent
- FunctionTool
- SessionService
- MemoryService

Why official ADK patterns were chosen:

- Standardized execution lifecycle and extensibility
- Native compatibility with future ADK workflow features
- Reduced custom framework surface and lower maintenance risk
- Strong alignment with capstone evaluation criteria for authentic ADK usage

## 7. Execution Flow

### Single-Agent Flow

Intent -> capability -> one specialized agent -> one function tool -> one service

Examples:

- "Generate health score" -> HealthAgent
- "Give me budgeting advice" -> BudgetAgent

### Multi-Agent Flow

Intent -> capability pipeline -> ordered specialized agents -> aggregation

Example:

- "Analyze my finances" -> Health -> Insights -> Budget -> Report -> Assistant

## 8. Validation

Validation includes:

- Regression tests for existing API behavior
- Smoke tests for specialized agent execution
- Coordinator tests for discovery and orchestration
- Workflow metadata checks
- API tests for /api/v1/agents/execute

Result: core regression and orchestration suites pass with no business logic movement.

## 9. Submission Mapping

| Rubric Requirement | WalletMind Implementation |
| --- | --- |
| Agent / Multi-Agent | CoordinatorAgent + Specialized ADK Agents |
| MCP | Planned for Sprint 2 using existing tool/agent contracts |
| Deployability | Render + Vercel + Neon architecture path |
| Security | Server-side Gemini, input validation, env vars, no client key exposure |
| Agent Skills | ADK Runner, ADK Workflow, Coordinator, Function Tools |

## 10. Architecture Highlights

Intentional architecture decisions:

- Business logic stays in deterministic services.
- Function Tools delegate; they do not calculate.
- Specialized agents are passive execution units.
- Coordinator plans and orchestrates.
- Workflow metadata keeps execution transport-agnostic.

This separation is deliberate for reliability, explainability, and low regression risk.
