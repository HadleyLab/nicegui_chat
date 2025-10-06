"""Main application entry point for the MammoChat SPA."""

from __future__ import annotations

import os
import sys

from nicegui import app, ui

# Ensure src imports resolve in production containers
sys.path.insert(0, "/app")

from src.__version__ import __version__
from src.config import load_app_config
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.ui.chat_ui import ChatUI


def main() -> None:
    """Run the MammoChat single-page application."""
    config = load_app_config()

    # Expose brand assets
    app.add_static_files("/branding", "branding")

    # Core services
    auth_service = AuthService(config.heysol)
    memory_service = MemoryService(auth_service)
    chat_service = ChatService(auth_service, memory_service, config)

    if not auth_service.is_authenticated:
        print("Warning: HeySol API key not configured. Memory features will be disabled.")

    def render_chat() -> None:
        """Render the branded chat page."""
        ChatUI(config, auth_service, chat_service, memory_service).build()

    def root() -> None:
        """Configure the NiceGUI 3.0 single-page shell."""
        ui.colors(
            primary=config.ui.primary_color,
            secondary=config.ui.accent_color,
            accent=config.ui.accent_color,
            background=config.ui.background_color,
            text=config.ui.text_color,
        )

        ui.link.default_classes(
            "text-inherit no-underline hover:text-primary-600 transition-colors"
        )

        ui.query("body").classes(
            "bg-rose-50 text-slate-800 antialiased min-h-screen"
        )

        ui.sub_pages({
            "/": render_chat,
        })

    os.environ.setdefault("NICEGUI_LOG_LEVEL", "DEBUG")
    os.environ.setdefault("NICEGUI_VERBOSE", "true")

    print(f"Starting MammoChat v{__version__}")
    print(f"Configuration loaded: {config.app.name}")
    print(f"Host: {config.app.host}")
    print(f"Port: {config.app.port}")
    print(f"Reload: {config.app.reload}")
    print(
        f"Authentication status: {'Valid' if auth_service.is_authenticated else 'Missing API key'}"
    )

    favicon_path = os.path.join("branding", os.path.basename(config.ui.logo_icon_path))

    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("NICEGUI_TEST_MODE"):
        return

    ui.run(
        root=root,
        title=f"{config.app.name} v{__version__}",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        favicon=favicon_path,
        show=True,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
