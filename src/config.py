"""Configuration for MammoChat."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def _load_text(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def load_theme() -> dict[str, Any]:
    """Load theme configuration from config/theme.json."""
    return _load_json(CONFIG_DIR / "theme.json")


def load_app_config() -> dict[str, Any]:
    """Load application configuration from app.json."""
    return _load_json(CONFIG_DIR / "app.json")


def load_system_prompt() -> str:
    """Load system prompt from markdown file."""
    return _load_text(CONFIG_DIR / "system.md")


# Load configuration resources once at module level
THEME = load_theme()
APP_CONFIG = load_app_config()
SYSTEM_PROMPT = load_system_prompt()


@dataclass
class Config:
    """Application configuration."""

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
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", APP_CONFIG["llm"]["base_url"])

    # HeySol Memory Service
    heysol_api_key: str = os.getenv("HEYSOL_API_KEY", "")
    heysol_base_url: str = os.getenv("HEYSOL_BASE_URL", APP_CONFIG["memory"]["base_url"])

    # Theme convenience
    palette: dict[str, str] = field(default_factory=lambda: THEME["palette"].copy())
    status_colors: dict[str, str] = field(default_factory=lambda: THEME["status"].copy())
    shadows: dict[str, str] = field(default_factory=lambda: THEME["shadows"].copy())
    layout: dict[str, str] = field(default_factory=lambda: THEME["layout"].copy())

    # Direct color access for convenience
    primary: str = field(init=False)
    primary_dark: str = field(init=False)
    secondary: str = field(init=False)
    accent: str = field(init=False)
    background: str = field(init=False)
    surface: str = field(init=False)
    text: str = field(init=False)
    text_secondary: str = field(init=False)
    border: str = field(init=False)
    mint: str = field(init=False)
    success: str = field(init=False)
    slate_gray: str = field(init=False)
    lavender: str = field(init=False)
    peach: str = field(init=False)

    # System Prompt
    system_prompt: str = SYSTEM_PROMPT

    def __post_init__(self) -> None:
        """Set theme after initialization."""
        object.__setattr__(self, "theme", {
            "palette": self.palette,
            "status": self.status_colors,
            "shadows": self.shadows,
            "layout": self.layout,
        })
        
        # Set direct color access
        object.__setattr__(self, "primary", self.palette["primary"])
        object.__setattr__(self, "primary_dark", self.palette["primary_dark"])
        object.__setattr__(self, "secondary", self.palette["secondary"])
        object.__setattr__(self, "accent", self.palette["accent"])
        object.__setattr__(self, "background", self.palette["background"])
        object.__setattr__(self, "surface", self.palette["surface"])
        object.__setattr__(self, "text", self.palette["text"])
        object.__setattr__(self, "text_secondary", self.palette["text_muted"])
        object.__setattr__(self, "border", "#E2E8F0")  # Light gray border
        object.__setattr__(self, "mint", self.palette["accent"])  # Use accent as mint
        object.__setattr__(self, "success", self.status_colors["positive"])
        object.__setattr__(self, "slate_gray", self.palette["secondary"])
        object.__setattr__(self, "lavender", self.palette["lavender"])
        object.__setattr__(self, "peach", self.palette["peach"])

    def validate(self) -> None:
        """Validate required configuration."""
        if not self.deepseek_api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is required. Please set it in your .env file."
            )


config = Config()
