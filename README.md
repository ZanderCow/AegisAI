# AegisAI

## Running the Application

This project uses Docker Compose to manage both the development
environment and the end-to-end (E2E) testing environment. All compose
files are located in the `infra` directory.

### Development Environment

The development environment runs the **PostgreSQL database**, a
dedicated **Chroma** vector store, the **FastAPI backend**, and the
**Vite + React frontend**.

Before starting any Compose stack, create a local `infra/.env` file by
copying `infra/.env.example` and then add the development values for the
variables listed in that file. All Compose-level runtime values now
live in `infra/.env` instead of being hardcoded in the YAML files. The
backend/frontend settings there use the same variable names as
production, such as `DATABASE_URL`, `SECRET_KEY`, `ENVIRONMENT`,
`CHROMA_*`, and `VITE_API_URL`.

These environment variables are intended for local development and local
test flows. Production environment variables are routed through a
different production configuration path and should not be copied into
`infra/.env`.

To start the development environment in the background, run:

```bash
docker compose -f infra/docker-compose.dev.yml up -d
```

For provider-backed chat in the dev stack, set `GROQ_API_KEY`,
`GEMINI_API_KEY`, and `DEEPSEEK_API_KEY` in `infra/.env` or export them
in your shell before starting Compose. These AI model API key variables
should use development credentials only. If you need those values,
contact the repository owner to obtain the approved development API
keys. Do not reuse or copy production AI provider credentials into the
development environment.

Once running:
- Frontend is accessible at: `http://localhost:5173`
- Backend: `http://localhost:8000` — [`/docs`](http://localhost:8000/docs) (Swagger), [`/health`](http://localhost:8000/health), and JSON endpoints under `/api/v1` (e.g. `POST /api/v1/auth/signup`).
- Database is running on port: `5432`
- Chroma persists its vector data in the named Docker volume `chroma_data`

To stop the development environment, run:

```bash
docker compose -f infra/docker-compose.dev.yml down
```

To wipe persisted Chroma data as well, run:

```bash
docker compose -f infra/docker-compose.dev.yml down -v
```

---

### Unit and Integration Testing

To run the backend and frontend unit/integration test suites together from a
single command, use the test runner script:

```bash
./scripts/test-compose.sh
```

The script builds the test images, starts the test-only infrastructure, runs
both suites, and cleans up automatically. If you need to clean up the stack
manually afterward, run:

```bash
docker compose -f infra/docker-compose.test.yml down --volumes --remove-orphans
```

---

### End-to-End (E2E) Testing Environment

The E2E environment runs the same application stack, including Chroma,
plus an additional **Playwright container**. The Playwright container
waits for the frontend and backend to become available, then
automatically executes the E2E test suite.

To start the E2E environment and watch the test output, run:

```bash
docker compose -f infra/docker-compose.e2e.yml up --build --abort-on-container-exit
```

For provider-backed RAG E2E tests, set at least one of `GROQ_API_KEY`,
`GEMINI_API_KEY`, or `DEEPSEEK_API_KEY` in `infra/.env` or export them
before starting Compose. These should also be development-only API keys;
reach out to the repository owner if you need access to them. You can
optionally set `E2E_PROVIDER` and `E2E_MODEL` there as well to force the
Playwright RAG test to use a specific provider and model when more than
one key is available. Production AI credentials are routed separately
and should not be added to the local development env file.

Using `--abort-on-container-exit` ensures that the entire stack stops and cleans up automatically once the e2e test runner container finishes executing the tests.

To stop and remove the containers manually, run:

```bash
docker compose -f infra/docker-compose.e2e.yml down
```
