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

import sys
from pathlib import Path

from nicegui import app, ui
from fastapi import Request

from config import config, validate_config
from src.utils.logging_config import configure_logging, get_logger
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.services.health_service import HealthService
from src.ui.main_ui import setup_ui
from src.utils.rate_limiting import rate_limiting_config

# Configure logging first for minimal overhead and explicit behavior
configure_logging(production=False)  # Set to True in production
logger = get_logger("main")

# Set up static file serving for branding assets
try:
    current_dir = Path(__file__).parent.resolve()
except NameError:
    # Fallback when __file__ is not defined (e.g., in certain container contexts)
    current_dir = Path.cwd()

branding_dir = current_dir / "branding"
if branding_dir.exists():
    app.add_static_files("/branding", str(branding_dir))

public_dir = current_dir / "public"
if public_dir.exists():
    app.add_static_files("/public", str(public_dir))

# Initialize modular services
limiter = rate_limiting_config.get_limiter()
app.state.limiter = limiter

# Rate limiting is now handled in the endpoint directly

# Secure error handler - don't expose sensitive information
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Log the actual error for debugging with structured logging
    logger.error("Unhandled error occurred", error=str(exc), error_type=type(exc).__name__)

    # Return generic error message without exposing sensitive information
    return {"error": "Internal server error", "detail": "An unexpected error occurred"}, 500

try:
    validate_config(config)
except ValueError as e:
    logger.error("Configuration validation failed", error=str(e), error_type=type(e).__name__)
    logger.error("Application startup aborted due to configuration error")
    sys.exit(1)

auth_service = AuthService(config.memory)
memory_service = MemoryService(auth_service)
chat_service = ChatService(auth_service, memory_service, config)

# Initialize health service for monitoring
health_service = HealthService(auth_service, memory_service, chat_service)

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


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint for application monitoring.

    This endpoint provides comprehensive health monitoring for the MammoChat application,
    delegating the actual health checks to the modular HealthService.

    Returns:
        HTTP 200 with JSON response if all services are healthy
        HTTP 503 with JSON response if any service is unhealthy
    """
    # Check rate limit for health endpoint
    is_limited, _ = limiter.check_rate_limit(request, "health")
    if is_limited:
        return {"error": "Rate limit exceeded", "detail": "Too many requests"}, 429

    health_status, http_status = await health_service.perform_health_check()
    return health_status.__dict__, http_status


# Run the application
if __name__ in {"__main__", "__mp_main__"}:
    logger.info("Starting MammoChat application", host=config.host, port=config.port)
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
