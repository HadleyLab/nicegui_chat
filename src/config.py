"""Configuration management for the NiceGUI Chat application."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
import json

from .utils.exceptions import ConfigurationError

# Load environment variables from .env file
load_dotenv()

CONFIG_PATH_ENV = "APP_CONFIG_PATH"
DEFAULT_CONFIG_PATH = Path("config/app_config.json")


@dataclass(frozen=True)
class PromptStore:
    """Lazy loader for prompt files stored on disk."""

    root: Path
    _cache: Dict[str, str] = field(default_factory=dict, init=False)

    def read(self, name: str) -> str:
        path = self.root / f"{name}.md"
        if not path.exists():
            raise ConfigurationError(f"Prompt '{name}' not found at {path}")
        cache = object.__getattribute__(self, "_cache")
        if name not in cache:
            cache[name] = path.read_text(encoding="utf-8").strip()
        return cache[name]

    def optional(self, name: str, default: str = "") -> str:
        try:
            return self.read(name)
        except ConfigurationError:
            return default


@dataclass(frozen=True)
class ChatConfig:
    """Runtime configuration for chat orchestration behaviour."""

    enable_memory_enrichment: bool
    store_user_messages: bool
    stream_chunk_size: int
    max_history_display: int

    @classmethod
    def from_payload(cls, payload: Dict[str, object]) -> "ChatConfig":
        try:
            return cls(
                enable_memory_enrichment=bool(payload.get("enable_memory_enrichment", True)),
                store_user_messages=bool(payload.get("store_user_messages", True)),
                stream_chunk_size=int(payload.get("stream_chunk_size", 50)),  # type: ignore
                max_history_display=int(payload.get("max_history_display", 50)),  # type: ignore
            )
        except (KeyError, ValueError) as exc:
            raise ConfigurationError(f"Chat configuration error: {exc}") from exc


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str
    model: str
    base_url: str
    system_prompt: str

    def ensure_valid(self) -> None:
        if not self.api_key:
            raise ConfigurationError(
                "DEEPSEEK_API_KEY environment variable is required to run the chat agent"
            )
        if not self.system_prompt:
            raise ConfigurationError("System prompt could not be loaded from configuration")


@dataclass(frozen=True)
class HeysolConfig:
    api_key: Optional[str]
    base_url: str


@dataclass(frozen=True)
class UIConfig:
    """UI theme and styling configuration."""

    theme: str
    primary_color: str
    background_color: str
    surface_color: str
    text_color: str
    accent_color: str
    border_radius: str
    animation_duration: str
    tagline: str
    logo_full_path: str
    logo_icon_path: str
    welcome_title: str
    welcome_message: str
    input_placeholder: str
    thinking_text: str
    send_tooltip: str
    dark_mode_tooltip: str
    new_conversation_tooltip: str
    logout_tooltip: str
    new_conversation_notification: str
    logout_notification: str
    response_complete_notification: str

    @classmethod
    def from_payload(cls, payload: Dict[str, object]) -> "UIConfig":
        return cls(
            theme=str(payload.get("theme", "dark")),
            primary_color=str(payload.get("primary_color", "#6366f1")),
            background_color=str(payload.get("background_color", "#0f172a")),
            surface_color=str(payload.get("surface_color", "#1e293b")),
            text_color=str(payload.get("text_color", "#e2e8f0")),
            accent_color=str(payload.get("accent_color", "#818cf8")),
            border_radius=str(payload.get("border_radius", "12px")),
            animation_duration=str(payload.get("animation_duration", "0.3s")),
            tagline=str(payload.get("tagline", "Your journey, together")),
            logo_full_path=str(payload.get("logo_full_path", "/branding/logo-full-color.svg")),
            logo_icon_path=str(payload.get("logo_icon_path", "/branding/logo-icon.svg")),
            welcome_title=str(payload.get("welcome_title", "Welcome to MammoChat")),
            welcome_message=str(payload.get("welcome_message", "")),
            input_placeholder=str(payload.get("input_placeholder", "Type your message...")),
            thinking_text=str(payload.get("thinking_text", "Thinking...")),
            send_tooltip=str(payload.get("send_tooltip", "Send Message")),
            dark_mode_tooltip=str(payload.get("dark_mode_tooltip", "Toggle Dark Mode")),
            new_conversation_tooltip=str(payload.get("new_conversation_tooltip", "New Conversation")),
            logout_tooltip=str(payload.get("logout_tooltip", "Logout")),
            new_conversation_notification=str(payload.get("new_conversation_notification", "Started new conversation")),
            logout_notification=str(payload.get("logout_notification", "Logged out successfully")),
            response_complete_notification=str(payload.get("response_complete_notification", "Response complete")),
        )


@dataclass(frozen=True)
class AppMetadata:
    """Application metadata."""

    name: str
    host: str
    port: int
    reload: bool

    @classmethod
    def from_payload(cls, payload: Dict[str, object]) -> "AppMetadata":
        return cls(
            name=str(payload.get("name", "NiceGUI Chat")),
            host=str(payload.get("host", "0.0.0.0")),
            port=int(payload.get("port", 8080)),  # type: ignore
            reload=bool(payload.get("reload", False)),
        )


@dataclass(frozen=True)
class AppConfig:
    app: AppMetadata
    chat: ChatConfig
    llm: DeepSeekConfig
    heysol: HeysolConfig
    prompts: PromptStore
    ui: UIConfig


def load_app_config() -> AppConfig:
    """Load application configuration from JSON file and environment variables."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = Path(os.getenv(CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    if not config_path.is_absolute():
        config_path = project_root / config_path
    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file not found at {config_path}. Set {CONFIG_PATH_ENV}."
        )

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigurationError(f"Failed to read config {config_path}: {exc}") from exc

    # Load prompts
    try:
        prompts_section = payload["prompts"]
    except KeyError as exc:
        raise ConfigurationError("Config missing 'prompts' section") from exc

    prompt_root = Path(prompts_section.get("root", "prompts"))
    if not prompt_root.is_absolute():
        prompt_root = project_root / prompt_root
    prompt_store = PromptStore(prompt_root)
    system_prompt_name = prompts_section.get("system", "system")
    system_prompt = prompt_store.read(system_prompt_name)

    # Load LLM config
    try:
        llm_section = payload["llm"]
    except KeyError as exc:
        raise ConfigurationError("Config missing 'llm' section") from exc
    
    # API key from environment variable only (secrets should not be in JSON)
    llm_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    
    llm_model = llm_section.get("model", "deepseek-chat")
    llm_base = llm_section.get("base_url", "https://api.deepseek.com")
    llm = DeepSeekConfig(
        api_key=llm_api_key,
        model=llm_model,
        base_url=llm_base,
        system_prompt=system_prompt,
    )

    # Load HeySol config
    try:
        heysol_section = payload["heysol"]
    except KeyError as exc:
        raise ConfigurationError("Config missing 'heysol' section") from exc
    
    # API key from environment variable only (secrets should not be in JSON)
    heysol_api_key = os.getenv("HEYSOL_API_KEY", "").strip() or None
    
    heysol_base = heysol_section.get("base_url", "https://core.heysol.ai/api/v1")
    heysol = HeysolConfig(api_key=heysol_api_key, base_url=heysol_base)

    # Load chat config
    try:
        chat_section = payload["chat"]
    except KeyError as exc:
        raise ConfigurationError("Config missing 'chat' section") from exc
    chat = ChatConfig.from_payload(chat_section)

    # Load app metadata (all from JSON, no environment overrides)
    app_meta = payload.get("app", {})
    app = AppMetadata.from_payload(app_meta)

    # Load UI config
    ui_section = payload.get("ui", {})
    ui = UIConfig.from_payload(ui_section)

    return AppConfig(
        app=app,
        chat=chat,
        llm=llm,
        heysol=heysol,
        prompts=prompt_store,
        ui=ui,
    )
