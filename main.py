#!/usr/bin/env python3
"""MammoChat Application Entry Point.

This module serves as the main entry point for the MammoChat application,
implementing a modular architecture with clear separation of concerns:

- Configuration management (src/config.py)
- Business logic services (src/services/)
- User interface components (src/ui/)
- Utility functions and exceptions (src/utils/)

The application follows a layered architecture where:
- main.py orchestrates initialization and startup
- Services handle business logic and external integrations
- UI components manage presentation and user interaction
- Configuration centralizes all settings and environment variables

This design enables maintainability, testability, and scalability.
"""

import os

from nicegui import app, ui

from config import config, validate_config
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.ui.main_ui import setup_ui

# Set up static file serving for branding assets
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback when __file__ is not defined (e.g., in certain container contexts)
    current_dir = os.getcwd()

branding_dir = os.path.join(current_dir, "branding")
if os.path.exists(branding_dir):
    app.add_static_files("/branding", branding_dir)

public_dir = os.path.join(current_dir, "public")
if os.path.exists(public_dir):
    app.add_static_files("/public", public_dir)

try:
    validate_config(config)
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print("Please create a .env file with your DEEPSEEK_API_KEY")
    exit(1)

auth_service = AuthService(config.memory)
memory_service = MemoryService(auth_service)
chat_service = ChatService(auth_service, memory_service, config)

# Network connectivity is tested during normal operation
# The httpx.ReadError you encountered is now handled gracefully with retry logic


@ui.page("/")
def main() -> None:
    """Main page handler for the MammoChat application.

    This function serves as the entry point for the web interface,
    delegating UI setup to the modular setup_ui function from the
    main_ui module. It maintains separation between routing and
    presentation logic.
    """
    setup_ui(chat_service)


# Run the application
if __name__ in {"__main__", "__mp_main__"}:
    print(f"Starting MammoChat on {config.host}:{config.port}")
    ui.run(
        title="MammoChat™ - Your journey, together",
        host=config.host,
        port=config.port,
        reload=False,
        show=True,
        reconnect_timeout=600.0,  # Increase to 10 minutes for very long AI responses
        favicon="💗",  # Heart emoji as favicon for MammoChat
        dark=False,  # Light theme for MammoChat
    )
