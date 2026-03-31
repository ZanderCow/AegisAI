---
name: run test
description: Run the full Docker Compose validation flow for this repo: smoke-check the dev stack, run backend/frontend unit and integration tests, run the E2E suite, tear each stack down, and report the findings clearly.
---

# Run Test

Use this skill when the user asks to run tests, validate the app end to end, or confirm that the Docker Compose stacks still work.

Always run from the repository root. Use `docker compose`, not `docker-compose`.

## Repo-Specific Compose Files

- Dev smoke check: `infra/docker-compose.dev.yml`
- Backend/frontend unit and integration tests: `infra/docker-compose.test.yml`
- End-to-end tests: `infra/docker-compose.e2e.yml`

## Ground Rules

- Treat this as a three-stage workflow: dev startup, test stack, then E2E.
- Tear each stack down before moving to the next one, even if a step fails.
- Prefer `down -v --remove-orphans` for `test` and `e2e` cleanup. For `dev`, use plain `down` unless the user explicitly asks to remove volumes.
- Do not claim success based on partial logs. A stage passes only if its validation checks succeed and the relevant command exits with code `0`.
- If a stage fails because Docker, dependencies, ports, or API keys are misconfigured, report that as an environment or infrastructure failure, not as an application regression.

## Step 1: Dev Stack Smoke Check

Bring the app up, confirm it is reachable, then tear it down.

```bash
docker compose -f infra/docker-compose.dev.yml up --build -d
```

Validate:

- Run `docker compose -f infra/docker-compose.dev.yml ps` and make sure the services are up.
- Wait for the backend health endpoint to respond at `http://localhost:8000/health`.
- Confirm the frontend responds at `http://localhost:5173`.

Example portable wait loops:

```bash
for i in $(seq 1 60); do curl -fsS http://localhost:8000/health >/dev/null && break; sleep 2; done
for i in $(seq 1 60); do curl -fsS http://localhost:5173 >/dev/null && break; sleep 2; done
```

If validation fails, capture:

```bash
docker compose -f infra/docker-compose.dev.yml ps
docker compose -f infra/docker-compose.dev.yml logs --no-color
```

Always tear it down before continuing:

```bash
docker compose -f infra/docker-compose.dev.yml down
```

## Step 2: Backend + Frontend Test Stack

Run the compose file that executes backend `pytest` and frontend `vitest`.

```bash
docker compose -f infra/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from frontend-test
```

Important repo detail:

- `backend-test` runs `uv run pytest tests/`
- `frontend-test` waits for `backend-test` to finish, then runs `npm run test -- --run`
- The overall exit code should be taken from `frontend-test`

After the run, inspect logs before cleanup if you need more detail:

```bash
docker compose -f infra/docker-compose.test.yml logs --no-color backend-test frontend-test
docker compose -f infra/docker-compose.test.yml ps
```

Your analysis should explicitly state:

- Whether backend tests passed
- Whether frontend tests passed
- Any failing test names, assertion messages, or stack traces that matter
- Whether the failure happened before tests actually started

Always tear the stack down:

```bash
docker compose -f infra/docker-compose.test.yml down -v --remove-orphans
```

## Step 3: E2E Stack

Run the full E2E environment and use the Playwright container's exit code as the result.

```bash
docker compose -f infra/docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e
```

If you need more detail before cleanup:

```bash
docker compose -f infra/docker-compose.e2e.yml logs --no-color e2e backend frontend
docker compose -f infra/docker-compose.e2e.yml ps
```

Notes:

- The `e2e` service runs `npx playwright test`
- Some provider-backed flows may require `GROQ_API_KEY`, `GEMINI_API_KEY`, or `DEEPSEEK_API_KEY`
- If E2E fails because required provider configuration is missing, say so clearly

Always tear the stack down:

```bash
docker compose -f infra/docker-compose.e2e.yml down -v --remove-orphans
```

## Final Report Format

Report the results in this order:

1. Dev smoke check
2. Backend/frontend unit and integration tests
3. E2E tests
4. Cleanup confirmation

For each stage, include:

- `Passed`, `Failed`, or `Blocked`
- The command you ran
- The key evidence: health checks, exit code, service status, or important failing test output
- A short explanation of what the result means

If everything passed, say that all three stages completed successfully and that all Docker Compose stacks were torn down cleanly.

If anything failed, keep the report actionable:

- Name the failing stage
- Name the failing service or test when available
- Quote or summarize the most useful error
- Distinguish test failures from setup failures
