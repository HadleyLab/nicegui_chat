"""Unit tests for MemoryService."""

from unittest.mock import MagicMock, patch

import pytest

from src.models.memory import MemoryEpisode, MemorySearchResult, MemorySpace
from src.services.memory_service import MemoryService
from src.utils.exceptions import AuthenticationError


class TestMemoryService:
    """Test MemoryService."""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock auth service."""
        auth = MagicMock()
        auth.is_authenticated = True
        auth.api_key = "test_key"
        auth.base_url = "https://api.example.com"
        return auth

    @pytest.fixture
    def memory_service(self, mock_auth_service):
        """Create MemoryService instance."""
        return MemoryService(mock_auth_service)

    @pytest.mark.asyncio
    async def test_search_success(self, memory_service):
        """Test successful memory search."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            result = await memory_service.search("test query")
            assert result is not None
            assert isinstance(result, MemorySearchResult)
            assert result.episodes == []
            assert result.total == 0

    @pytest.mark.asyncio
    async def test_search_with_episodes(self, memory_service):
        """Test search returning episodes."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {
                "episodes": [
                    {"episode_id": "1", "body": "test content", "space_id": "space1"}
                ],
                "total": 1,
            }
            mock_client_class.return_value = mock_client

            result = await memory_service.search("test query")
            assert len(result.episodes) == 1
            assert result.episodes[0].episode_id == "1"
            assert result.episodes[0].body == "test content"
            assert result.total == 1

    @pytest.mark.asyncio
    async def test_search_with_space_ids(self, memory_service):
        """Test search with specific space IDs."""
        space_ids = ["space1", "space2"]
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            await memory_service.search("test query", space_ids=space_ids)
            mock_client.search.assert_called_once_with(
                "test query", space_ids, 10, False
            )

    @pytest.mark.asyncio
    async def test_search_with_custom_limit(self, memory_service):
        """Test search with custom limit."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            await memory_service.search("test query", limit=5)
            mock_client.search.assert_called_once_with("test query", None, 5, False)

    @pytest.mark.asyncio
    async def test_search_with_include_invalidated(self, memory_service):
        """Test search with include invalidated flag."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            await memory_service.search("test query", include_invalidated=True)
            mock_client.search.assert_called_once_with("test query", None, 10, True)

    @pytest.mark.asyncio
    async def test_search_not_authenticated(self, memory_service, mock_auth_service):
        """Test search when not authenticated."""
        mock_auth_service.is_authenticated = False

        with pytest.raises(AuthenticationError):
            await memory_service.search("test")

    @pytest.mark.asyncio
    async def test_search_import_error_fallback(self, memory_service):
        """Test search fallback when HeySolClient import fails."""
        with patch("heysol.HeySolClient", side_effect=ImportError):
            result = await memory_service.search("test query")
            assert isinstance(result, MemorySearchResult)
            assert result.episodes == []
            assert result.total == 0

    @pytest.mark.asyncio
    async def test_search_result_conversion_dict(self, memory_service):
        """Test search result conversion from dict."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 5}
            mock_client_class.return_value = mock_client

            result = await memory_service.search("test")
            assert result.total == 5

    @pytest.mark.asyncio
    async def test_search_result_conversion_object(self, memory_service):
        """Test search result conversion from object with __dict__."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()

            # Create a simple object with __dict__
            class MockResult:
                def __init__(self):
                    self.episodes = []
                    self.total = 3

            mock_result = MockResult()
            mock_client.search.return_value = mock_result
            mock_client_class.return_value = mock_client

            result = await memory_service.search("test")
            assert result.total == 3

    @pytest.mark.asyncio
    async def test_search_result_conversion_iterable(self, memory_service):
        """Test search result conversion from other iterable."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = [("key", "value")]
            mock_client_class.return_value = mock_client

            result = await memory_service.search("test")
            # Should not crash, though result may be empty
            assert isinstance(result, MemorySearchResult)

    @pytest.mark.asyncio
    async def test_add_success(self, memory_service):
        """Test successful memory add."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"episode_id": "123"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("test message")
            assert result.episode_id == "123"
            assert result.body == "test message"
            assert isinstance(result, MemoryEpisode)

    @pytest.mark.asyncio
    async def test_add_with_space_id(self, memory_service):
        """Test add with space ID."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"episode_id": "456"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("test message", space_id="space1")
            assert result.space_id == "space1"
            mock_client.ingest.assert_called_once_with(
                "test message", "space1", None, None
            )

    @pytest.mark.asyncio
    async def test_add_with_session_id(self, memory_service):
        """Test add with session ID."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"id": "789"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("test message", session_id="session1")
            assert result.episode_id == "789"
            mock_client.ingest.assert_called_once_with(
                "test message", None, "session1", None
            )

    @pytest.mark.asyncio
    async def test_add_with_source(self, memory_service):
        """Test add with source."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"episode_id": "101"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("test message", source="test_source")
            assert result.episode_id == "101"
            mock_client.ingest.assert_called_once_with(
                "test message", None, None, "test_source"
            )

    @pytest.mark.asyncio
    async def test_add_not_authenticated(self, memory_service, mock_auth_service):
        """Test add when not authenticated."""
        mock_auth_service.is_authenticated = False

        with pytest.raises(AuthenticationError):
            await memory_service.add("test message")

    @pytest.mark.asyncio
    async def test_add_import_error_fallback(self, memory_service):
        """Test add fallback when HeySolClient import fails."""
        with patch("heysol.HeySolClient", side_effect=ImportError):
            result = await memory_service.add("test message")
            assert isinstance(result, MemoryEpisode)
            assert result.episode_id == "dummy"
            assert result.body == "test message"

    @pytest.mark.asyncio
    async def test_add_payload_with_id_field(self, memory_service):
        """Test add when payload uses 'id' instead of 'episode_id'."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"id": "999"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("test message")
            assert result.episode_id == "999"

    @pytest.mark.asyncio
    async def test_add_payload_empty(self, memory_service):
        """Test add when payload is empty."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("test message")
            assert result.episode_id == ""

    @pytest.mark.asyncio
    async def test_list_spaces_success(self, memory_service):
        """Test successful list spaces."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_spaces.return_value = [
                {"id": "1", "name": "Test Space", "description": "A test space"}
            ]
            mock_client_class.return_value = mock_client

            result = await memory_service.list_spaces()
            assert len(result) == 1
            assert isinstance(result[0], MemorySpace)
            assert result[0].space_id == "1"
            assert result[0].name == "Test Space"

    @pytest.mark.asyncio
    async def test_list_spaces_multiple(self, memory_service):
        """Test list spaces with multiple spaces."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_spaces.return_value = [
                {"space_id": "1", "name": "Space 1"},
                {"id": "2", "name": "Space 2", "description": "Second space"},
            ]
            mock_client_class.return_value = mock_client

            result = await memory_service.list_spaces()
            assert len(result) == 2
            assert result[0].space_id == "1"
            assert result[1].space_id == "2"

    @pytest.mark.asyncio
    async def test_list_spaces_not_authenticated(
        self, memory_service, mock_auth_service
    ):
        """Test list spaces when not authenticated."""
        mock_auth_service.is_authenticated = False

        with pytest.raises(AuthenticationError):
            await memory_service.list_spaces()

    @pytest.mark.asyncio
    async def test_list_spaces_import_error_fallback(self, memory_service):
        """Test list spaces fallback when HeySolClient import fails."""
        with patch("heysol.HeySolClient", side_effect=ImportError):
            result = await memory_service.list_spaces()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_spaces_empty_payload(self, memory_service):
        """Test list spaces with empty payload."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_spaces.return_value = []
            mock_client_class.return_value = mock_client

            result = await memory_service.list_spaces()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_spaces_invalid_payload(self, memory_service):
        """Test list spaces with invalid payload items."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_spaces.return_value = [{"invalid": "data"}, {}]
            mock_client_class.return_value = mock_client

            result = await memory_service.list_spaces()
            assert len(result) == 2
            # Should handle missing fields gracefully
            assert result[0].space_id == ""
            assert result[0].name == ""

    @pytest.mark.asyncio
    async def test_search_with_exception(self, memory_service):
        """Test search with exception to cover error handling."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception, match="API error"):
                await memory_service.search("test")

    @pytest.mark.asyncio
    async def test_add_with_exception(self, memory_service):
        """Test add with exception to cover error handling."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception, match="API error"):
                await memory_service.add("test message")

    @pytest.mark.asyncio
    async def test_list_spaces_with_exception(self, memory_service):
        """Test list spaces with exception to cover error handling."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_spaces.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception, match="API error"):
                await memory_service.list_spaces()

    @pytest.mark.asyncio
    async def test_search_empty_query(self, memory_service):
        """Test search with empty query."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            result = await memory_service.search("")
            assert isinstance(result, MemorySearchResult)

    @pytest.mark.asyncio
    async def test_add_empty_message(self, memory_service):
        """Test add with empty message."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"episode_id": "123"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("")
            assert result.body == ""

    @pytest.mark.asyncio
    async def test_search_with_large_limit(self, memory_service):
        """Test search with large limit."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            await memory_service.search("test", limit=1000)
            mock_client.search.assert_called_once_with("test", None, 1000, False)

    @pytest.mark.asyncio
    async def test_search_with_zero_limit(self, memory_service):
        """Test search with zero limit."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            await memory_service.search("test", limit=0)
            mock_client.search.assert_called_once_with("test", None, 0, False)

    @pytest.mark.asyncio
    async def test_add_with_all_parameters(self, memory_service):
        """Test add with all optional parameters."""
        with patch("heysol.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"episode_id": "123"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add(
                "test message",
                space_id="space1",
                session_id="session1",
                source="source1",
            )
            mock_client.ingest.assert_called_once_with(
                "test message", "space1", "session1", "source1"
            )
            assert result.space_id == "space1"
