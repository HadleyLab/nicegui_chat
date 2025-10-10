"""Utility Functions for MammoChat.

This module provides shared utility functions used across the MammoChat application.
These utilities handle common tasks like logging, static file serving, and error handling,
promoting code reuse and consistency throughout the modular architecture.

The utilities are organized to support the layered architecture:
- Logging utilities for structured application logging
- Static file serving for web assets and PWA resources
- Error handling for fail-fast behavior and debugging

All utilities follow the application's coding standards: minimalism, explicitness,
and performance optimization.
"""

import structlog
from fastapi.responses import FileResponse


def get_logger(name: str = __name__) -> structlog.BoundLoggerBase:
    """Get a configured structured logger instance.

    Creates and returns a structlog logger configured for the application.
    The logger provides structured logging with consistent formatting and
    supports the application's logging requirements across all modules.

    Args:
        name: Logger name, defaults to the current module name

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


def setup_static_files(app) -> None:
    """Configure static file serving and PWA routes for the application.

    Sets up FastAPI routes to serve branding assets and PWA manifest files.
    This enables the web application to load icons, stylesheets, and manifest
    for Progressive Web App functionality.

    Args:
        app: FastAPI application instance to configure routes on
    """
    app.add_static_files("/branding", "branding")
    # Also serve branding files at root level for compatibility
    app.add_static_files("/static", "branding")

    @app.get("/manifest.json")
    def manifest() -> FileResponse:
        return FileResponse(
            "public/manifest.json", media_type="application/manifest+json"
        )

    @app.get("/service_worker.js")
    def service_worker() -> FileResponse:
        return FileResponse("service_worker.js", media_type="application/javascript")

    @app.get("/apple-touch-icon.png")
    def apple_icon() -> FileResponse:
        return FileResponse("branding/apple-touch-icon.png", media_type="image/png")


def handle_error(error: Exception, logger: structlog.BoundLoggerBase) -> None:
    """Log an error with structured details and re-raise for fail-fast behavior.

    Implements the application's fail-fast error handling strategy by logging
    comprehensive error information and immediately re-raising the exception.
    This ensures errors are never silently ignored and debugging information
    is captured in structured logs.

    Args:
        error: The exception that occurred
        logger: Configured logger instance for error reporting

    Raises:
        Exception: Re-raises the original error after logging
    """
    logger.error("error_occurred", error=str(error), error_type=type(error).__name__)
    raise error
