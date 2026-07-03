# WalletMind

WalletMind is an AI-first financial intelligence platform that converts raw bank statements into actionable insights, deterministic scores, grounded assistant responses, and advisor-style monthly reports.

This repository is the capstone submission build, optimized for product clarity, technical transparency, and production-style engineering quality.

## Screenshots (Placeholders)

- Landing Page: `assets/screenshots/landing-page-placeholder.png`
- AI Dashboard: `assets/screenshots/ai-dashboard-placeholder.png`
- Financial Health: `assets/screenshots/financial-health-placeholder.png`
- AI Assistant: `assets/screenshots/assistant-placeholder.png`
- Monthly Report: `assets/screenshots/monthly-report-placeholder.png`

## Architecture Diagram (Placeholder)

- Architecture diagram: `assets/diagrams/walletmind-architecture-placeholder.png`

## Project Overview

WalletMind delivers a complete statement-to-intelligence workflow:

1. Upload statement files (CSV, XLS/XLSX, PDF, image-based parsing paths).
2. Parse and normalize transactions into a consistent schema.
3. Run deterministic engines for financial health, insights, and budgeting.
4. Layer Gemini reasoning for explanations, recommendations, and assistant responses.
5. Present outcomes through a polished React SaaS interface.

## Core Features

- Statement upload, library management, and processing status tracking.
- Transaction enrichment and classification (merchant, category, channel, recurring signals).
- Spending Insights with category, merchant, and cash flow visualizations.
- Financial Health score with component breakdown and recommendations.
- Budget Recommendations with deterministic savings opportunities.
- AI Financial Assistant with grounded source references.
- Monthly Financial Report with executive summary, risks, and action plan.

## Tech Stack

- Frontend: React, TypeScript, React Router, React Query, Recharts, Tailwind CSS.
- Backend: FastAPI, Pydantic, SQLAlchemy.
- AI: Gemini API integration.
- Testing: Pytest (backend), Vitest + Testing Library (frontend).

## Repository Structure

```text
backend/                  FastAPI app, services, routers, schemas
frontend/                 React app, pages, features, components, hooks
walletmind/               Core domain package and shared backend logic
tests/                    Backend test suites
docs/                     Architecture, implementation, deployment docs
assets/                   Branding, diagrams, screenshots, notebook assets
notebook/                 Kaggle/demo notebook assets
scripts/                  Utilities and automation scripts
storage/                  Runtime storage (db, uploads, cache)
```

## Setup

### 1. Clone

```bash
git clone <your-repo-url>
cd WalletMind
```

### 2. Backend Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set your Gemini key in `.env`:

```env
GEMINI_API_KEY=your_key_here
```

Run backend:

```bash
python backend/app/main.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Optional frontend env (`frontend/.env`):

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Run frontend:

```bash
npm run dev
```

## Environment Variables

Backend (`.env`):

- `GEMINI_API_KEY` (required)
- `GEMINI_MODEL` (default: `gemini-2.5-flash`)
- `TEMPERATURE` (default: `0.2`)
- `MAX_OUTPUT_TOKENS` (default: `2048`)

Frontend (`frontend/.env`, optional):

- `VITE_API_BASE_URL` (default: `http://127.0.0.1:8000`)

## API Overview

Representative API endpoints:

- `POST /api/v1/users/register`
- `POST /api/v1/statements/upload`
- `GET /api/v1/statements`
- `GET /api/v1/statements/{statement_uuid}/transactions`
- `GET /api/v1/statements/{statement_uuid}/health-score`
- `GET /api/v1/statements/{statement_uuid}/insights`
- `GET /api/v1/statements/{statement_uuid}/budget-recommendations`
- `GET /api/v1/statements/{statement_uuid}/monthly-report`
- `POST /api/v1/assistant/chat`

## Testing & Validation

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

## Development Notes

- Prefer deterministic computations for financial math; AI augments explanations.
- Reuse existing hooks and feature components before creating new abstractions.
- Keep assistant answers grounded with source transaction evidence.

## Future Roadmap

- Export-ready PDF monthly reports.
- Multi-statement trend aggregation.
- Scenario simulation and goal planning workflows.
- Role-based collaboration and shared household workspaces.

## Contribution

1. Create a feature branch.
2. Keep changes scoped and tested.
3. Run backend and frontend validation suites before opening PR.
4. Document architecture-impacting changes in `docs/`.

## License

This project is licensed under the terms in `LICENSE`.
