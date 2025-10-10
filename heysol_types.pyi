"""Type stubs for HeySol API client."""

from typing_extensions import TypeAlias

# Type definitions for API responses
MemoryMetadata: TypeAlias = dict[str, str | int | float | bool | None]
MemoryEpisodeData: TypeAlias = dict[
    str, str | int | float | bool | None | list[str] | MemoryMetadata
]
MemorySearchResultData: TypeAlias = dict[
    str, str | int | float | bool | None | list[MemoryEpisodeData]
]
MemorySpaceData: TypeAlias = dict[str, str | int | float | bool | None]

class HeySolClient:
    """Unified HeySol client with both API and MCP support."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        mcp_url: str | None = None,
        config: HeySolConfig | None = None,
        prefer_mcp: bool = False,
        skip_mcp_init: bool = False,
    ) -> None: ...
    def search(
        self,
        query: str,
        space_ids: list[str] | None = None,
        limit: int = 10,
        include_invalidated: bool = False,
    ) -> MemorySearchResultData: ...
    def ingest(
        self,
        message: str,
        space_id: str | None = None,
        session_id: str | None = None,
        source: str | None = None,
    ) -> MemoryEpisodeData: ...
    def get_spaces(self) -> list[MemorySpaceData]: ...

class HeySolConfig:
    """Configuration for HeySol client."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        mcp_url: str | None = None,
    ) -> None: ...

class HeySolError(Exception):
    """Base exception for HeySol errors."""

class AuthenticationError(HeySolError):
    """Authentication related errors."""

class ValidationError(HeySolError):
    """Validation related errors."""

class ConnectionError(HeySolError):
    """Connection related errors."""

class RateLimitError(HeySolError):
    """Rate limiting errors."""

# Type aliases for common return types
MemoryEpisode = MemoryEpisodeData
MemorySearchResult = MemorySearchResultData
MemorySpace = MemorySpaceData
