"""Chat Service Layer for MammoChat.

This module implements the business logic layer for chat operations,
serving as the orchestration point between:

- User interface (src/ui/) - handles presentation and user interaction
- Data persistence (src/services/memory_service.py) - manages conversation storage
- AI agent (src/services/agent_service.py) - handles LLM interactions
- Authentication (src/services/auth_service.py) - manages user sessions

The ChatService class coordinates streaming chat responses, message persistence,
and memory enrichment while maintaining clear separation of concerns. It acts
as the primary interface for chat-related operations in the application.

Key responsibilities:
- Stream chat responses from the AI agent
- Manage conversation state and message persistence
- Handle authentication and authorization
- Coordinate memory enrichment and context retrieval
- Process streaming events and error handling
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from config import Config
from ..models.chat import (ChatEventType, ChatMessage, ChatStreamEvent,
                           ConversationState, ConversationStatus,
                           ExecutionStep, MessageRole)
from ..services.agent_service import ChatAgent
from ..services.auth_service import AuthService
from ..services.memory_service import MemoryService
from ..utils.exceptions import AuthenticationError, ChatServiceError


class ChatService:
    """Service layer orchestrating chat operations with clear separation of concerns.

    This class acts as the business logic coordinator, bridging:
    - Authentication service for user session management
    - Memory service for conversation persistence and context retrieval
    - AI agent for LLM interactions and response generation

    Responsibilities:
    - Validate user authentication before chat operations
    - Stream AI responses with proper error handling
    - Manage conversation state transitions
    - Coordinate memory enrichment and execution step tracking
    - Ensure data consistency across chat sessions

    The service maintains no UI concerns, focusing purely on business logic
    and data orchestration to enable clean testing and reusability.
    """

    def __init__(
        self,
        auth_service: AuthService,
        memory_service: MemoryService,
        app_config: Config,
        agent: ChatAgent | None = None,
    ) -> None:
        self._auth_service = auth_service
        self._memory_service = memory_service
        self._app_config = app_config
        self._app_config.llm.ensure_valid()
        self._agent: ChatAgent = agent or ChatAgent(
            memory_service, config=app_config.llm
        )

    async def stream_chat(
        self,
        conversation: ConversationState,
        user_message: str,
        *,
        selected_space_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        store_user_message: bool = True,
    ) -> AsyncIterator[ChatStreamEvent]:
        """Stream AI-generated chat responses with proper state management.

        This method orchestrates the complete chat flow:
        - Validates user authentication and message content
        - Stores user messages in conversation history (if enabled)
        - Generates AI responses through the agent service
        - Streams response chunks for real-time UI updates
        - Tracks execution steps for memory references
        - Manages conversation state transitions

        The streaming approach enables responsive UI updates while maintaining
        clean separation between service logic and presentation concerns.

        Args:
            conversation: Current conversation state to update
            user_message: User's input message to process
            selected_space_ids: Optional memory space filtering
            metadata: Additional context for response generation
            store_user_message: Whether to persist user message in history

        Yields:
            ChatStreamEvent: Streaming events for UI consumption

        Raises:
            AuthenticationError: If user is not authenticated
            ChatServiceError: If message is empty or service fails
        """
        if not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication is required")
        if not user_message.strip():
            raise ChatServiceError("Cannot send an empty message")

        conversation.status = ConversationStatus.RUNNING

        if store_user_message and self._app_config.chat_store_user_messages:
            user_chat_message = ChatMessage(
                message_id=str(uuid4()),
                role=MessageRole.USER,
                content=user_message,
            )
            conversation.append_message(user_chat_message)

        assistant_message = ChatMessage(
            message_id=str(uuid4()),
            role=MessageRole.ASSISTANT,
            content="",
        )
        conversation.append_message(assistant_message)

        yield ChatStreamEvent(
            event_type=ChatEventType.MESSAGE_START,
            payload={"role": MessageRole.ASSISTANT.value},
        )

        # Stream response using the agent's streaming method
        referenced_memories: list[str] = []
        async for event_type, data in self._agent.generate_stream(
            conversation,
            user_message,
            selected_space_ids=selected_space_ids,
            metadata=metadata,
            prefetch_memory=self._app_config.chat_enable_memory_enrichment,
        ):
            if event_type == "chunk":
                chunk = data
                assistant_message.content += chunk
                yield ChatStreamEvent(
                    event_type=ChatEventType.MESSAGE_CHUNK, payload={"content": chunk}
                )
            elif event_type == "final":
                agent_result = data
                referenced_memories = agent_result.referenced_memories

        yield ChatStreamEvent(
            event_type=ChatEventType.MESSAGE_END,
            payload={"content": assistant_message.content},
        )

        # Add execution steps for memory references
        if referenced_memories:
            step_payload = {
                "skillName": "memory",
                "skillStatus": "complete",
                "userMessage": "",
                "observation": {
                    "referenced": agent_result.referenced_memories,
                },
            }
            execution_step = ExecutionStep(
                step_id=str(uuid4()),
                skill_name="memory",
                status="complete",
                observation=json.dumps(step_payload["observation"]),
                user_message="",
                data=step_payload,
            )
            conversation.execution_history.append(execution_step)
            yield ChatStreamEvent(event_type=ChatEventType.STEP, payload=step_payload)

        conversation.status = ConversationStatus.SUCCESS
        yield ChatStreamEvent(
            event_type=ChatEventType.STREAM_END,
            payload={"type": ChatEventType.STREAM_END.value},
        )

    def _chunk_reply(self, reply: str) -> list[str]:
        """Split AI response into chunks for streaming delivery.

        This method breaks down the complete AI response into smaller
        chunks to enable real-time streaming to the UI. The chunk size
        is configurable and ensures smooth, responsive user experience.

        Args:
            reply: The complete AI-generated response text

        Returns:
            List of text chunks for streaming, or empty list if reply is empty
        """
        if not reply:
            return []
        step = max(self._app_config.chat_stream_chunk_size, 1)
        return [reply[i : i + step] for i in range(0, len(reply), step)]
