# Railway GitHub Actions Deploy

This repository now ships with a manual Railway deployment workflow at `.github/workflows/deploy.yml`.

## What it does

- Runs only when manually triggered from GitHub Actions.
- Fails unless the selected ref is `main`.
- Deploys services in this order:
  - `chroma`
  - `backend`
  - `frontend`
- Can bootstrap missing Railway services only when you explicitly choose `create_missing_services = yes`.
- Fails fast when required secrets are missing.

## Required GitHub secrets

- `RAILWAY_TOKEN`
- `RAILWAY_PROJECT`
- `RAILWAY_ENVIRONMENT`
- `RAILWAY_BACKEND_SERVICE`
- `RAILWAY_FRONTEND_SERVICE`
- `RAILWAY_CHROMA_SERVICE`
- `BACKEND_SECRET_KEY`

## Optional but recommended GitHub secrets

- `RAILWAY_POSTGRES_SERVICE`
  - If omitted, the workflow assumes the managed Railway Postgres service is named `Postgres`.
- `BACKEND_ALGORITHM`
  - Defaults to `HS256`.
- `CHROMA_COLLECTION_NAME`
  - Defaults to `rag_documents`.
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

That bootstrap run will:

- create empty Railway services for the repo-backed apps if they are missing
- create a managed Railway Postgres service if it is missing
- deploy Chroma from `chroma/Dockerfile`
- deploy the backend from `backend/Dockerfile`
- generate a Railway public domain for the backend
- deploy the frontend from `frontend/Dockerfile`
- generate a Railway public domain for the frontend

## Important note about the backend domain

The workflow intentionally gives the backend a public Railway domain so the frontend can bake `VITE_API_URL` at build time.

That works, but it is not the long-term privacy ideal. A better future setup would move toward a more private/internal API topology or a frontend proxy strategy so the frontend build does not depend on a public backend hostname.
