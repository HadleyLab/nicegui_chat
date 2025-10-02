"""Chat domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


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
    """Chat message model."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class ExecutionStep(BaseModel):
    """Execution step model for tracking agent actions."""
    step_id: str = Field(default_factory=lambda: str(uuid4()))
    skill_name: str
    status: str
    observation: Optional[str] = None
    user_message: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """Conversation state model."""
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    status: ConversationStatus = ConversationStatus.IDLE
    messages: list[ChatMessage] = Field(default_factory=list)
    execution_history: list[ExecutionStep] = Field(default_factory=list)
    memory_space_ids: list[str] = Field(default_factory=list)
    credits_remaining: Optional[int] = None

    class Config:
        use_enum_values = True

    def append_message(self, message: ChatMessage) -> None:
        """Append a message to the conversation."""
        self.messages.append(message)

    def get_last_assistant_message(self) -> Optional[ChatMessage]:
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


class ChatStreamEvent(BaseModel):
    """Chat stream event model."""
    event_type: ChatEventType
    payload: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
