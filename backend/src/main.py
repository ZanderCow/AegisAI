"""
main.py
=======
Application entry point for the FastAPI backend.

Running Locally
---------------
.. code-block:: bash

    uvicorn src.main:app --reload
"""

from fastapi import FastAPI

from src.api.v1.api import api_router

app = FastAPI(
    title="AegisAI API",
    description="AegisAI REST API",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")
