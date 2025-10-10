"""Simple MCP server authentication."""

from __future__ import annotations

from config import HeysolConfig


class AuthService:
    """Simple MCP authentication service."""

    def __init__(self, config: HeysolConfig) -> None:
        self.api_key = config.api_key
        self.base_url = config.base_url

    @property
    def is_authenticated(self) -> bool:
        """Check if API key is available."""
        return bool(self.api_key)
