"""Pydantic models for HeySol API client and memory management."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HeySolConfig(BaseModel):
    """Configuration for HeySol client."""

    api_key: str | None = Field(default=None, description="HeySol API key")
    base_url: str | None = Field(default=None, description="HeySol API base URL")
    mcp_url: str | None = Field(default=None, description="MCP server URL")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


class MemoryMetadata(BaseModel):
    """Metadata associated with memory episodes."""

    class Config:
        """Allow extra fields in metadata."""

        extra = "allow"


class MemoryEpisodeData(BaseModel):
    """Data structure for memory episodes."""

    id: str | None = Field(default=None, description="Episode unique identifier")
    body: str = Field(description="Memory content text")
    space_id: str | None = Field(default=None, description="Associated space ID")
    session_id: str | None = Field(default=None, description="Session identifier")
    source: str | None = Field(default=None, description="Source of the memory")
    metadata: MemoryMetadata = Field(
        default_factory=MemoryMetadata, description="Additional metadata"
    )
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")

    class Config:
        """Allow extra fields from API responses."""

        extra = "allow"


class MemorySearchResultData(BaseModel):
    """Search results for memory queries."""

    episodes: list[MemoryEpisodeData] = Field(
        default_factory=list, description="Matching episodes"
    )
    total: int = Field(default=0, description="Total number of results")
    query: str | None = Field(default=None, description="Original search query")
    execution_time_ms: float | None = Field(
        default=None, description="Query execution time"
    )

    class Config:
        """Allow extra fields from API responses."""

        extra = "allow"


class MemorySpaceData(BaseModel):
    """Data structure for memory spaces."""

    id: str = Field(description="Space unique identifier")
    name: str = Field(description="Space display name")
    description: str | None = Field(default=None, description="Space description")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional space metadata"
    )

    class Config:
        """Allow extra fields from API responses."""

        extra = "allow"


class HeySolClientConfig(BaseModel):
    """Complete configuration for HeySol client."""

    api_key: str | None = Field(default=None)
    base_url: str | None = Field(default=None)
    mcp_url: str | None = Field(default=None)
    config: HeySolConfig | None = Field(default=None)
    prefer_mcp: bool = Field(default=False, description="Prefer MCP over API")
    skip_mcp_init: bool = Field(default=False, description="Skip MCP initialization")


# Exception models for better error handling
class HeySolError(Exception):
    """Base exception for HeySol errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(HeySolError):
    """Authentication related errors."""

    pass


class ValidationError(HeySolError):
    """Validation related errors."""

    pass


class ConnectionError(HeySolError):
    """Connection related errors."""

    pass


class RateLimitError(HeySolError):
    """Rate limiting errors."""

    pass


# Type aliases for backward compatibility
MemoryEpisode = MemoryEpisodeData
MemorySearchResult = MemorySearchResultData
MemorySpace = MemorySpaceData
