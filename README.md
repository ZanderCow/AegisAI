# AegisAI

## Running the Application

This project uses `docker-compose` to manage both the development environment and the end-to-end (E2E) testing environment. All docker-compose files are located in the `infra` directory.

### Development Environment

The development environment runs the **PostgreSQL database**, the **FastAPI backend**, and the **Vite + React frontend**. It spins up all exactly what you need to run the app natively on your host machine without running the test suite.

To start the development environment in the background, run:

```bash
docker-compose -f infra/docker-compose.dev.yml up -d
```

Once running:
- Frontend is accessible at: `http://localhost:5173`
- Backend API is accessible at: `http://localhost:8000`
- Database is running on port: `5432`

To stop the development environment, run:

```bash
docker-compose -f infra/docker-compose.dev.yml down
```

---

### End-to-End (E2E) Testing Environment

The E2E environment runs everything from the development environment, but also spins up an additional **Playwright container**. The Playwright container waits for the frontend and backend to become available, then automatically executes the E2E test suite.

To start the E2E environment and watch the test output, run:

```bash
docker-compose -f infra/docker-compose.e2e.yml up --build --abort-on-container-exit
```

Using `--abort-on-container-exit` ensures that the entire stack stops and cleans up automatically once the e2e test runner container finishes executing the tests.

To stop and remove the containers manually, run:

```bash
docker-compose -f infra/docker-compose.e2e.yml down
```
