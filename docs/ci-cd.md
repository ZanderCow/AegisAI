# CI/CD Boilerplate

## CI
Workflow: `.github/workflows/ci.yml`

Triggers:
- Pull requests into `main`
- Pushes to `main`

Jobs:
- Backend unit tests (`pytest tests/unit`)
- Backend integration tests (`pytest tests/integration`) with PostgreSQL service
- Frontend lint/build checks
- Docker Compose full-stack Selenium auth E2E checks (`docker-compose.e2e.yml`)

## Deployment (Railway)
Workflow: `.github/workflows/deploy.yml`

Trigger:
- Automatically after `CI` succeeds on `main` (and manual dispatch)

Safety default:
- Deployment is disabled until repository variable `ENABLE_RAILWAY_DEPLOY=true`

Required GitHub credentials (add later):
- Secret: `RAILWAY_TOKEN`
- Variable: `RAILWAY_SERVICE`
- Variable: `RAILWAY_ENVIRONMENT`

Required Railway production variables (set in Railway dashboard):
- `ENVIRONMENT=production`
- `DATABASE_URL`
- `SECRET_KEY` (strong random value)
- `ALLOWED_HOSTS` (no `*`)
- `CORS_ORIGINS` (no `*`)
- `UVICORN_WORKERS`
