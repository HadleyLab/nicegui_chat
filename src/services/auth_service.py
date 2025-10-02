"""Authentication and HeySol client lifecycle management."""

from __future__ import annotations

import os
import sys

try:
    from heysol import HeySolClient
except ModuleNotFoundError as exc:
    client_path = os.getenv("HEYSOL_CLIENT_PATH")
    if client_path and client_path not in sys.path:
        sys.path.append(client_path)
        from heysol import HeySolClient
    else:
        raise exc

from ..config import HeysolConfig
from ..utils.exceptions import AuthenticationError


class AuthService:
    """Wraps the HeySol authentication workflow for use across the app."""

    def __init__(self, config: HeysolConfig) -> None:
        self._config = config
        self._client: HeySolClient | None = None
        self._api_key: str | None = config.api_key

        if self._api_key:
            try:
                self._client = HeySolClient(
                    api_key=self._api_key,
                    base_url=config.base_url,
                    prefer_mcp=False,
                    skip_mcp_init=False,
                )
            except Exception as exc:
                print(f"Warning: Failed to initialize HeySol client: {exc}")

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._client is not None and self._api_key is not None

    @property
    def client(self) -> HeySolClient:
        """Get the HeySol client."""
        if not self._client:
            raise AuthenticationError("User is not authenticated")
        return self._client

    async def authenticate(self, api_key: str) -> bool:
        """Authenticate with the provided API key."""
        try:
            self._client = HeySolClient(
                api_key=api_key,
                base_url=self._config.base_url,
                prefer_mcp=False,
                skip_mcp_init=False,
            )
            self._api_key = api_key
            return True
        except Exception as exc:
            print(f"Authentication failed: {exc}")
            return False

    def logout(self) -> None:
        """Logout and clear authentication."""
        self._client = None
        self._api_key = None

    def headers(self) -> dict[str, str]:
        """Get authentication headers."""
        if not self._api_key:
            raise AuthenticationError("User is not authenticated")
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
