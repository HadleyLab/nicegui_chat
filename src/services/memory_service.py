"""High level wrappers around HeySol memory operations."""

from __future__ import annotations

from collections.abc import Iterable

import structlog

from ..models.memory import MemoryEpisode, MemorySearchResult, MemorySpace
from ..utils.exceptions import AuthenticationError, ChatServiceError
from .auth_service import AuthService


class MemoryService:
    """Service for managing HeySol memory operations."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service
        self._logger = structlog.get_logger()

    async def search(
        self,
        query: str,
        *,
        space_ids: Iterable[str] | None = None,
        limit: int = 10,
        include_invalidated: bool = False,
    ) -> MemorySearchResult:
        """Search memory for relevant episodes."""
        self._logger.debug(
            "memory_search_start",
            query=query,
            space_ids=list(space_ids) if space_ids else None,
            limit=limit,
        )
        if not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication required for memory search")

        space_list = list(space_ids) if space_ids else None

        try:
            from heysol import HeySolClient

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
            self._logger.debug(
                "memory_search_success",
                query=query,
                result_count=(
                    len(result.get("episodes", [])) if isinstance(result, dict) else 0
                ),
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
        self._logger.debug(
            "memory_add_start", message=message[:50], space_id=space_id, source=source
        )
        if not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication required for memory operations")

        try:
            from heysol import HeySolClient

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
            self._logger.debug(
                "memory_add_success",
                episode_id=str(payload.get("episode_id") or payload.get("id") or ""),
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
            from heysol import HeySolClient

            client = HeySolClient(
                api_key=self._auth_service.api_key,
                base_url=self._auth_service.base_url,
            )
            payload = client.get_spaces()
            return [MemorySpace.from_dict(item) for item in payload]
        except Exception as exc:
            raise ChatServiceError(f"Failed to list memory spaces: {exc}") from exc
