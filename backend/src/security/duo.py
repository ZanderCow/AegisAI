"""Duo Universal Prompt client factory.

Provides a helper to instantiate a configured Duo client using the
application settings, and re-exports DuoException for caller use.
"""
from duo_universal.client import Client, DuoException  # noqa: F401
from src.core.config import settings


def get_duo_client() -> Client:
    """Return a Duo Universal Prompt client built from application settings."""
    return Client(
        client_id=settings.DUO_CLIENT_ID,
        client_secret=settings.DUO_CLIENT_SECRET,
        host=settings.DUO_API_HOST,
        redirect_uri=settings.DUO_REDIRECT_URI,
    )
