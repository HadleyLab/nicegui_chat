"""Main application entry point for MammoChat."""

import sys

from nicegui import app, ui

# Set Python path explicitly for src imports
sys.path.insert(0, '/app')

from src.__version__ import __version__
from src.config import load_app_config
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.ui.chat_ui import ChatUI


def main() -> None:
    """Main application entry point."""
    # Load configuration
    config = load_app_config()

    # Add static files for branding
    app.add_static_files("/branding", "branding")

    # Initialize services
    auth_service = AuthService(config.heysol)
    memory_service = MemoryService(auth_service)
    chat_service = ChatService(auth_service, memory_service, config)

    # Alert user if HeySol API key is not configured
    if not auth_service.is_authenticated:
        print("Warning: HeySol API key not configured. Memory features will be disabled.")

    # Build UI
    @ui.page("/")
    def index() -> None:
        """Main page."""
        chat_ui = ChatUI(config, auth_service, chat_service, memory_service)
        chat_ui.build()

    # Run the application with verbose output
    print(f"Starting MammoChat v{__version__}")
    print(f"Configuration loaded: {config.app.name}")
    print(f"Host: {config.app.host}")
    print(f"Port: {config.app.port}")
    print(f"Reload: {config.app.reload}")
    print("Dark mode: True")
    print(f"Authentication status: {'Valid' if auth_service.is_authenticated else 'Missing API key'}")

    # Set environment variables for verbose logging
    import os
    os.environ['NICEGUI_LOG_LEVEL'] = 'DEBUG'
    os.environ['NICEGUI_VERBOSE'] = 'true'

    print("Environment variables set for verbose logging")
    print("Starting NiceGUI server...")

    ui.run(
        title=f"{config.app.name} v{__version__}",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        dark=True,
        favicon="💗",
        show=True,  # Show the UI in browser
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
