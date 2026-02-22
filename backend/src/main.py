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

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.core.config import settings
from src.core.db import connect_db, disconnect_db
from src.core.logger import configure_logging, get_logger
from src.api.v1.api import api_router

configure_logging(settings)
auth_logger = get_logger("auth")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(
    title=settings.app_name,
    description="AegisAI REST API",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/v1/auth"):
        errors = exc.errors()
        for error in errors:
            loc = ".".join([str(l) for l in error.get("loc", [])])
            msg = error.get("msg", "Unknown error")
            auth_logger.warning(f"[AUTH][VALIDATION] Validation failed: field '{loc}' - {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


if settings.allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

if settings.enforce_https:
    app.add_middleware(HTTPSRedirectMiddleware)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")
