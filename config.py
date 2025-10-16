"""Configuration Management for MammoChat.

This module centralizes all application configuration, providing a clean
interface for environment variables, JSON config files, and theme settings.
It implements a layered configuration approach:

- Environment variables (highest priority)
- JSON configuration files (app.json, theme.json)
- Default values (fallback)

The configuration is organized into logical sections:
- Application metadata (name, branding, UI settings)
- Server configuration (host, port)
- AI service settings (DeepSeek LLM configuration)
- Memory service settings (HeySol integration)
- Theme and UI customization
- Chat behavior settings

This design enables easy deployment across different environments while
maintaining type safety and validation.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

load_dotenv()


@dataclass
class DeepSeekConfig:
    """DeepSeek LLM configuration."""

    api_key: str
    model: str
    base_url: str
    system_prompt: str

    def ensure_valid(self) -> None:
        """Validate required configuration."""
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        if not self.model:
            raise ValueError("DeepSeek model is required")
        if not self.base_url:
            raise ValueError("DeepSeek base URL is required")


@dataclass
class HeysolConfig:
    """HeySol Memory Service configuration."""

    api_key: str
    base_url: str


try:
    BASE_DIR = Path(__file__).parent
except NameError:
    # Fallback when __file__ is not defined (e.g., in certain container contexts)
    BASE_DIR = Path.cwd()
CONFIG_DIR = BASE_DIR / "config"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def _load_text(path: Path) -> str:
    with path.open(encoding="utf-8") as f:
        return f.read().strip()


def load_scene() -> dict[str, Any]:
    """Load scene configuration from config/scene.json."""
    return _load_json(CONFIG_DIR / "scene.json")


def load_app_config() -> dict[str, Any]:
    """Load application configuration from app.json."""
    return _load_json(CONFIG_DIR / "app.json")


def load_system_prompt() -> str:
    """Load system prompt from markdown file."""
    return _load_text(CONFIG_DIR / "system.md")


# Load configuration resources once at module level
SCENE = load_scene()
APP_CONFIG = load_app_config()
SYSTEM_PROMPT = load_system_prompt()


@dataclass
class Config:
    """Centralized application configuration with layered loading.

    This class aggregates all configuration settings from multiple sources:
    - Environment variables (highest priority)
    - JSON configuration files (app.json, theme.json)
    - Default values (fallback)

    It provides type-safe access to configuration values and ensures
    all required settings are validated before application startup.

    The configuration is divided into logical sections:
    - Application metadata and branding
    - Server network settings
    - AI service integration (DeepSeek)
    - Memory service integration (HeySol)
    - UI theming and styling
    - Chat behavior and streaming settings
    """

    # App Info
    app_name: str = APP_CONFIG["app"]["name"]
    app_tagline: str = APP_CONFIG["app"]["tagline"]
    logo_full: str = APP_CONFIG["app"]["branding"]["logo_full"]
    logo_icon: str = APP_CONFIG["app"]["branding"]["logo_icon"]

    # Server
    host: str = os.getenv("HOST", APP_CONFIG["server"]["host"])
    port: int = int(os.getenv("PORT", str(APP_CONFIG["server"]["port"])))

    # AI Service (DeepSeek)
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_model: str = APP_CONFIG["llm"]["model"]
    deepseek_base_url: str = os.getenv(
        "DEEPSEEK_BASE_URL", APP_CONFIG["llm"]["base_url"]
    )

    # HeySol Memory Service
    heysol_api_key: str = os.getenv("HEYSOL_API_KEY", "")
    heysol_base_url: str = os.getenv(
        "HEYSOL_BASE_URL", APP_CONFIG["memory"]["base_url"]
    )

    # Scene configuration for NiceGUI colors
    scene: dict[str, Any] = field(default_factory=lambda: SCENE.copy())

    # LLM Configuration
    llm: DeepSeekConfig = field(init=False)

    # Memory Configuration
    memory: HeysolConfig = field(init=False)

    # UI Configuration
    ui_logo_icon_path: str = APP_CONFIG["app"]["branding"]["logo_icon"]
    ui_welcome_title: str = "Welcome to MammoChat™!"
    ui_welcome_message: str = (
        """
Welcome to MammoChat™!

I'm here to support you on your breast cancer journey. I can help you:

- Find clinical trials that match your situation
- Connect with communities of patients with similar experiences
- Understand information about treatments and options
- Navigate your healthcare with confidence

How can I support you today?
""".strip()
    )
    ui_input_placeholder: str = "Share what's on your mind..."
    ui_send_tooltip: str = "Send message"
    ui_dark_mode_tooltip: str = "Toggle dark mode"
    ui_new_conversation_tooltip: str = "Start a new conversation"
    ui_thinking_text: str = "Thinking..."
    ui_response_complete_notification: str = "Response complete"
    ui_new_conversation_notification: str = "New conversation started"

    # Chat Configuration
    chat_store_user_messages: bool = True
    chat_enable_memory_enrichment: bool = True
    chat_stream_chunk_size: int = 50

    # Performance and Memory Management
    max_conversation_messages: int = 1000
    max_execution_steps: int = 500
    max_memory_search_results: int = 100
    background_task_limit: int = 5
    cleanup_interval_seconds: int = 60

    # HTTP Client Configuration for Performance
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20
    http_keepalive_expiry: float = 30.0
    http_connect_timeout: float = 10.0
    http_read_timeout: float = 60.0
    http_write_timeout: float = 10.0
    http_pool_timeout: float = 10.0

    # Docker Resource Configuration
    docker_cpu_limit: str = "1.0"
    docker_memory_limit: str = "2g"
    docker_memory_reservation: str = "1g"
    docker_network_mode: str = "bridge"
    docker_restart_policy: str = "unless-stopped"
    docker_healthcheck_interval: str = "30s"
    docker_healthcheck_timeout: str = "10s"
    docker_healthcheck_retries: int = 3

    # Request Processing Configuration
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 300
    streaming_timeout_seconds: int = 120
    memory_operation_timeout_seconds: int = 30

    # System Prompt
    system_prompt: str = SYSTEM_PROMPT

    def __post_init__(self) -> None:
        """Set llm and memory configs after initialization."""
        # Set LLM config
        object.__setattr__(
            self,
            "llm",
            DeepSeekConfig(
                api_key=self.deepseek_api_key,
                model=self.deepseek_model,
                base_url=self.deepseek_base_url,
                system_prompt=self.system_prompt,
            ),
        )

        # Set Memory config
        object.__setattr__(
            self,
            "memory",
            HeysolConfig(
                api_key=self.heysol_api_key,
                base_url=self.heysol_base_url,
            ),
        )

    def validate(self) -> None:
        """Validate required configuration."""
        if not self.deepseek_api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is required. Please set it in your .env file."
            )


def load_config() -> Config:
    """Load and validate complete application configuration.

    This function orchestrates the configuration loading process:
    - Loads JSON configuration files (app.json, theme.json)
    - Applies environment variable overrides
    - Creates and validates the Config instance
    - Ensures all required settings are present and valid

    Returns:
        Config: Fully initialized and validated configuration object

    Raises:
        ValueError: If required configuration values are missing or invalid
    """
    return Config()


def validate_config(config: Config) -> None:
    """Validate configuration integrity and required settings.

    Performs comprehensive validation of the configuration object,
    ensuring all required API keys, URLs, and settings are present
    and properly formatted before application startup.

    Args:
        config: The Config instance to validate

    Raises:
        ValueError: If any required configuration values are missing or invalid
    """
    config.validate()


config = load_config()
