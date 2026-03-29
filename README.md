# AegisAI

## Running the Application

This project uses Docker Compose to manage both the development
environment and the end-to-end (E2E) testing environment. All compose
files are located in the `infra` directory.

### Development Environment

The development environment runs the **PostgreSQL database**, a
dedicated **Chroma** vector store, the **FastAPI backend**, and the
**Vite + React frontend**.

To start the development environment in the background, run:

```bash
docker compose -f infra/docker-compose.dev.yml up -d
```

For provider-backed chat in the dev stack, set `GROQ_API_KEY`,
`GEMINI_API_KEY`, and `DEEPSEEK_API_KEY` in `infra/.env` or export them
in your shell before starting Compose.

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

### End-to-End (E2E) Testing Environment

The E2E environment runs the same application stack, including Chroma,
plus an additional **Playwright container**. The Playwright container
waits for the frontend and backend to become available, then
automatically executes the E2E test suite.

To start the E2E environment and watch the test output, run:

```bash
docker compose -f infra/docker-compose.e2e.yml up --build --abort-on-container-exit
```

For provider-backed RAG E2E tests, export at least one of
`GROQ_API_KEY`, `GEMINI_API_KEY`, or `DEEPSEEK_API_KEY` before starting
Compose. You can optionally set `E2E_PROVIDER` and `E2E_MODEL` to force
the Playwright RAG test to use a specific provider and model when more
than one key is available.

Using `--abort-on-container-exit` ensures that the entire stack stops and cleans up automatically once the e2e test runner container finishes executing the tests.

To stop and remove the containers manually, run:

```bash
docker compose -f infra/docker-compose.e2e.yml down
```
