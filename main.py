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

from nicegui import app, ui

from src.ai_service import AIService
from src.config import config, validate_config
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.ui.main_ui import setup_ui
from src.utils import get_logger, setup_static_files

logger = get_logger()

try:
    validate_config(config)
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print("Please create a .env file with your DEEPSEEK_API_KEY")
    exit(1)

ai_service = AIService()
auth_service = AuthService(config.memory)
memory_service = MemoryService(auth_service)
chat_service = ChatService(auth_service, memory_service, config)
setup_static_files(app)


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
    logger.info("starting_application", host=config.host, port=config.port)
    ui.run(
        title="MammoChat",
        host=config.host,
        port=config.port,
        reload=True,
        show=False,
        reconnect_timeout=30.0,  # Increase reconnect timeout
    )
