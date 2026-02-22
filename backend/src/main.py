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
from fastapi.middleware.cors import CORSMiddleware

from api.v1.api import api_router
from core.config import settings
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

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")
