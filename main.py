"""Main application entry point for MammoChat."""

from nicegui import app, ui

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

    # Check authentication
    if not auth_service.is_authenticated:
        ui.notify(
            "Warning: HeySol API key not configured. Memory features will be disabled.",
            type="warning",
            timeout=5000,
        )

    # Build UI
    @ui.page("/")
    def index() -> None:
        """Main page."""
        chat_ui = ChatUI(config, auth_service, chat_service, memory_service)
        chat_ui.build()

    # Run the application
    print(f"Starting MammoChat v{__version__}")
    ui.run(
        title=f"{config.app.name} v{__version__}",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        dark=True,
        favicon="💗",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
