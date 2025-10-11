"""Memory domain models with performance optimizations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryEpisode(BaseModel):
    """Memory episode model with performance optimizations."""

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=False,
        populate_by_name=True,
        # Optimize for memory efficiency
        str_strip_whitespace=True,
    )

    episode_id: str = Field(description="Unique episode identifier")
    body: str = Field(description="Episode content text")
    space_id: str | None = Field(default=None, description="Associated space ID")
    session_id: str | None = Field(default=None, description="Associated session ID")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Episode metadata"
    )

    def __hash__(self) -> int:
        """Optimized hash for episode deduplication."""
        return hash(
            (self.episode_id, self.body[:100])
        )  # Hash first 100 chars for performance

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> MemoryEpisode:
        """Create a MemoryEpisode from API response with validation."""
        return cls(
            episode_id=str(payload.get("episode_id") or payload.get("id", "")),
            body=str(payload.get("body") or payload.get("content", "")),
            space_id=payload.get("space_id"),
            session_id=payload.get("session_id"),
            created_at=payload.get("created_at"),
            metadata=payload.get("metadata", {}),
        )


class MemorySearchResult(BaseModel):
    """Memory search result model with performance optimizations."""

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=False,
        populate_by_name=True,
    )

    episodes: list[MemoryEpisode] = Field(
        default_factory=list, description="Search result episodes"
    )
    total: int = Field(default=0, description="Total number of results")

    # Performance optimization: limit maximum episodes per result
    max_episodes: int = Field(default=100, description="Maximum episodes to retain")

    def __post_init__(self) -> None:
        """Enforce episode limits after initialization."""
        if len(self.episodes) > self.max_episodes:
            self.episodes = self.episodes[: self.max_episodes]

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> MemorySearchResult:
        """Create a MemorySearchResult from API response with limits."""
        episodes_data = payload.get("episodes", [])
        episodes = [MemoryEpisode.from_api(ep) for ep in episodes_data]
        return cls(
            episodes=episodes,
            total=payload.get("total", len(episodes)),
        )


class MemorySpace(BaseModel):
    """Memory space model with performance optimizations."""

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=False,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    space_id: str = Field(description="Unique space identifier")
    name: str = Field(description="Space name")
    description: str | None = Field(default=None, description="Space description")
    created_at: str | None = Field(default=None, description="Creation timestamp")

    def __hash__(self) -> int:
        """Optimized hash for space deduplication."""
        return hash((self.space_id, self.name))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> MemorySpace:
        """Create a MemorySpace from dictionary with validation."""
        return cls(
            space_id=str(payload.get("space_id") or payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=payload.get("description"),
            created_at=payload.get("created_at"),
        )
