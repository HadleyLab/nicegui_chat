"""Unit tests for chat domain models."""

from datetime import datetime, timezone

from src.models.chat import (
    ChatEventType,
    ChatMessage,
    ChatStreamEvent,
    ConversationState,
    ConversationStatus,
    ExecutionStep,
    MessageRole,
)


class TestMessageRole:
    """Test MessageRole enum."""

    def test_message_role_values(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.ERROR.value == "error"

    def test_message_role_membership(self):
        """Test MessageRole enum membership."""
        assert MessageRole.USER in MessageRole
        assert MessageRole.ASSISTANT in MessageRole
        assert MessageRole.SYSTEM in MessageRole
        assert MessageRole.ERROR in MessageRole

    def test_message_role_string_conversion(self):
        """Test MessageRole string conversion."""
        assert str(MessageRole.USER) == "MessageRole.USER"
        assert MessageRole.USER.value == "user"


class TestConversationStatus:
    """Test ConversationStatus enum."""

    def test_conversation_status_values(self):
        """Test ConversationStatus enum values."""
        assert ConversationStatus.IDLE.value == "idle"
        assert ConversationStatus.RUNNING.value == "running"
        assert ConversationStatus.SUCCESS.value == "success"
        assert ConversationStatus.FAILED.value == "failed"

    def test_conversation_status_membership(self):
        """Test ConversationStatus enum membership."""
        assert ConversationStatus.IDLE in ConversationStatus
        assert ConversationStatus.RUNNING in ConversationStatus
        assert ConversationStatus.SUCCESS in ConversationStatus
        assert ConversationStatus.FAILED in ConversationStatus


class TestChatEventType:
    """Test ChatEventType enum."""

    def test_chat_event_type_values(self):
        """Test ChatEventType enum values."""
        assert ChatEventType.MESSAGE_START.value == "MESSAGE_START"
        assert ChatEventType.MESSAGE_CHUNK.value == "MESSAGE_CHUNK"
        assert ChatEventType.MESSAGE_END.value == "MESSAGE_END"
        assert ChatEventType.STEP.value == "STEP"
        assert ChatEventType.ERROR.value == "ERROR"
        assert ChatEventType.STREAM_END.value == "STREAM_END"
        assert ChatEventType.SYSTEM.value == "SYSTEM"

    def test_chat_event_type_membership(self):
        """Test ChatEventType enum membership."""
        assert ChatEventType.MESSAGE_START in ChatEventType
        assert ChatEventType.STREAM_END in ChatEventType


class TestChatMessage:
    """Test ChatMessage model."""

    def test_chat_message_creation_minimal(self):
        """Test ChatMessage creation with minimal fields."""
        message = ChatMessage(role=MessageRole.USER, content="Hello, world!")

        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.message_id is not None
        assert len(message.message_id) > 0
        assert message.metadata == {}
        assert message.created_at is not None

    def test_chat_message_creation_full(self):
        """Test ChatMessage creation with all fields."""
        test_time = datetime.now(timezone.utc)
        metadata = {"source": "test", "priority": "high"}

        message = ChatMessage(
            message_id="custom-id-123",
            role=MessageRole.ASSISTANT,
            content="Test response",
            created_at=test_time,
            metadata=metadata,
        )

        assert message.message_id == "custom-id-123"
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Test response"
        assert message.created_at == test_time
        assert message.metadata == metadata

    def test_chat_message_auto_id_generation(self):
        """Test automatic ID generation for ChatMessage."""
        message1 = ChatMessage(role=MessageRole.USER, content="test")
        message2 = ChatMessage(role=MessageRole.USER, content="test")

        assert message1.message_id != message2.message_id
        assert len(message1.message_id) > 0
        assert len(message2.message_id) > 0

    def test_chat_message_auto_timestamp(self):
        """Test automatic timestamp generation for ChatMessage."""
        before = datetime.now(timezone.utc)
        message = ChatMessage(role=MessageRole.USER, content="test")
        after = datetime.now(timezone.utc)

        assert before <= message.created_at <= after

    def test_chat_message_serialization(self):
        """Test ChatMessage serialization includes enum values."""
        message = ChatMessage(role=MessageRole.USER, content="test")

        # Test that the message can be serialized
        data = message.model_dump()
        assert data["role"] == "user"  # Should use enum value
        assert data["content"] == "test"

    def test_chat_message_equality(self):
        """Test ChatMessage equality by field comparison."""
        message1 = ChatMessage(
            message_id="test-1", role=MessageRole.USER, content="content"
        )
        message2 = ChatMessage(
            message_id="test-1", role=MessageRole.USER, content="content"
        )
        message3 = ChatMessage(
            message_id="test-2", role=MessageRole.USER, content="content"
        )

        # Test field-by-field equality since Pydantic models compare all fields
        assert message1.message_id == message2.message_id
        assert message1.role == message2.role
        assert message1.content == message2.content
        assert message1.message_id != message3.message_id
        assert message1.role == message3.role  # Same role
        assert message1.content == message3.content  # Same content


class TestExecutionStep:
    """Test ExecutionStep model."""

    def test_execution_step_creation_minimal(self):
        """Test ExecutionStep creation with minimal fields."""
        step = ExecutionStep(skill_name="memory", status="complete")

        assert step.skill_name == "memory"
        assert step.status == "complete"
        assert step.step_id is not None
        assert step.observation is None
        assert step.user_message == ""
        assert step.data == {}

    def test_execution_step_creation_full(self):
        """Test ExecutionStep creation with all fields."""
        data = {"result": "success", "items": ["item1", "item2"]}

        step = ExecutionStep(
            step_id="custom-step-123",
            skill_name="search",
            status="running",
            observation="Search completed",
            user_message="Find information",
            data=data,
        )

        assert step.step_id == "custom-step-123"
        assert step.skill_name == "search"
        assert step.status == "running"
        assert step.observation == "Search completed"
        assert step.user_message == "Find information"
        assert step.data == data

    def test_execution_step_auto_id_generation(self):
        """Test automatic ID generation for ExecutionStep."""
        step1 = ExecutionStep(skill_name="test", status="pending")
        step2 = ExecutionStep(skill_name="test", status="pending")

        assert step1.step_id != step2.step_id
        assert len(step1.step_id) > 0


class TestConversationState:
    """Test ConversationState model."""

    def test_conversation_state_creation_minimal(self):
        """Test ConversationState creation with minimal fields."""
        conversation = ConversationState()

        assert conversation.conversation_id is not None
        assert len(conversation.conversation_id) > 0
        assert conversation.status == ConversationStatus.IDLE
        assert conversation.messages == []
        assert conversation.execution_history == []
        assert conversation.memory_space_ids == []
        assert conversation.credits_remaining is None

    def test_conversation_state_creation_full(self):
        """Test ConversationState creation with all fields."""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there"),
        ]
        execution_history = [ExecutionStep(skill_name="memory", status="complete")]

        conversation = ConversationState(
            conversation_id="custom-conv-123",
            status=ConversationStatus.RUNNING,
            messages=messages,
            execution_history=execution_history,
            memory_space_ids=["space-1", "space-2"],
            credits_remaining=100,
        )

        assert conversation.conversation_id == "custom-conv-123"
        assert conversation.status == ConversationStatus.RUNNING
        assert conversation.messages == messages
        assert conversation.execution_history == execution_history
        assert conversation.memory_space_ids == ["space-1", "space-2"]
        assert conversation.credits_remaining == 100

    def test_conversation_state_auto_id_generation(self):
        """Test automatic ID generation for ConversationState."""
        conv1 = ConversationState()
        conv2 = ConversationState()

        assert conv1.conversation_id != conv2.conversation_id
        assert len(conv1.conversation_id) > 0

    def test_conversation_state_append_message(self):
        """Test appending messages to conversation."""
        conversation = ConversationState()
        message1 = ChatMessage(role=MessageRole.USER, content="First message")
        message2 = ChatMessage(role=MessageRole.ASSISTANT, content="Response")

        conversation.append_message(message1)
        assert len(conversation.messages) == 1
        assert conversation.messages[0] == message1

        conversation.append_message(message2)
        assert len(conversation.messages) == 2
        assert conversation.messages[1] == message2

    def test_conversation_state_get_last_assistant_message(self):
        """Test getting the last assistant message."""
        conversation = ConversationState()

        # No messages
        assert conversation.get_last_assistant_message() is None

        # Add user message
        conversation.append_message(ChatMessage(role=MessageRole.USER, content="Hello"))
        assert conversation.get_last_assistant_message() is None

        # Add assistant message
        assistant_msg = ChatMessage(role=MessageRole.ASSISTANT, content="Hi")
        conversation.append_message(assistant_msg)
        assert conversation.get_last_assistant_message() == assistant_msg

        # Add another user message
        conversation.append_message(
            ChatMessage(role=MessageRole.USER, content="How are you?")
        )
        assert conversation.get_last_assistant_message() == assistant_msg

        # Add another assistant message
        new_assistant_msg = ChatMessage(role=MessageRole.ASSISTANT, content="I'm fine")
        conversation.append_message(new_assistant_msg)
        assert conversation.get_last_assistant_message() == new_assistant_msg

    def test_conversation_state_clear_messages(self):
        """Test clearing messages from conversation."""
        conversation = ConversationState()
        conversation.append_message(ChatMessage(role=MessageRole.USER, content="test"))
        conversation.execution_history.append(
            ExecutionStep(skill_name="test", status="complete")
        )
        conversation.status = ConversationStatus.RUNNING

        conversation.clear_messages()

        assert conversation.messages == []
        assert conversation.execution_history == []
        assert conversation.status == ConversationStatus.IDLE

    def test_conversation_state_serialization(self):
        """Test ConversationState serialization includes enum values."""
        conversation = ConversationState(status=ConversationStatus.RUNNING)

        # Test that the conversation can be serialized
        data = conversation.model_dump()
        assert data["status"] == "running"  # Should use enum value
        assert "conversation_id" in data


class TestChatStreamEvent:
    """Test ChatStreamEvent model."""

    def test_chat_stream_event_creation_minimal(self):
        """Test ChatStreamEvent creation with minimal fields."""
        event = ChatStreamEvent(event_type=ChatEventType.MESSAGE_START)

        assert event.event_type == ChatEventType.MESSAGE_START
        assert event.payload == {}

    def test_chat_stream_event_creation_full(self):
        """Test ChatStreamEvent creation with payload."""
        payload = {"content": "Hello", "role": "assistant"}

        event = ChatStreamEvent(event_type=ChatEventType.MESSAGE_CHUNK, payload=payload)

        assert event.event_type == ChatEventType.MESSAGE_CHUNK
        assert event.payload == payload

    def test_chat_stream_event_serialization(self):
        """Test ChatStreamEvent serialization includes enum values."""
        event = ChatStreamEvent(event_type=ChatEventType.STREAM_END)

        # Test that the event can be serialized
        data = event.model_dump()
        assert data["event_type"] == "STREAM_END"  # Should use enum value
        assert data["payload"] == {}

    def test_chat_stream_event_equality(self):
        """Test ChatStreamEvent equality."""
        event1 = ChatStreamEvent(
            event_type=ChatEventType.MESSAGE_START, payload={"role": "assistant"}
        )
        event2 = ChatStreamEvent(
            event_type=ChatEventType.MESSAGE_START, payload={"role": "assistant"}
        )
        event3 = ChatStreamEvent(
            event_type=ChatEventType.MESSAGE_END, payload={"content": "done"}
        )

        assert event1 == event2
        assert event1 != event3
