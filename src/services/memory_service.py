"""High level wrappers around HeySol memory operations."""

from __future__ import annotations

from collections.abc import Iterable

from ..models.memory import MemoryEpisode, MemorySearchResult, MemorySpace
from ..utils.exceptions import AuthenticationError
from .auth_service import AuthService

try:
    from heysol import HeySolClient  # type: ignore
except ImportError:
    HeySolClient = None


class MemoryService:
    """Service for managing HeySol memory operations."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service

    async def search(
        self,
        query: str,
        *,
        space_ids: Iterable[str] | None = None,
        limit: int = 10,
        include_invalidated: bool = False,
    ) -> MemorySearchResult:
        """Search memory for relevant episodes."""
        if not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication required for memory search")

        try:
            if HeySolClient is None:
                raise ImportError("HeySolClient not available")

            space_list = list(space_ids) if space_ids else None
            client = HeySolClient(
                api_key=self._auth_service.api_key,
                base_url=self._auth_service.base_url,
            )
            result = client.search(
                query,
                space_list,
                limit,
                include_invalidated,
            )

            # Convert result to dict for from_api method
            if isinstance(result, dict):
                result_dict = result
            elif hasattr(result, "__dict__"):
                result_dict = result.__dict__  # type: ignore
            else:
                result_dict = dict(result)  # type: ignore

            return MemorySearchResult.from_api(result_dict)
        except ImportError:
            # Return empty result if heysol is not available
            return MemorySearchResult(episodes=[], total=0)

    async def add(
        self,
        message: str,
        *,
        space_id: str | None = None,
        session_id: str | None = None,
        source: str | None = None,
    ) -> MemoryEpisode:
        """Add a new memory episode."""
        if not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication required for memory operations")

        try:
            if HeySolClient is None:
                raise ImportError("HeySolClient not available")

            client = HeySolClient(
                api_key=self._auth_service.api_key,
                base_url=self._auth_service.base_url,
            )
            payload = client.ingest(
                message,
                space_id,
                session_id,
                source,
            )

            episode_id = str(payload.get("episode_id") or payload.get("id") or "")
            return MemoryEpisode(episode_id=episode_id, body=message, space_id=space_id)
        except ImportError:
            # Return a dummy episode if heysol is not available
            return MemoryEpisode(episode_id="dummy", body=message, space_id=space_id)

    async def list_spaces(self) -> list[MemorySpace]:
        """List all available memory spaces."""
        if not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication required for memory operations")

        try:
            if HeySolClient is None:
                raise ImportError("HeySolClient not available")

            client = HeySolClient(
                api_key=self._auth_service.api_key,
                base_url=self._auth_service.base_url,
            )
            payload = client.get_spaces()
            return [MemorySpace.from_dict(item) for item in payload]
        except ImportError:
            # Return empty list if heysol is not available
            return []
