# PROJECT_CONTEXT

## Vision

WalletMind provides a complete AI-first financial intelligence experience from statement upload to actionable monthly planning.

The product philosophy is:

1. Deterministic financial computations for trust.
2. AI narrative and guidance for usability.
3. Grounded explanations tied to real transaction data.
4. Production-quality UX for portfolio and capstone judging.

## Architecture

WalletMind uses a layered architecture:

1. Frontend (React + TypeScript)

- Feature-based modules (`ai-dashboard`, `assistant`, shared UI).
- React Query for server state and cache orchestration.
- Recharts for visual intelligence surfaces.

2. Backend (FastAPI)

- Router layer for API contracts.
- Service layer for deterministic business logic.
- AI service layer for Gemini integrations and response validation.
- SQLAlchemy persistence for statements, users, and transactions.

3. Intelligence flow

- Parse statements.
- Normalize/enrich transactions.
- Run deterministic analytics (health, insights, budgets, reports).
- Apply AI reasoning for summaries and recommendations.

## Database Schema (High-Level)

Primary entities include:

- `User`
- `Statement`
- `Transaction`

Key relationships:

- One user can own many statements.
- One statement can have many transactions.

Storage and DB path are configured in backend core config and default to SQLite under `storage/database/`.

## AI Pipeline

1. Ingest deterministic outputs from analysis services.
2. Build structured prompts with explicit schema expectations.
3. Generate Gemini response.
4. Validate/parse response payload.
5. Fallback gracefully to deterministic-only behavior on AI degradation.

## Completed Modules

- Module 1: Foundation and profile/statement flow.
- Module 2: Intelligence and analytics layers.
- Module 3: AI workflows, monthly report, assistant experience.

Sprints completed:

- 4.1 Dashboard Foundation
- 4.2 Financial Health Experience
- 4.3 Spending Insights Experience
- 4.4 Budget Recommendations Experience
- 4.5 AI Financial Assistant Experience
- 4.6 Monthly Financial Report Experience
- 4.7 Final SaaS polish, documentation, and submission readiness

## Product Roadmap

1. PDF export and report sharing.
2. Multi-month comparative analytics.
3. Goal planner with scenario simulations.
4. Collaboration and household workspace models.

## Folder Structure

```text
backend/                  API, services, schemas, database wiring
frontend/                 React app and product UI
walletmind/               Shared/domain backend package
tests/                    Backend tests
docs/                     Architecture and implementation documentation
assets/                   Branding, diagrams, screenshots placeholders
notebook/                 Kaggle/demo notebook assets
storage/                  Runtime data (uploads, cache, sqlite db)
```

## Development Workflow

1. Create scoped feature branch.
2. Implement changes in smallest safe units.
3. Reuse existing hooks/components/services before adding new code.
4. Run frontend and backend validation before commit.
5. Update documentation when behavior or architecture changes.

## Testing Workflow

Backend:

```bash
python -m pytest
python -m ruff check .
python -m black --check .
```

Frontend:

```bash
cd frontend
npm run lint
npm run test
npm run build
```

## Coding Standards

- Strict typing for API and UI contracts.
- Deterministic calculations remain source-of-truth for financial numbers.
- AI outputs should never replace core deterministic business logic.
- Avoid duplicate hooks, duplicate API calls, and duplicate visual primitives.
- Prefer compositional page assembly from existing feature components.

## Deployment Notes

- Backend defaults to local SQLite storage under `storage/`.
- Configure Gemini key in `.env`.
- Frontend API base URL configurable via `VITE_API_BASE_URL`.
- For portfolio/Kaggle demo, include screenshots and architecture artifacts from `assets/`.
