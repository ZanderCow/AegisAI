---
name: check-tests
description: Use this skill when the user explicitly asks for the check-tests skill or wants a focused check of relevant project tests.
---

# Check Tests

Use this skill when the user asks to check tests for a specific change or feature.

Always run from the repository root. Use `docker compose`, not `docker-compose`.

## Repo-Specific Compose Files

- Dev smoke check: `infra/docker-compose.dev.yml`
- Backend/frontend unit and integration tests: `./scripts/test-compose.sh` using `infra/docker-compose.test.yml`
- End-to-end tests: `infra/docker-compose.e2e.yml`

## Ground Rules

- Treat this as a three-stage workflow: dev startup, test stack, then E2E.
- Tear each stack down before moving to the next one, even if a step fails.
- Prefer `down -v --remove-orphans` for `test` and `e2e` cleanup. For `dev`, use plain `down` unless the user explicitly asks to remove volumes.
- Do not claim success based on partial logs. A stage passes only if its validation checks succeed and the relevant command exits with code `0`.
- If a stage fails because Docker, dependencies, ports, or API keys are misconfigured, report that as an environment or infrastructure failure, not as an application regression.
- Call out skipped coverage separately from failures. In this repo, parts of the E2E suite can skip when provider keys are unavailable.

## Step 1: Dev Stack Smoke Check

Bring the app up, confirm it is reachable, then tear it down.

```bash
docker compose -f infra/docker-compose.dev.yml up --build -d
```

Validate:

- Run `docker compose -f infra/docker-compose.dev.yml ps` and inspect service state carefully:
  - `db`, `chroma`, `backend`, and `frontend` should be running
  - `add-admin-user-to-db` is a one-shot bootstrap helper and may exit `0`; treat that as expected, not as a failure
- Wait for the backend health endpoint to respond at `http://localhost:8000/health`.
- Confirm the frontend responds at `http://localhost:5173`.

If validation fails, capture:

```bash
docker compose -f infra/docker-compose.dev.yml ps
docker compose -f infra/docker-compose.dev.yml logs --no-color
```

Always tear it down before continuing:

```bash
docker compose -f infra/docker-compose.dev.yml down
```

## Step 2: Backend + Frontend Unit/Integration Tests

Run the canonical repository test runner from the repository root:

```bash
./scripts/test-compose.sh
```

Important repo detail:

- This script is the canonical local and CI entrypoint for backend/frontend unit and integration tests
- It builds the `backend-test` and `frontend-test` images, starts `db` and `chroma`, runs backend `pytest`, then runs frontend `vitest`
- The backend test command is `uv run pytest tests/`
- The frontend test command is `npm run test -- --run`
- The script prints a final summary with both exit codes and then cleans the stack up automatically with `docker compose -f infra/docker-compose.test.yml down --volumes --remove-orphans`
- If the script fails before either test suite starts, treat that as a Docker or environment failure rather than a test regression

If you need to preserve the full run output, capture the script output directly:

```bash
set -o pipefail
./scripts/test-compose.sh 2>&1 | tee compose-test-logs.txt
```

For focused troubleshooting after a failure, you may rerun the underlying test containers manually:

```bash
docker compose -f infra/docker-compose.test.yml build backend-test frontend-test
docker compose -f infra/docker-compose.test.yml up -d db chroma
docker compose -f infra/docker-compose.test.yml run --rm --no-deps backend-test
docker compose -f infra/docker-compose.test.yml run --rm --no-deps frontend-test
docker compose -f infra/docker-compose.test.yml down -v --remove-orphans
```

Your analysis should explicitly state:

- Whether backend tests passed
- Whether frontend tests passed
- Which exit code the script returned
- Any failing test names, assertion messages, or stack traces that matter
- Whether the failure happened during image build, infrastructure startup, backend tests, or frontend tests

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
- `login.spec.ts` and `signup.spec.ts` do not require provider keys
- `rag.spec.ts` skips when none of `GROQ_API_KEY`, `GEMINI_API_KEY`, or `DEEPSEEK_API_KEY` is set
- If `E2E_PROVIDER` is set without its matching API key, treat that as configuration failure
- If the suite passes with one or more skipped tests, report that clearly instead of calling it a clean full pass

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

- `Passed`, `Passed with skips`, `Failed`, or `Blocked`
- The command you ran
- The key evidence: health checks, exit code, service status, or important failing test output
- A short explanation of what the result means

If everything passed without skips, say that all three stages completed successfully and that all Docker Compose stacks were torn down cleanly.

If E2E passed with skips, say exactly which test file or scenario skipped and why.

If anything failed, keep the report actionable:

- Name the failing stage
- Name the failing service or test when available
- Quote or summarize the most useful error
- Distinguish test failures from setup failures

When relevant, note that GitHub Actions uses the same unit/integration command by running:

```bash
set -o pipefail
./scripts/test-compose.sh 2>&1 | tee compose-test-logs.txt
```
