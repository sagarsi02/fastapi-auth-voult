"""Centralized logging configuration."""

from __future__ import annotations

import logging

from src.config import settings


def _resolve_log_level() -> int:
    """Resolve log level from env with sane defaults."""
    if settings.LOG_LEVEL:
        return logging._nameToLevel.get(settings.LOG_LEVEL.upper(), logging.DEBUG)
    return logging.DEBUG


def setup_logging() -> None:
    """Configure root logging only once."""
    level = _resolve_log_level()
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given name."""
    setup_logging()
    return logging.getLogger(name)
