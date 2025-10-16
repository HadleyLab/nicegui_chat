"""Logging configuration for the application.

This module provides centralized logging configuration using structlog.
"""

import structlog  # type: ignore


def get_logger(name: str = "nicegui_chat") -> structlog.WriteLogger:  # type: ignore
    """Get a structured logger instance.

    Args:
        name: Name of the logger, typically the module name

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)  # type: ignore
