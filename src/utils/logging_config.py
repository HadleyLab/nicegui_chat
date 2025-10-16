"""Logging configuration for the application.

This module provides centralized logging configuration using structlog.
"""

import structlog


def get_logger(name: str = "nicegui_chat") -> structlog.WriteLogger:
    """Get a structured logger instance.

    Args:
        name: Name of the logger, typically the module name

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)