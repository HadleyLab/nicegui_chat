"""High level wrappers around HeySol memory operations."""

from __future__ import annotations

from collections.abc import Iterable

from ..models.memory import MemoryEpisode, MemorySearchResult, MemorySpace
from ..utils.exceptions import AuthenticationError, ChatServiceError
from .auth_service import AuthService


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

        space_list = list(space_ids) if space_ids else None

        try:
            result = self._auth_service.client.search(
                query,
                space_list,
                limit,
                include_invalidated,
            )
            # Convert result to dict for from_api method
            try:
                # Handle different possible result types
                if isinstance(result, dict):
                    result_dict = result
                elif hasattr(result, "__dict__"):
                    result_dict = result.__dict__
                else:
                    # Try to convert to dict, fallback to empty result on failure
                    try:
                        result_dict = dict(result)
                    except (TypeError, ValueError):
                        result_dict = {"episodes": [], "total": 0}
            except Exception:
                # Handle unexpected response format - fallback for non-convertible types
                result_dict = {"episodes": [], "total": 0}

            # Type annotation to help mypy understand the result type
            result_dict = dict(result_dict)

            return MemorySearchResult.from_api(result_dict)
        except Exception as exc:
            raise ChatServiceError(f"Memory search failed: {exc}") from exc

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
            payload = self._auth_service.client.ingest(
                message,
                space_id,
                session_id,
                source,
            )

            episode_id = str(payload.get("episode_id") or payload.get("id") or "")
            return MemoryEpisode(episode_id=episode_id, body=message, space_id=space_id)
        except Exception as exc:
            raise ChatServiceError(f"Memory add failed: {exc}") from exc

    async def list_spaces(self) -> list[MemorySpace]:
        """List all available memory spaces."""
        if not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication required for memory operations")

        try:
            payload = self._auth_service.client.get_spaces()
            return [MemorySpace.from_dict(item) for item in payload]
        except Exception as exc:
            raise ChatServiceError(f"Failed to list memory spaces: {exc}") from exc
