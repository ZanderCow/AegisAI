"""
core/logger.py
==============

Centralized logging configuration for all environments.
"""

import json
import logging
from datetime import datetime, timezone
from logging.config import dictConfig

from src.core.config import Settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(settings: Settings) -> None:
    formatter_name = "json" if settings.json_logs_enabled else "plain"
    access_level = "INFO" if settings.should_log_uvicorn_access else "WARNING"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
                "json": {"()": "src.core.logger.JsonFormatter"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": formatter_name,
                }
            },
            "root": {"handlers": ["console"], "level": settings.effective_log_level},
            "loggers": {
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": access_level,
                    "propagate": False,
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Returns a domain-specific logger that hooks into the global configuration.
    Example: logger = get_logger("payment")
    """
    return logging.getLogger(f"aegisai.{name}")
