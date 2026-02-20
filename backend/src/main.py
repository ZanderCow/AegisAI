"""
main.py
=======
Application entry point for the FastAPI backend.

Running Locally
---------------
.. code-block:: bash

    uvicorn src.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.v1.api import api_router
from core.db import connect_db, disconnect_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(
    title="AegisAI API",
    description="AegisAI REST API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")
