# Security

This document captures implemented and expected security controls for WalletMind.

## Current Implemented Controls

## Session and Request Controls

- Session middleware enabled in FastAPI with signed cookie support.
- Session configuration is environment-driven (`session_secret_key`, cookie name, max age, secure flag).
- Request-scoped context binding is applied via middleware.

Relevant files:

- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/request_context.py`

## API Boundary Controls

- Pydantic request validation on API payloads.
- Structured API response envelopes for predictable error handling.
- Coordinator endpoint validates statement context resolution and rejects ambiguous selection.

Relevant files:

- `backend/app/routers/agents.py`
- `backend/app/schemas/response.py`
- `backend/app/api/errors.py`

## CORS and Origin Policy

- Allowed origins are parsed from environment config.
- Credentials are enabled for authenticated browser flows.

Relevant files:

- `backend/app/core/config.py`
- `backend/app/main.py`

## AI Key and Model Controls

- Gemini API key loaded from environment (`GEMINI_API_KEY` or `GOOGLE_API_KEY`).
- Session-scoped key caching and lock protection exist in app state.
- Model, temperature, and token limits are configuration-driven.

Relevant files:

- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/app/routers/ai.py`

## Data Handling Controls

- Statement upload and processing use service-layer boundaries.
- Persistence through SQLAlchemy model layer.
- Local storage paths are explicit and repository-scoped by default.

Relevant files:

- `walletmind/services/statement_upload_service.py`
- `walletmind/services/statement_processing_service.py`
- `backend/app/database/`

## Security Risks to Address Before Public Production

- Default development session secret must be replaced.
- `session_cookie_secure` should be enabled under HTTPS.
- CORS allowlist should be narrowed to production domains.
- Secret scanning and dependency vulnerability scanning should be enforced in CI.
- Public MCP exposure policy should be explicitly documented and constrained.

## Recommended Security Validation Checklist

- [ ] No hard-coded API keys or secrets in source.
- [ ] Environment variables loaded from secure secret manager in deployment.
- [ ] Session cookie secure settings verified in production.
- [ ] CORS policy validated against frontend origin(s).
- [ ] Error responses do not leak internals.
- [ ] Dependency updates and vulnerability scans run regularly.
- [ ] Upload validation constraints enforced (type/size/content checks).

## Compliance and Audit Notes

WalletMind prioritizes explainability and deterministic execution boundaries through coordinator traces and function-tool/service separation, which improves auditability for judge and review workflows.
