# Backend API

This is a FastAPI-based backend application with built-in JWT authentication and SQLAlchemy database integration.

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
   ```

## Running the Application

To start the FastAPI development server using `uv`:
```bash
uv run uvicorn src.main:app --reload
```
The API documentation will be available at `http://127.0.0.1:8000/docs`.

## Running Tests

To run the `pytest` suite, simply use `uv run`. 
Because of our `pyproject.toml` configuration, `uv` automatically sets the correct `PYTHONPATH` and loads test environment variables from `.env.example`.

```bash
uv run pytest
```
