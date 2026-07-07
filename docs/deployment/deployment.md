# Deployment

This document describes the currently configured deployment model for WalletMind.

## Deployment Topology

- Backend API: Render (see `render.yaml`)
- Frontend SPA: Vercel (see `frontend/vercel.json`)
- Continuous Integration: GitHub Actions (see `.github/workflows/ci.yml`)

## Backend Deployment (Render)

Reference file: `render.yaml`

Configured behavior:

- Uses Python runtime.
- Installs dependencies from `requirements.txt`.
- Starts backend using `python -m backend.app.main`.
- Reads runtime environment variables from Render environment settings.

Required environment variables:

- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`)
- `GEMINI_MODEL`
- `TEMPERATURE`
- `MAX_OUTPUT_TOKENS`
- `SESSION_SECRET_KEY`
- Any production-specific DB URL or origin settings if overridden.

## Frontend Deployment (Vercel)

Reference file: `frontend/vercel.json`

Configured behavior:

- Builds Vite application from `frontend/`.
- Applies SPA rewrite routing so client-side routes resolve correctly.
- Uses environment variables prefixed with `VITE_`.

Recommended frontend env vars:

- `VITE_API_BASE_URL` (backend host, no `/api/v1` suffix)
- `VITE_APP_VERSION` (optional)
- Optional build metadata variables for settings page display.

## CI Pipeline

Reference file: `.github/workflows/ci.yml`

Current checks:

- Backend: install + pytest.
- Frontend: install + test + lint + build.

This ensures both runtime paths are validated on push and pull request.

## Production Hardening Checklist

- [ ] Replace default session secret with strong random value.
- [ ] Set `session_cookie_secure=true` behind HTTPS.
- [ ] Restrict CORS origins to production hosts only.
- [ ] Provide production-grade database URL when needed.
- [ ] Ensure MCP endpoint exposure policy is explicit (public/internal).
- [ ] Verify no development URLs remain in environment configs.

## Runtime Validation After Deploy

- REST docs available at deployed backend `/docs`.
- MCP docs available at deployed MCP server `/docs`.
- Frontend route `/app/judge` loads and links work.
- End-to-end flow: upload statement -> execute coordinator -> inspect timeline.
