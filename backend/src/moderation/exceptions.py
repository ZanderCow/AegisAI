"""Custom exceptions for the moderation layer."""


class ContentPolicyError(Exception):
    """Raised by a provider when its built-in content filter blocks a request."""
