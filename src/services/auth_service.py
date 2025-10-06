"""Authentication helpers for HeySol-backed services."""

from __future__ import annotations

from typing import Any

from ..config import HeysolConfig
from ..utils.exceptions import AuthenticationError

try:  # pragma: no cover - handled in tests via patching
    from heysol import HeySolClient  # type: ignore
except Exception:  # pragma: no cover - graceful degradation when SDK missing
    HeySolClient = None  # type: ignore[assignment]


class AuthService:
    """Manage HeySol authentication lifecycle."""

    def __init__(self, config: HeysolConfig) -> None:
        self._base_url = config.base_url
        self._api_key: str | None = config.api_key
        self._client: Any | None = None

        if self._api_key:
            self._client = self._initialize_client(self._api_key)

    @property
    def api_key(self) -> str | None:
        """Return the current API key (may be None)."""
        return self._api_key

    @property
    def base_url(self) -> str:
        """Return the configured HeySol base URL."""
        return self._base_url

    @property
    def is_authenticated(self) -> bool:
        """Whether a valid HeySol client is available."""
        return self._client is not None and bool(self._api_key)

    @property
    def client(self) -> Any:
        """Return the authenticated HeySol client or raise."""
        if not self.is_authenticated or not self._client:
            raise AuthenticationError("Authentication service is not authenticated")
        return self._client

    def headers(self) -> dict[str, str]:
        """Produce authorization headers for HeySol API calls."""
        if not self.is_authenticated or not self._api_key:
            raise AuthenticationError("Service is not authenticated; cannot build headers")
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def authenticate(
        self,
        api_key: str,
        *,
        prefer_mcp: bool = False,
        skip_mcp_init: bool = False,
    ) -> bool:
        """Attempt to authenticate with the provided API key."""
        try:
            client = self._create_client(
                api_key,
                prefer_mcp=prefer_mcp,
                skip_mcp_init=skip_mcp_init,
            )
        except Exception as exc:  # pragma: no cover - exercised in tests
            print(f"Authentication failed: {exc}")
            return False

        if client is None:
            print("Authentication failed: HeySol client is unavailable")
            return False

        self._client = client
        self._api_key = api_key
        return True

    def logout(self) -> None:
        """Clear authentication state."""
        self._client = None
        self._api_key = None

    def _initialize_client(self, api_key: str) -> Any | None:
        """Initialize the client during construction."""
        try:
            return self._create_client(api_key)
        except Exception as exc:  # pragma: no cover - exercised in tests
            print(f"Failed to initialize HeySol client: {exc}")
            return None

    def _create_client(
        self,
        api_key: str,
        *,
        prefer_mcp: bool = False,
        skip_mcp_init: bool = False,
    ) -> Any | None:
        """Construct a HeySol client instance."""
        if HeySolClient is None:
            return None

        return HeySolClient(  # type: ignore[call-arg]
            api_key=api_key,
            base_url=self._base_url,
            prefer_mcp=prefer_mcp,
            skip_mcp_init=skip_mcp_init,
        )
