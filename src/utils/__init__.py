"""Utility Functions for MammoChat™.

This module provides shared utility functions used across the MammoChat™ application.
These utilities handle common tasks like static file serving,
promoting code reuse and consistency throughout the modular architecture.

All utilities follow the application's coding standards: minimalism, explicitness,
and performance optimization.
"""

from pathlib import Path

import structlog
from nicegui import app as nicegui_app


def get_logger(name: str = "mammochat") -> structlog.WriteLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def handle_error(error: Exception, logger: structlog.WriteLogger) -> None:
    """Handle and log an error, then re-raise it."""
    logger.error(f"An error occurred: {error} (type: {type(error).__name__})")
    raise error


def setup_static_files(app) -> None:
    """Configure static file serving for the application.

    Sets up NiceGUI static file serving for branding assets.
    This enables the web application to load icons and stylesheets.

    Args:
        app: NiceGUI application instance to configure routes on
    """
    # Mount branding directory
    branding_path = Path("branding")
    if branding_path.exists():
        from fastapi.staticfiles import StaticFiles
        nicegui_app.mount(
            "/branding", StaticFiles(directory="branding"), name="branding"
        )

    # Mount static directory for backward compatibility
    if branding_path.exists():
        from fastapi.staticfiles import StaticFiles
        nicegui_app.mount(
            "/static",
            StaticFiles(directory="branding"),
            name="static-branding",
        )
