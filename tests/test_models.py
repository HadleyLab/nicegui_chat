"""Unit tests for chat models."""

import pytest
from datetime import datetime, timezone

from src.models.chat import (
    ChatEventType,
    ChatMessage,
    ConversationState,
    ConversationStatus,
    ChatStreamEvent,
    ExecutionStep,
    MessageRole,
)


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
        message = ChatMessage(
            role=MessageRole.USER,
            content="Test",
            metadata=metadata
        )
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
        conv.execution_history.append(ExecutionStep(skill_name="test", status="complete"))

        conv.clear_messages()

        assert conv.messages == []
        assert conv.execution_history == []
        assert conv.status == ConversationStatus.IDLE


class TestChatStreamEvent:
    """Test ChatStreamEvent model."""

    def test_create_event(self):
        """Test creating a stream event."""
        event = ChatStreamEvent(event_type=ChatEventType.MESSAGE_CHUNK, payload={"content": "test"})
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
            data={"key": "value"}
        )
        assert step.skill_name == "memory"
        assert step.status == "complete"
        assert step.observation == "test observation"
        assert step.user_message == "test message"
        assert step.data == {"key": "value"}
        assert step.step_id is not None


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