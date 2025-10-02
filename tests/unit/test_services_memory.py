"""Unit tests for memory service."""

from unittest.mock import MagicMock

import pytest

from src.services.memory_service import MemoryService
from src.utils.exceptions import AuthenticationError, ChatServiceError


class TestMemoryService:
    """Test MemoryService functionality."""

    def test_memory_service_init(self, mock_auth_service):
        """Test MemoryService initialization."""
        service = MemoryService(mock_auth_service)
        assert service._auth_service == mock_auth_service

    @pytest.mark.asyncio
    async def test_search_authenticated(self, mock_memory_service):
        """Test search when authenticated."""
        # Setup
        query = "test query"
        space_ids = ["space-1", "space-2"]
        limit = 10
        include_invalidated = False

        # Mock the client search
        mock_memory_service._auth_service.client.search = MagicMock(
            return_value={
                "episodes": [
                    {
                        "episode_id": "ep1",
                        "body": "Test episode 1",
                        "space_id": "space-1",
                        "created_at": "2024-01-01T00:00:00Z",
                    }
                ],
                "total": 1,
            }
        )

        # Execute
        result = await mock_memory_service.search(
            query=query,
            space_ids=space_ids,
            limit=limit,
            include_invalidated=include_invalidated,
        )

        # Verify
        assert len(result.episodes) == 1
        assert result.total == 1
        assert result.episodes[0].episode_id == "ep1"
        assert result.episodes[0].body == "Test episode 1"

        # Check that client.search was called correctly
        mock_memory_service._auth_service.client.search.assert_called_once_with(
            query, space_ids, limit, include_invalidated
        )

    @pytest.mark.asyncio
    async def test_search_not_authenticated(self):
        """Test search when not authenticated."""
        # Create unauthenticated auth service
        mock_auth = MagicMock()
        mock_auth.is_authenticated = False
        service = MemoryService(mock_auth)

        with pytest.raises(AuthenticationError) as exc_info:
            await service.search("test query")

        assert "Authentication required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_with_none_space_ids(self, mock_memory_service):
        """Test search with None space_ids."""
        query = "test query"

        mock_memory_service._auth_service.client.search = MagicMock(
            return_value={"episodes": [], "total": 0}
        )

        result = await mock_memory_service.search(query=query, space_ids=None)

        assert len(result.episodes) == 0
        assert result.total == 0

        # Check that None was passed to client.search
        mock_memory_service._auth_service.client.search.assert_called_once_with(
            query, None, 10, False
        )

    @pytest.mark.asyncio
    async def test_search_client_error(self, mock_memory_service):
        """Test search when client raises an error."""
        mock_memory_service._auth_service.client.search.side_effect = Exception(
            "API error"
        )

        with pytest.raises(ChatServiceError) as exc_info:
            await mock_memory_service.search("test query")

        assert "Memory search failed" in str(exc_info.value)
        assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_unexpected_response_format(self, mock_memory_service):
        """Test search with unexpected response format."""
        mock_memory_service._auth_service.client.search.return_value = "not a dict"

        # Should handle gracefully and return empty result
        result = await mock_memory_service.search("test query")

        assert len(result.episodes) == 0
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_add_authenticated(self, mock_memory_service):
        """Test add when authenticated."""
        message = "Test memory message"
        space_id = "test-space"
        session_id = "test-session"
        source = "test-source"

        mock_memory_service._auth_service.client.ingest.return_value = {
            "episode_id": "new-episode-id",
            "id": "new-episode-id",
        }

        result = await mock_memory_service.add(
            message=message, space_id=space_id, session_id=session_id, source=source
        )

        assert result.episode_id == "new-episode-id"
        assert result.body == message
        assert result.space_id == space_id

        mock_memory_service._auth_service.client.ingest.assert_called_once_with(
            message, space_id, session_id, source
        )

    @pytest.mark.asyncio
    async def test_add_not_authenticated(self):
        """Test add when not authenticated."""
        # Create unauthenticated auth service
        mock_auth = MagicMock()
        mock_auth.is_authenticated = False
        service = MemoryService(mock_auth)

        with pytest.raises(AuthenticationError) as exc_info:
            await service.add("test message")

        assert "Authentication required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_minimal_parameters(self, mock_memory_service):
        """Test add with minimal parameters."""
        message = "Simple message"

        mock_memory_service._auth_service.client.ingest.return_value = {
            "episode_id": "simple-episode"
        }

        result = await mock_memory_service.add(message)

        assert result.episode_id == "simple-episode"
        assert result.body == message
        assert result.space_id is None

        mock_memory_service._auth_service.client.ingest.assert_called_once_with(
            message, None, None, None
        )

    @pytest.mark.asyncio
    async def test_add_client_error(self, mock_memory_service):
        """Test add when client raises an error."""
        mock_memory_service._auth_service.client.ingest.side_effect = Exception(
            "Ingest failed"
        )

        with pytest.raises(ChatServiceError) as exc_info:
            await mock_memory_service.add("test message")

        assert "Memory add failed" in str(exc_info.value)
        assert "Ingest failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_response_parsing(self, mock_memory_service):
        """Test add response parsing with different formats."""
        test_cases = [
            {"episode_id": "ep1", "id": "ep1"},
            {"episode_id": "ep2"},  # No id field
            {"id": "ep3"},  # No episode_id field
            {},  # No id fields
        ]

        for i, response in enumerate(test_cases):
            mock_memory_service._auth_service.client.ingest.return_value = response
            expected_id = response.get("episode_id") or response.get("id") or ""

            result = await mock_memory_service.add(f"message {i}")

            assert result.episode_id == expected_id

    @pytest.mark.asyncio
    async def test_list_spaces_authenticated(self, mock_memory_service):
        """Test list_spaces when authenticated."""
        mock_spaces = [
            {"space_id": "space-1", "name": "Space One", "description": "First space"},
            {"space_id": "space-2", "name": "Space Two", "description": "Second space"},
        ]
        mock_memory_service._auth_service.client.get_spaces.return_value = mock_spaces

        result = await mock_memory_service.list_spaces()

        assert len(result) == 2
        assert result[0].space_id == "space-1"
        assert result[0].name == "Space One"
        assert result[0].description == "First space"
        assert result[1].space_id == "space-2"
        assert result[1].name == "Space Two"

        mock_memory_service._auth_service.client.get_spaces.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_spaces_not_authenticated(self):
        """Test list_spaces when not authenticated."""
        # Create unauthenticated auth service
        mock_auth = MagicMock()
        mock_auth.is_authenticated = False
        service = MemoryService(mock_auth)

        with pytest.raises(AuthenticationError) as exc_info:
            await service.list_spaces()

        assert "Authentication required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_spaces_empty(self, mock_memory_service):
        """Test list_spaces with empty response."""
        mock_memory_service._auth_service.client.get_spaces.return_value = []

        result = await mock_memory_service.list_spaces()

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_spaces_client_error(self, mock_memory_service):
        """Test list_spaces when client raises an error."""
        mock_memory_service._auth_service.client.get_spaces.side_effect = Exception(
            "Get spaces failed"
        )

        with pytest.raises(ChatServiceError) as exc_info:
            await mock_memory_service.list_spaces()

        assert "Failed to list memory spaces" in str(exc_info.value)
        assert "Get spaces failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_spaces_malformed_response(self, mock_memory_service):
        """Test list_spaces with malformed response."""
        mock_memory_service._auth_service.client.get_spaces.return_value = [
            {"space_id": "good-space", "name": "Good Space"},
            {"invalid": "space"},  # Missing required fields
        ]

        result = await mock_memory_service.list_spaces()

        # Should handle malformed spaces gracefully
        assert len(result) == 2
        assert result[0].space_id == "good-space"
        assert result[0].name == "Good Space"
        # Second space should have empty/default values
        assert result[1].space_id == ""
        assert result[1].name == ""

    def test_memory_service_no_init_dependencies(self):
        """Test that MemoryService doesn't require complex initialization."""
        # This test ensures the service can be created without complex setup
        # which is important for testing isolation
        mock_auth = MagicMock()
        service = MemoryService(mock_auth)
        assert service._auth_service == mock_auth
