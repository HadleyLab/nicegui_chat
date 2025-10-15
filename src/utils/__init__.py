"""Utility Functions for MammoChat™.

This module provides shared utility functions used across the MammoChat™ application.
These utilities handle common tasks like static file serving,
promoting code reuse and consistency throughout the modular architecture.

All utilities follow the application's coding standards: minimalism, explicitness,
and performance optimization.
"""


def setup_static_files(app) -> None:
    """Configure static file serving for the application.

    Sets up NiceGUI static file serving for branding assets.
    This enables the web application to load icons and stylesheets.

    Args:
        app: NiceGUI application instance to configure routes on
    """
    # NiceGUI handles static files automatically
    # This function is kept for compatibility but simplified
    pass
