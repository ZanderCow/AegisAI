# ──────────────────────────────────────────────────────────────
# AegisAI – FastAPI Backend
# Python 3.12 slim image running uvicorn.
# ──────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
