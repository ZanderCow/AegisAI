# Backend API

This is a FastAPI-based backend application with built-in JWT authentication,
SQLAlchemy integration, and a Chroma-backed RAG document store.

## Prerequisites
- Python 3.10+
- PostgreSQL (or SQLite for local development)

## Setup Instructions

We use [uv](https://github.com/astral-sh/uv), the blazing-fast Python package manager, to handle dependencies and environments.

1. **Install uv** (if you don't have it already)
   - **macOS / Linux**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - **Windows**:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```


2. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd backend
   ```

3. **Install Dependencies**
   ```bash
   # This will automatically create a virtual environment (.venv) 
   # and install both application and development dependencies in < 2 seconds.
   uv sync --dev
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory (alongside `src/`):
   ```
   DATABASE_URL="postgresql+asyncpg://user:password@localhost/dbname"
   SECRET_KEY="your-super-secret-key"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ENVIRONMENT="development"  # Set to "production" to enable logging
   MOCK_PROVIDER_RESPONSES=false
   CHROMA_HOST="localhost"
   CHROMA_PORT=8001
   CHROMA_SSL=false
   CHROMA_COLLECTION_NAME="rag_documents"
   ```

## Chroma Configuration

The backend now connects to Chroma over HTTP instead of using embedded local
storage. For local host-based development, point `CHROMA_HOST` and
`CHROMA_PORT` at your running Chroma server. For Docker Compose development,
the compose files use the same `CHROMA_*` variables and set them to the
internal `chroma` service by default.

To point the same backend code at a hosted Chroma deployment later, only
change the connection variables. For example:

```env
CHROMA_HOST="your-chroma-hostname"
CHROMA_PORT=443
CHROMA_SSL=true
CHROMA_COLLECTION_NAME="rag_documents"
```

`CHROMA_PATH` is no longer the primary runtime configuration for the backend.

## Running the Application

To start the FastAPI development server using `uv`:
```bash
uv run uvicorn src.main:app --reload
```
The API documentation will be available at `http://127.0.0.1:8000/docs`.

If you want the RAG endpoints to work while running the backend directly on
your host, make sure a Chroma server is reachable at the `CHROMA_*` endpoint
you configured above.

For direct local runs, the backend still supports the development fallback of
creating tables on startup when `AUTO_CREATE_TABLES=true`. Compose-managed
environments now run Alembic first and override `AUTO_CREATE_TABLES=false` so
schema changes do not happen inside the API process.

## Database Setup

The database schema is managed via `db/schema.sql`. When starting the development environment with Docker Compose, the database will automatically initialize from this file if the volume is mounted correctly.

To manually initialize or reset the database:
1. Connect to your PostgreSQL instance.
2. Run the contents of `db/schema.sql`.

Deterministic admin and security accounts can be created using the provided bootstrap scripts in `infra/dev/`.

## Schema-Only Handoff

The default teammate/deploy handoff is `schema only`, not a transfer of live
application rows.

Typical flow on another machine:

1. Provision an empty PostgreSQL database.
2. Configure `DATABASE_URL` and the other required environment variables.
3. Run `uv run alembic upgrade head`.
4. Optionally run an explicit bootstrap step for deterministic admin/security accounts if that environment needs them.
5. Start the backend.

This keeps schema history separate from bootstrap data. For dev and E2E flows,
the fixed privileged accounts remain one-off bootstrap jobs, while ordinary
test users are still created dynamically through the signup API.

## Running Tests

To run the local `pytest` suite, simply use `uv run`.
Because of our `pyproject.toml` configuration, `uv` automatically sets the
correct `PYTHONPATH` and loads test environment variables from `.env.example`.

```bash
uv run pytest
```

To run the backend and frontend test suites together in Docker Compose, run the
following command from the repository root:

```bash
./scripts/test-compose.sh
```
