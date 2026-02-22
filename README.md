# AegisAI

## Workspace Rules
- If you want to work on the front end, you gotta go to `frontend/aegisai`.
- If you want to work on the back end, you gotta go to `backend`.
- If you want to work on end-to-end tests, you gotta go to `e2e`.
- If you want to work on the database, you gotta go to `db`.

## Quick Navigation
```bash
cd frontend/aegisai   # frontend work
cd backend            # backend work
cd e2e                # selenium e2e tests
cd db                 # database assets
```

## Run Full End Services (Docker)
From the project root, this command starts everything in order (database, backend, frontend, selenium, e2e tests):

```bash
docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e-tests
```

Stop and clean up:

```bash
docker compose -f docker-compose.e2e.yml down --volumes --remove-orphans
```

## CI/CD
CI workflow:
- `.github/workflows/ci.yml`

Deploy workflow (Railway boilerplate):
- `.github/workflows/deploy.yml`

Additional docs:
- `docs/ci-cd.md`
- `e2e/README.md`

### What CI runs
- Backend unit tests
- Backend integration tests
- Frontend lint + build
- Docker Compose Selenium auth end-to-end tests

### Deployment note
Railway deployment is intentionally boilerplate and disabled until credentials/variables are provided.
