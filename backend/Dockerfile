# Stage 1: Base image
FROM python:3.11-slim AS base
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT="/usr/local"
# Set working directory
WORKDIR /app
# Copy dependency files
COPY pyproject.toml uv.lock ./

# Stage 2: Development environment
FROM base AS development
# Install all dependencies including dev dependencies
RUN uv sync --locked --all-extras
# Copy the rest of the application
COPY . .
# Expose the port
EXPOSE 8000
# Run uvicorn with hot-reload enabled
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production environment
FROM base AS production
# Install only production dependencies
ENV ENVIRONMENT=production
RUN uv sync --locked --no-dev
# Copy the rest of the application
COPY . .
# Expose the port
EXPOSE 8000
# Run uvicorn without hot-reload for maximum performance
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
