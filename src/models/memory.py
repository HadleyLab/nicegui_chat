"""Memory domain models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MemoryEpisode(BaseModel):  # type: ignore[misc]
    """Memory episode model."""

    episode_id: str
    body: str
    space_id: str | None = None
    session_id: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> MemoryEpisode:
        """Create a MemoryEpisode from API response."""
        return cls(
            episode_id=str(payload.get("episode_id") or payload.get("id", "")),
            body=str(payload.get("body") or payload.get("content", "")),
            space_id=payload.get("space_id"),
            session_id=payload.get("session_id"),
            created_at=payload.get("created_at"),
            metadata=payload.get("metadata", {}),
        )


class MemorySearchResult(BaseModel):  # type: ignore[misc]
    """Memory search result model."""

    episodes: list[MemoryEpisode] = Field(default_factory=list)
    total: int = 0

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> MemorySearchResult:
        """Create a MemorySearchResult from API response."""
        episodes_data = payload.get("episodes", [])
        episodes = [MemoryEpisode.from_api(ep) for ep in episodes_data]
        return cls(
            episodes=episodes,
            total=payload.get("total", len(episodes)),
        )


class MemorySpace(BaseModel):  # type: ignore[misc]
    """Memory space model."""

    space_id: str
    name: str
    description: str | None = None
    created_at: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> MemorySpace:
        """Create a MemorySpace from dictionary."""
        return cls(
            space_id=str(payload.get("space_id") or payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=payload.get("description"),
            created_at=payload.get("created_at"),
        )
