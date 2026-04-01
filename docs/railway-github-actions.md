# Railway GitHub Actions Deploy

This repository now ships with a manual Railway deployment workflow at `.github/workflows/deploy.yml`.

## What it does

- Runs only when manually triggered from GitHub Actions.
- Fails unless the selected ref is `main`.
- Deploys services in this order:
  - `chroma`
  - `backend`
  - `frontend`
- Can bootstrap missing repo-backed Railway services only when you explicitly choose `create_missing_services = yes`.
- Fails fast when required secrets are missing.
- Waits for each Railway deployment to reach `SUCCESS` before continuing.

## Required GitHub secrets

- `RAILWAY_API_TOKEN`
- `RAILWAY_PROJECT`
- `RAILWAY_ENVIRONMENT`
- `RAILWAY_BACKEND_SERVICE`
- `RAILWAY_FRONTEND_SERVICE`
- `RAILWAY_CHROMA_SERVICE`
- `RAILWAY_POSTGRES_SERVICE`
- `BACKEND_SECRET_KEY`

## Optional but recommended GitHub secrets

- `BACKEND_ALGORITHM`
  - Defaults to `HS256`.
- `CHROMA_COLLECTION_NAME`
  - Defaults to `rag_documents`.
- `FRONTEND_VITE_API_URL`
  - If set, the frontend uses this exact API base URL instead of the backend service's Railway public domain reference.
- `MOCK_PROVIDER_RESPONSES`
  - Defaults to `false`.

## LLM provider secrets

Set at least one of these unless you intentionally deploy with `MOCK_PROVIDER_RESPONSES=true`:

- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `DEEPSEEK_API_KEY`

## First bootstrap run

On the first deployment:

1. Open the `Deploy Railway` workflow in GitHub Actions.
2. Run it from `main`.
3. Set `create_missing_services` to `yes`.
4. Make sure the managed Railway Postgres service already exists and that `RAILWAY_POSTGRES_SERVICE` matches its exact service name.

That bootstrap run will:

- create empty Railway services for the repo-backed apps if they are missing
- attach a persistent volume to Chroma if Chroma was created on that run
- deploy Chroma from `chroma/Dockerfile`
- deploy the backend from `backend/Dockerfile`
- generate a Railway public domain for the backend if the backend service was created on that run and you did not provide `FRONTEND_VITE_API_URL`
- deploy the frontend from `frontend/Dockerfile`

## Safety differences from the earlier version

- It uses `RAILWAY_API_TOKEN`, which Railway documents for account/workspace-level actions like service configuration and management.
- It does not auto-create managed Postgres anymore. That was the least deterministic part of the old flow.
- It deploys with attached Railway logs instead of `railway up --ci`, then verifies the latest deployment reaches `SUCCESS`.
- It only creates a backend public domain automatically when the backend service was created on that run.

## Important note about the backend domain

If `FRONTEND_VITE_API_URL` is not provided, the workflow uses the backend service's Railway public domain reference so the frontend can bake `VITE_API_URL` at build time.

That works, but it is not the long-term privacy ideal. A better future setup would move toward a more private/internal API topology or a frontend proxy strategy so the frontend build does not depend on a public backend hostname.

## Recommended next hardening step

Configure Railway healthchecks for the long-running services.

This workflow now waits for each deployment to reach `SUCCESS`, which is much better than stopping at build completion. But Railway documents that healthchecks are what make deployment readiness stricter during the deploy phase. Without healthchecks, a service can be marked successful after the container starts even if the app is not fully ready yet.
