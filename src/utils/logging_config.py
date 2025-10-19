"""Logging configuration for the application.

This module provides centralized logging configuration using structlog for structured logging
with minimal overhead and explicit behavior. Follows coding standards for fail-fast debugging
and essential-only logging.
"""

import logging
import sys

import structlog


def configure_logging(production: bool = False) -> None:
    """Configure structlog with colored console output and production-ready settings.

    Args:
        production: Enable production mode (JSON output, no colors)
    """
    # Configure standard library logging first
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            stream=sys.stdout
        )

    # Disable standard library logging to avoid duplication
    logging.getLogger().handlers.clear()

    # Configure structlog processors
    if production:
        # Production: JSON output, no colors, minimal overhead
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Colored console output, readable format
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True)
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance.

    Args:
        name: Name of the logger, typically the module name

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)
