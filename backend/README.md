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
