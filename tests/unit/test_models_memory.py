"""Unit tests for memory domain models."""

from src.models.memory import MemoryEpisode, MemorySearchResult, MemorySpace


class TestMemoryEpisode:
    """Test MemoryEpisode model."""

    def test_memory_episode_creation(self):
        """Test basic MemoryEpisode creation."""
        episode = MemoryEpisode(
            episode_id="test-episode-123",
            body="Test memory content",
            space_id="test-space",
        )

        assert episode.episode_id == "test-episode-123"
        assert episode.body == "Test memory content"
        assert episode.space_id == "test-space"
        assert episode.session_id is None
        assert episode.created_at is None
        assert episode.metadata == {}

    def test_memory_episode_with_all_fields(self):
        """Test MemoryEpisode with all optional fields."""
        metadata = {"source": "chat", "importance": "high"}
        episode = MemoryEpisode(
            episode_id="episode-456",
            body="Full memory content",
            space_id="space-1",
            session_id="session-789",
            created_at="2024-01-01T12:00:00Z",
            metadata=metadata,
        )

        assert episode.episode_id == "episode-456"
        assert episode.body == "Full memory content"
        assert episode.space_id == "space-1"
        assert episode.session_id == "session-789"
        assert episode.created_at == "2024-01-01T12:00:00Z"
        assert episode.metadata == metadata

    def test_memory_episode_from_api_valid(self):
        """Test creating MemoryEpisode from valid API response."""
        api_data = {
            "episode_id": "api-episode-123",
            "body": "API memory content",
            "space_id": "api-space",
            "session_id": "api-session",
            "created_at": "2024-01-02T10:30:00Z",
            "metadata": {"api_source": "test"},
        }

        episode = MemoryEpisode.from_api(api_data)

        assert episode.episode_id == "api-episode-123"
        assert episode.body == "API memory content"
        assert episode.space_id == "api-space"
        assert episode.session_id == "api-session"
        assert episode.created_at == "2024-01-02T10:30:00Z"
        assert episode.metadata == {"api_source": "test"}

    def test_memory_episode_from_api_minimal(self):
        """Test creating MemoryEpisode from minimal API response."""
        api_data = {
            "id": "minimal-episode",  # Alternative id field
            "content": "Minimal content",  # Alternative body field
        }

        episode = MemoryEpisode.from_api(api_data)

        assert episode.episode_id == "minimal-episode"
        assert episode.body == "Minimal content"
        assert episode.space_id is None
        assert episode.session_id is None
        assert episode.created_at is None
        assert episode.metadata == {}

    def test_memory_episode_from_api_missing_fields(self):
        """Test creating MemoryEpisode from API response with missing fields."""
        api_data = {}

        episode = MemoryEpisode.from_api(api_data)

        assert episode.episode_id == ""
        assert episode.body == ""
        assert episode.space_id is None
        assert episode.session_id is None
        assert episode.created_at is None
        assert episode.metadata == {}

    def test_memory_episode_equality(self):
        """Test MemoryEpisode equality."""
        episode1 = MemoryEpisode(
            episode_id="test-1", body="content", space_id="space-1"
        )
        episode2 = MemoryEpisode(
            episode_id="test-1", body="content", space_id="space-1"
        )
        episode3 = MemoryEpisode(
            episode_id="test-2", body="content", space_id="space-1"
        )

        assert episode1 == episode2
        assert episode1 != episode3


class TestMemorySearchResult:
    """Test MemorySearchResult model."""

    def test_memory_search_result_creation(self):
        """Test basic MemorySearchResult creation."""
        episodes = [
            MemoryEpisode(episode_id="ep1", body="content1"),
            MemoryEpisode(episode_id="ep2", body="content2"),
        ]

        result = MemorySearchResult(episodes=episodes, total=2)

        assert len(result.episodes) == 2
        assert result.total == 2
        assert result.episodes[0].episode_id == "ep1"
        assert result.episodes[1].episode_id == "ep2"

    def test_memory_search_result_empty(self):
        """Test MemorySearchResult with no episodes."""
        result = MemorySearchResult()

        assert len(result.episodes) == 0
        assert result.total == 0

    def test_memory_search_result_from_api_valid(self):
        """Test creating MemorySearchResult from valid API response."""
        api_data = {
            "episodes": [
                {
                    "episode_id": "api-ep1",
                    "body": "API content 1",
                    "space_id": "space-1",
                },
                {
                    "episode_id": "api-ep2",
                    "body": "API content 2",
                    "space_id": "space-1",
                },
            ],
            "total": 2,
        }

        result = MemorySearchResult.from_api(api_data)

        assert len(result.episodes) == 2
        assert result.total == 2
        assert result.episodes[0].episode_id == "api-ep1"
        assert result.episodes[1].episode_id == "api-ep2"

    def test_memory_search_result_from_api_empty(self):
        """Test creating MemorySearchResult from empty API response."""
        api_data = {"episodes": [], "total": 0}

        result = MemorySearchResult.from_api(api_data)

        assert len(result.episodes) == 0
        assert result.total == 0

    def test_memory_search_result_from_api_missing_total(self):
        """Test creating MemorySearchResult when total is missing."""
        api_data = {"episodes": [{"episode_id": "ep1", "body": "content"}]}

        result = MemorySearchResult.from_api(api_data)

        assert len(result.episodes) == 1
        assert result.total == 1  # Should default to episode count


class TestMemorySpace:
    """Test MemorySpace model."""

    def test_memory_space_creation(self):
        """Test basic MemorySpace creation."""
        space = MemorySpace(
            space_id="test-space-123",
            name="Test Space",
            description="A test memory space",
        )

        assert space.space_id == "test-space-123"
        assert space.name == "Test Space"
        assert space.description == "A test memory space"
        assert space.created_at is None

    def test_memory_space_minimal(self):
        """Test MemorySpace with minimal fields."""
        space = MemorySpace(space_id="minimal-space", name="Minimal Space")

        assert space.space_id == "minimal-space"
        assert space.name == "Minimal Space"
        assert space.description is None
        assert space.created_at is None

    def test_memory_space_with_created_at(self):
        """Test MemorySpace with created_at field."""
        space = MemorySpace(
            space_id="space-with-date",
            name="Space with Date",
            description="Has creation date",
            created_at="2024-01-01T00:00:00Z",
        )

        assert space.space_id == "space-with-date"
        assert space.name == "Space with Date"
        assert space.description == "Has creation date"
        assert space.created_at == "2024-01-01T00:00:00Z"

    def test_memory_space_from_dict_valid(self):
        """Test creating MemorySpace from valid dictionary."""
        data = {
            "space_id": "dict-space-123",
            "name": "Dict Space",
            "description": "From dictionary",
            "created_at": "2024-01-02T12:00:00Z",
        }

        space = MemorySpace.from_dict(data)

        assert space.space_id == "dict-space-123"
        assert space.name == "Dict Space"
        assert space.description == "From dictionary"
        assert space.created_at == "2024-01-02T12:00:00Z"

    def test_memory_space_from_dict_minimal(self):
        """Test creating MemorySpace from minimal dictionary."""
        data = {
            "id": "minimal-dict-space",
            "name": "Minimal Dict Space",
        }  # Alternative id field

        space = MemorySpace.from_dict(data)

        assert space.space_id == "minimal-dict-space"
        assert space.name == "Minimal Dict Space"
        assert space.description is None
        assert space.created_at is None

    def test_memory_space_from_dict_missing_fields(self):
        """Test creating MemorySpace from dictionary with missing fields."""
        data = {}

        space = MemorySpace.from_dict(data)

        assert space.space_id == ""
        assert space.name == ""
        assert space.description is None
        assert space.created_at is None

    def test_memory_space_equality(self):
        """Test MemorySpace equality."""
        space1 = MemorySpace(space_id="space-1", name="Space One")
        space2 = MemorySpace(space_id="space-1", name="Space One")
        space3 = MemorySpace(space_id="space-2", name="Space Two")

        assert space1 == space2
        assert space1 != space3
