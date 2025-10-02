"""Memory domain models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryEpisode(BaseModel):
    """Memory episode model."""
    episode_id: str
    body: str
    space_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "MemoryEpisode":
        """Create a MemoryEpisode from API response."""
        return cls(
            episode_id=str(payload.get("episode_id") or payload.get("id", "")),
            body=str(payload.get("body") or payload.get("content", "")),
            space_id=payload.get("space_id"),
            session_id=payload.get("session_id"),
            created_at=payload.get("created_at"),
            metadata=payload.get("metadata", {}),
        )


class MemorySearchResult(BaseModel):
    """Memory search result model."""
    episodes: List[MemoryEpisode] = Field(default_factory=list)
    total: int = 0

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "MemorySearchResult":
        """Create a MemorySearchResult from API response."""
        episodes_data = payload.get("episodes", [])
        episodes = [MemoryEpisode.from_api(ep) for ep in episodes_data]
        return cls(
            episodes=episodes,
            total=payload.get("total", len(episodes)),
        )


class MemorySpace(BaseModel):
    """Memory space model."""
    space_id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "MemorySpace":
        """Create a MemorySpace from dictionary."""
        return cls(
            space_id=str(payload.get("space_id") or payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=payload.get("description"),
            created_at=payload.get("created_at"),
        )
