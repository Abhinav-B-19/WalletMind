# API Examples

Copy-paste examples for judge validation.

Assumption:

- Backend: `http://127.0.0.1:8000`
- MCP: `http://127.0.0.1:8100`

Replace `<statement_uuid>` with a processed statement UUID.

## 1. Health

### Request

```bash
curl -X GET 'http://127.0.0.1:8000/api/v1/statements/<statement_uuid>/health-score'
```

### Expected Response (shape)

```json
{
  "success": true,
  "message": "Statement health score generated successfully.",
  "data": {
    "statement_uuid": "<statement_uuid>",
    "overall_score": 0,
    "grade": "string",
    "component_scores": {},
    "explanation": "string"
  }
}
```

## 2. Insights

### Request

```bash
curl -X GET 'http://127.0.0.1:8000/api/v1/statements/<statement_uuid>/insights'
```

### Expected Response (shape)

```json
{
  "success": true,
  "message": "Statement insights generated successfully.",
  "data": {
    "statement_uuid": "<statement_uuid>",
    "insights": [],
    "summary": "string"
  }
}
```

## 3. Budget

### Request

```bash
curl -X GET 'http://127.0.0.1:8000/api/v1/statements/<statement_uuid>/budget-recommendations'
```

### Expected Response (shape)

```json
{
  "success": true,
  "message": "Statement budget recommendations generated successfully.",
  "data": {
    "statement_uuid": "<statement_uuid>",
    "total_savings_opportunity": 0,
    "recommendations": []
  }
}
```

## 4. Report

### Request

```bash
curl -X GET 'http://127.0.0.1:8000/api/v1/statements/<statement_uuid>/monthly-report'
```

### Expected Response (shape)

```json
{
  "success": true,
  "message": "Statement monthly report generated successfully.",
  "data": {
    "statement_uuid": "<statement_uuid>",
    "executive_summary": "string",
    "highlights": [],
    "action_plan": []
  }
}
```

## 5. Assistant

### Request

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/assistant/chat' \
  -H 'Content-Type: application/json' \
  -d '{
    "statement_id": "<statement_uuid>",
    "question": "Where can I reduce monthly spend?"
  }'
```

### Expected Response (shape)

```json
{
  "success": true,
  "message": "Assistant response generated successfully.",
  "data": {
    "answer": "string",
    "citations": []
  }
}
```

## 6. Coordinator

### Request

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/agents/execute' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Analyze spending, score health, and suggest budget actions",
    "user_id": "judge-user",
    "session_id": "judge-session",
    "inputs": {
      "statement_uuid": "<statement_uuid>"
    }
  }'
```

### Expected Response (shape)

```json
{
  "success": true,
  "message": "Coordinator execution completed successfully.",
  "data": {
    "decision_record": {
      "execution_mode": "single"
    },
    "individual_agent_results": []
  }
}
```

## 7. MCP

### List Tools

```bash
curl -X GET 'http://127.0.0.1:8100/mcp/tools'
```

Expected tools include:

- `analyze_finances`
- `processing_tool`
- `health_tool`
- `insights_tool`
- `budget_tool`
- `report_tool`
- `assistant_tool`

### Execute Coordinator via MCP

```bash
curl -X POST 'http://127.0.0.1:8100/mcp/tools/analyze_finances/execute' \
  -H 'Content-Type: application/json' \
  -d '{
    "args": {
      "query": "Summarize financial health and top budget actions",
      "user_id": "judge-user",
      "session_id": "judge-session",
      "inputs": {
        "statement_uuid": "<statement_uuid>",
        "statement_id": "<statement_uuid>"
      }
    }
  }'
```

### Expected Response (shape)

```json
{
  "success": true,
  "tool_name": "analyze_finances",
  "result": {
    "decision_record": {
      "execution_mode": "single"
    }
  },
  "error": null
}
```
