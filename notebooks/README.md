# WalletMind Kaggle Notebooks

This folder contains the Kaggle-facing notebook experience for WalletMind and stays terminology-aligned with the main architecture and judge documentation.

## Official Submission Notebook

- `walletmind_capstone_submission.ipynb`
  - Single official Kaggle submission notebook
  - Judge-first executive structure with rubric mapping and deployment verification
  - Executed top-to-bottom with saved outputs
  - Uses the same architecture language as `README.md` and `docs/judge/ARCHITECTURE.md` (Coordinator, Specialized Agents, Function Tools, MCP, shared REST/MCP core)

## Exported Artifact

- `exported/walletmind_capstone_submission.html`
  - Generated from the executed notebook
  - Ready for browser-based review and sharing

## Folder Structure

- `helpers/`
  - Reusable rendering utilities for K1-K4 notebook phases
  - Includes: `render_title`, `render_callout`, `render_badge`, `render_section`, `render_card`, `render_table`
- `assets/`
  - Notebook-local assets if needed in future phases
  - K1 intentionally reuses root `../assets/` artifacts

## Reused Assets (K1)

Architecture:

- `../assets/diagrams/walletmind-architecture-overview.png`

Product screenshots:

- `../assets/screenshots/landing-page.png`
- `../assets/screenshots/dashboard.png`
- `../assets/screenshots/upload.png`
- `../assets/screenshots/agent-playground.png`
- `../assets/screenshots/judge-hub.png`
- `../assets/screenshots/health-card.png`
- `../assets/screenshots/budget-card.png`
- `../assets/screenshots/insights-card.png`
- `../assets/screenshots/report-card.png`
- `../assets/screenshots/assistant-card.png`
- `../assets/screenshots/swagger-rest.png`
- `../assets/screenshots/swagger-mcp.png`

## Source Documentation Reused

- `../README.md`
- `../docs/judge/README.md`
- `../docs/judge/JUDGE_CHECKLIST.md`
- `../docs/judge/RUBRIC_MAPPING.md`
- `../docs/judge/QUICK_START.md`
- `../docs/judge/API_EXAMPLES.md`
- `../docs/mcp-architecture.md`
- `../docs/mcp-tools.md`
- `../docs/architecture/overview.md`
- `../docs/screenshots/README.md`
- `../docs/evaluation/kaggle_mapping.md`

## Validation Notes

K1 notebook is intentionally static-first and does not require backend/frontend/database availability.
This ensures top-to-bottom execution in isolated notebook environments.

## Consistency Guardrails

- Coordinator terminology must match `backend/app/agents/coordinator_agent.py` and `docs/judge/ARCHITECTURE.md`.
- Workflow wording should reflect that `backend/app/adk/workflow.py` currently provides a bootstrap workflow skeleton.
- Any runtime endpoint references should match `docs/judge/QUICK_START.md`.
