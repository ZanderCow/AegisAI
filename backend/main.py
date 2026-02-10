from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.db import init_db
from src.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database
    await init_db()
    yield
    # Shutdown: Clean up resources if needed (not strictly required for Beanie)

from src.api.v1.api import api_router

app = FastAPI()

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to AegisAI Backend", "database": "Connected"}
