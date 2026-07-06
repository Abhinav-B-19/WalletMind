# MCP Tools (Sprint 2.2)

WalletMind MCP exposes existing capabilities only.

No business logic is implemented in MCP.

## Tool Mapping

| MCP Tool         | ADK Function Tool / Orchestration | WalletMind Service / Runtime Path                            |
| ---------------- | --------------------------------- | ------------------------------------------------------------ |
| processing_tool  | PROCESSING_TOOL                   | StatementProcessingService                                   |
| health_tool      | HEALTH_TOOL                       | FinancialHealthService                                       |
| insights_tool    | INSIGHTS_TOOL                     | SpendingInsightsService                                      |
| budget_tool      | BUDGET_TOOL                       | BudgetService                                                |
| report_tool      | REPORT_TOOL                       | FinancialReportService                                       |
| assistant_tool   | ASSISTANT_TOOL                    | FinancialAssistantService                                    |
| analyze_finances | CoordinatorAgent orchestration    | Coordinator -> Workflow -> Specialized Agents -> Aggregation |

## Execution Paths

### processing_tool

processing_tool
-> PROCESSING_TOOL
-> processing_tool(...)
-> run_processing_tool(...)
-> StatementProcessingService.process_statement(...)

### health_tool

health_tool
-> HEALTH_TOOL
-> health_tool(...)
-> run_health_tool(...)
-> FinancialHealthService.generate_statement_health_score(...)

### insights_tool

insights_tool
-> INSIGHTS_TOOL
-> insights_tool(...)
-> run_insights_tool(...)
-> SpendingInsightsService.generate_statement_insights(...)

### budget_tool

budget_tool
-> BUDGET_TOOL
-> budget_tool(...)
-> run_budget_tool(...)
-> BudgetService.generate_statement_budget_recommendations(...)

### report_tool

report_tool
-> REPORT_TOOL
-> report_tool(...)
-> run_report_tool(...)
-> FinancialReportService.generate_monthly_report(...)

### assistant_tool

assistant_tool
-> ASSISTANT_TOOL
-> assistant_tool(...)
-> run_assistant_tool(...)
-> FinancialAssistantService.chat(...)

### analyze_finances

analyze_finances
-> CoordinatorAgent.execute(...)
-> capability routing
-> specialized agent execution
-> aggregated response payload

## Notes

- MCP adapter reads ADK tool declarations and maps their schemas into registry metadata.
- MCP server executes registry handlers only; it does not call WalletMind services directly.
- Service-layer behavior remains unchanged and authoritative.
