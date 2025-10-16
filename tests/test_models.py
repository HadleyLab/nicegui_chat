"""Unit tests for chat models."""

from src.models.chat import (ChatEventType, ChatMessage, ChatStreamEvent,
                             ConversationState, ConversationStatus,
                             ExecutionStep, MessageRole)
from src.models.memory import MemoryEpisode, MemorySearchResult, MemorySpace


class TestChatMessage:
    """Test ChatMessage model."""

    def test_create_user_message(self):
        """Test creating a user message."""
        message = ChatMessage(role=MessageRole.USER, content="Hello")
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.message_id is not None
        assert message.created_at is not None
        assert isinstance(message.metadata, dict)

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        message = ChatMessage(role=MessageRole.ASSISTANT, content="Hi there")
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Hi there"

    def test_message_with_metadata(self):
        """Test message with custom metadata."""
        metadata = {"source": "test"}
        message = ChatMessage(role=MessageRole.USER, content="Test", metadata=metadata)
        assert message.metadata == metadata


class TestConversationState:
    """Test ConversationState model."""

    def test_initial_state(self):
        """Test initial conversation state."""
        conv = ConversationState()
        assert conv.status == ConversationStatus.IDLE
        assert conv.messages == []
        assert conv.execution_history == []
        assert conv.conversation_id is not None

    def test_append_message(self):
        """Test appending messages to conversation."""
        conv = ConversationState()
        msg1 = ChatMessage(role=MessageRole.USER, content="Hello")
        msg2 = ChatMessage(role=MessageRole.ASSISTANT, content="Hi")

        conv.append_message(msg1)
        conv.append_message(msg2)

        assert len(conv.messages) == 2
        assert conv.messages[0] == msg1
        assert conv.messages[1] == msg2

    def test_get_last_assistant_message(self):
        """Test getting the last assistant message."""
        conv = ConversationState()
        user_msg = ChatMessage(role=MessageRole.USER, content="Hello")
        assistant_msg1 = ChatMessage(role=MessageRole.ASSISTANT, content="Hi")
        assistant_msg2 = ChatMessage(role=MessageRole.ASSISTANT, content="How are you?")

        conv.append_message(user_msg)
        conv.append_message(assistant_msg1)
        conv.append_message(assistant_msg2)

        last_assistant = conv.get_last_assistant_message()
        assert last_assistant == assistant_msg2

    def test_get_last_assistant_message_no_assistant(self):
        """Test getting last assistant message when none exists."""
        conv = ConversationState()
        user_msg = ChatMessage(role=MessageRole.USER, content="Hello")
        conv.append_message(user_msg)

        last_assistant = conv.get_last_assistant_message()
        assert last_assistant is None

    def test_clear_messages(self):
        """Test clearing messages from conversation."""
        conv = ConversationState()
        conv.append_message(ChatMessage(role=MessageRole.USER, content="Hello"))
        conv.append_message(ChatMessage(role=MessageRole.ASSISTANT, content="Hi"))
        conv.execution_history.append(
            ExecutionStep(skill_name="test", status="complete")
        )

        conv.clear_messages()

        assert conv.messages == []
        assert conv.execution_history == []
        assert conv.status == ConversationStatus.IDLE


class TestChatStreamEvent:
    """Test ChatStreamEvent model."""

    def test_create_event(self):
        """Test creating a stream event."""
        event = ChatStreamEvent(
            event_type=ChatEventType.MESSAGE_CHUNK, payload={"content": "test"}
        )
        assert event.event_type == ChatEventType.MESSAGE_CHUNK
        assert event.payload == {"content": "test"}

    def test_event_with_empty_payload(self):
        """Test event with empty payload."""
        event = ChatStreamEvent(event_type=ChatEventType.STREAM_END)
        assert event.event_type == ChatEventType.STREAM_END
        assert event.payload == {}


class TestExecutionStep:
    """Test ExecutionStep model."""

    def test_create_step(self):
        """Test creating an execution step."""
        step = ExecutionStep(
            skill_name="memory",
            status="complete",
            observation="test observation",
            user_message="test message",
            data={"key": "value"},
        )
        assert step.skill_name == "memory"
        assert step.status == "complete"
        assert step.observation == "test observation"
        assert step.user_message == "test message"
        assert step.data == {"key": "value"}
        assert step.step_id is not None


class TestMemoryEpisode:
    """Test MemoryEpisode model."""

    def test_create_memory_episode(self):
        """Test creating a memory episode."""
        episode = MemoryEpisode(
            episode_id="123",
            body="Test memory",
            space_id="space1",
            session_id="session1",
            created_at="2023-01-01",
            metadata={"key": "value"},
        )
        assert episode.episode_id == "123"
        assert episode.body == "Test memory"
        assert episode.space_id == "space1"
        assert episode.session_id == "session1"
        assert episode.created_at == "2023-01-01"
        assert episode.metadata == {"key": "value"}

    def test_from_api_with_episode_id(self):
        """Test from_api method with episode_id."""
        payload = {
            "episode_id": "123",
            "body": "Test content",
            "space_id": "space1",
            "session_id": "session1",
            "created_at": "2023-01-01",
            "metadata": {"key": "value"},
        }
        episode = MemoryEpisode.from_api(payload)
        assert episode.episode_id == "123"
        assert episode.body == "Test content"
        assert episode.space_id == "space1"

    def test_from_api_with_id_fallback(self):
        """Test from_api method with id fallback."""
        payload = {"id": "456", "content": "Alternative content", "metadata": {}}
        episode = MemoryEpisode.from_api(payload)
        assert episode.episode_id == "456"
        assert episode.body == "Alternative content"
        assert episode.space_id is None


class TestMemorySearchResult:
    """Test MemorySearchResult model."""

    def test_create_memory_search_result(self):
        """Test creating a memory search result."""
        result = MemorySearchResult(episodes=[], total=0)
        assert result.episodes == []
        assert result.total == 0

    def test_from_api_empty(self):
        """Test from_api method with empty result."""
        payload = {"episodes": [], "total": 0}
        result = MemorySearchResult.from_api(payload)
        assert result.episodes == []
        assert result.total == 0

    def test_from_api_with_episodes(self):
        """Test from_api method with episodes."""
        payload = {
            "episodes": [
                {"episode_id": "1", "body": "Episode 1", "space_id": "space1"},
                {"id": "2", "content": "Episode 2"},
            ],
            "total": 2,
        }
        result = MemorySearchResult.from_api(payload)
        assert len(result.episodes) == 2
        assert result.episodes[0].episode_id == "1"
        assert result.episodes[0].body == "Episode 1"
        assert result.episodes[1].episode_id == "2"
        assert result.episodes[1].body == "Episode 2"
        assert result.total == 2


class TestMemorySpace:
    """Test MemorySpace model."""

    def test_create_memory_space(self):
        """Test creating a memory space."""
        space = MemorySpace(
            space_id="space1",
            name="Test Space",
            description="A test space",
            created_at="2023-01-01",
        )
        assert space.space_id == "space1"
        assert space.name == "Test Space"
        assert space.description == "A test space"
        assert space.created_at == "2023-01-01"

    def test_from_dict_with_space_id(self):
        """Test from_dict method with space_id."""
        payload = {
            "space_id": "space1",
            "name": "Test Space",
            "description": "Description",
            "created_at": "2023-01-01",
        }
        space = MemorySpace.from_dict(payload)
        assert space.space_id == "space1"
        assert space.name == "Test Space"
        assert space.description == "Description"

    def test_from_dict_with_id_fallback(self):
        """Test from_dict method with id fallback."""
        payload = {"id": "space2", "name": "Another Space"}
        space = MemorySpace.from_dict(payload)
        assert space.space_id == "space2"
        assert space.name == "Another Space"
        assert space.description is None


class TestEnums:
    """Test enum values."""

    def test_message_role_values(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.ERROR.value == "error"

    def test_conversation_status_values(self):
        """Test ConversationStatus enum values."""
        assert ConversationStatus.IDLE.value == "idle"
        assert ConversationStatus.RUNNING.value == "running"
        assert ConversationStatus.SUCCESS.value == "success"
        assert ConversationStatus.FAILED.value == "failed"

    def test_chat_event_type_values(self):
        """Test ChatEventType enum values."""
        assert ChatEventType.MESSAGE_START.value == "MESSAGE_START"
        assert ChatEventType.MESSAGE_CHUNK.value == "MESSAGE_CHUNK"
        assert ChatEventType.MESSAGE_END.value == "MESSAGE_END"
        assert ChatEventType.STEP.value == "STEP"
        assert ChatEventType.ERROR.value == "ERROR"
        assert ChatEventType.STREAM_END.value == "STREAM_END"
        assert ChatEventType.SYSTEM.value == "SYSTEM"
