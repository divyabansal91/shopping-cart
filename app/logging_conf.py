"""Logging setup: console + rotating file."""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging() -> None:
    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return  # already configured
    # force=True replaces handlers that libraries (e.g. mcp) may have added on import
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                os.getenv("LOG_FILE", "app.log"), maxBytes=1_000_000, backupCount=3
            ),
        ],
        force=True,
    )
