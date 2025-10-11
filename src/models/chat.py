"""Chat domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class ConversationStatus(str, Enum):
    """Conversation status enumeration."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ChatEventType(str, Enum):
    """Chat event type enumeration."""

    MESSAGE_START = "MESSAGE_START"
    MESSAGE_CHUNK = "MESSAGE_CHUNK"
    MESSAGE_END = "MESSAGE_END"
    STEP = "STEP"
    ERROR = "ERROR"
    STREAM_END = "STREAM_END"
    SYSTEM = "SYSTEM"


class ChatMessage(BaseModel):
    """Chat message model with performance optimizations."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        frozen=False,
        populate_by_name=True,
    )

    message_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique message identifier"
    )
    role: MessageRole = Field(description="Role of the message sender")
    content: str = Field(description="Message content text")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message creation timestamp",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional message metadata"
    )

    def __hash__(self) -> int:
        """Optimized hash for message deduplication."""
        return hash((self.message_id, self.role, self.content))


class ExecutionStep(BaseModel):
    """Execution step model for tracking agent actions with performance optimizations."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        frozen=False,
        populate_by_name=True,
    )

    step_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique step identifier"
    )
    skill_name: str = Field(description="Name of the executed skill")
    status: str = Field(description="Execution status")
    observation: str | None = Field(default=None, description="Execution observation")
    user_message: str = Field(default="", description="Associated user message")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Additional step data"
    )

    def __hash__(self) -> int:
        """Optimized hash for step deduplication."""
        return hash((self.step_id, self.skill_name, self.status))


class ConversationState(BaseModel):
    """Conversation state model with bounded memory management."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        frozen=False,
        populate_by_name=True,
    )

    conversation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique conversation identifier",
    )
    status: ConversationStatus = Field(
        default=ConversationStatus.IDLE, description="Current conversation status"
    )
    messages: list[ChatMessage] = Field(
        default_factory=list, description="Conversation messages"
    )
    execution_history: list[ExecutionStep] = Field(
        default_factory=list, description="Execution step history"
    )
    memory_space_ids: list[str] = Field(
        default_factory=list, description="Associated memory space IDs"
    )
    credits_remaining: int | None = Field(
        default=None, description="Remaining conversation credits"
    )

    # Memory management configuration
    max_messages: int = Field(
        default=1000, description="Maximum number of messages to retain"
    )
    max_execution_steps: int = Field(
        default=500, description="Maximum execution steps to retain"
    )

    def append_message(self, message: ChatMessage) -> None:
        """Append a message to the conversation with bounded memory."""
        self.messages.append(message)
        self._enforce_message_limits()

    def append_execution_step(self, step: ExecutionStep) -> None:
        """Append an execution step with bounded memory."""
        self.execution_history.append(step)
        self._enforce_step_limits()

    def get_last_assistant_message(self) -> ChatMessage | None:
        """Get the last assistant message in the conversation."""
        for message in reversed(self.messages):
            if message.role == MessageRole.ASSISTANT:
                return message
        return None

    def clear_messages(self) -> None:
        """Clear all messages from the conversation."""
        self.messages.clear()
        self.execution_history.clear()
        self.status = ConversationStatus.IDLE

    def _enforce_message_limits(self) -> None:
        """Enforce message count limits to prevent memory bloat."""
        if len(self.messages) > self.max_messages:
            # Keep only the most recent messages
            self.messages = self.messages[-self.max_messages :]

    def _enforce_step_limits(self) -> None:
        """Enforce execution step limits to prevent memory bloat."""
        if len(self.execution_history) > self.max_execution_steps:
            # Keep only the most recent steps
            self.execution_history = self.execution_history[-self.max_execution_steps :]


class ChatStreamEvent(BaseModel):
    """Chat stream event model with performance optimizations."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        frozen=False,
        populate_by_name=True,
    )

    event_type: ChatEventType = Field(description="Type of chat event")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event payload data"
    )

    def __hash__(self) -> int:
        """Optimized hash for event deduplication."""
        return hash((self.event_type, str(self.payload)))
