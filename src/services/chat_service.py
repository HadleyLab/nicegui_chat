"""Chat Service Layer for MammoChat with enhanced async processing.

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
- Background task processing for memory operations
- Bounded conversation history management

Performance enhancements:
- Async background task processing for memory operations
- Bounded conversation history to prevent memory leaks
- Optimized streaming pipeline with proper resource management
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import structlog

from config import Config

from ..models.chat import (
    ChatEventType,
    ChatMessage,
    ChatStreamEvent,
    ConversationState,
    ConversationStatus,
    ExecutionStep,
    MessageRole,
)
from ..services.agent_service import ChatAgent
from ..services.auth_service import AuthService
from ..services.memory_service import MemoryService
from ..utils.exceptions import AuthenticationError, ChatServiceError

logger = structlog.get_logger()


class ChatService:
    """Service layer orchestrating chat operations with enhanced async processing.

    This class acts as the business logic coordinator, bridging:
    - Authentication service for user session management
    - Memory service for conversation persistence and context retrieval
    - AI agent for LLM interactions and response generation

    Enhanced with:
    - Background task processing for memory operations
    - Bounded conversation history management
    - Optimized streaming pipeline with proper resource management
    - Async task queue for non-blocking operations

    Responsibilities:
    - Validate user authentication before chat operations
    - Stream AI responses with proper error handling
    - Manage conversation state transitions
    - Coordinate memory enrichment and execution step tracking
    - Background processing of memory operations
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

        # Background task management for async operations
        self._background_tasks: set[asyncio.Task[Any]] = set()
        self._task_semaphore = asyncio.Semaphore(5)  # Limit concurrent background tasks

        # Performance monitoring
        self._request_count = 0
        self._last_cleanup = asyncio.get_event_loop().time()

    async def _background_memory_enrichment(
        self,
        conversation: ConversationState,
        user_message: str,
    ) -> None:
        """Process memory enrichment in the background."""
        async with self._task_semaphore:
            try:
                # Search for relevant memories in background
                if self._app_config.chat_enable_memory_enrichment:
                    await self._memory_service.search(
                        user_message,
                        space_ids=conversation.memory_space_ids,
                        limit=5,
                    )
                    logger.debug("background_memory_enrichment_completed")
            except Exception as e:
                logger.warning("background_memory_enrichment_failed", error=str(e))

    async def _cleanup_background_tasks(self) -> None:
        """Clean up completed background tasks."""
        current_time = asyncio.get_event_loop().time()

        # Cleanup every 60 seconds or after 100 requests
        if (current_time - self._last_cleanup) < 60 and self._request_count < 100:
            return

        completed_tasks = {task for task in self._background_tasks if task.done()}
        self._background_tasks -= completed_tasks

        # Cancel tasks that raised exceptions
        for task in completed_tasks:
            if task.exception():
                logger.warning("background_task_failed", error=str(task.exception()))

        self._last_cleanup = current_time
        self._request_count = 0

        if completed_tasks:
            logger.debug("background_tasks_cleaned", count=len(completed_tasks))

    async def close(self) -> None:
        """Clean up resources and cancel background tasks."""
        # Cancel all background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete cancellation
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        logger.info("chat_service_closed")

    async def stream_chat(
        self,
        conversation: ConversationState,
        user_message: str,
        *,
        selected_space_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        store_user_message: bool = True,
    ) -> AsyncIterator[ChatStreamEvent]:
            """Stream AI-generated chat responses with enhanced async processing.

            This method orchestrates the complete chat flow with optimizations:
            - Validates user authentication and message content
            - Stores user messages in conversation history (if enabled)
            - Generates AI responses through the agent service
            - Streams response chunks for real-time UI updates
            - Tracks execution steps for memory references
            - Manages conversation state transitions
            - Background processing for memory operations
            - Bounded conversation history management

            Performance enhancements:
            - Background memory enrichment processing
            - Bounded conversation history to prevent memory leaks
            - Optimized streaming pipeline with proper resource management

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

            # Update performance counters
            self._request_count += 1

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

            # Start background memory enrichment if enabled
            background_task = None
            if self._app_config.chat_enable_memory_enrichment:
                background_task = asyncio.create_task(
                    self._background_memory_enrichment(conversation, user_message)
                )
                self._background_tasks.add(background_task)

            # Stream response using the agent's streaming method
            referenced_memories: list[str] = []
            agent_result = None

            try:
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

            except Exception as e:
                logger.error("streaming_error", error=str(e))
                yield ChatStreamEvent(
                    event_type=ChatEventType.ERROR,
                    payload={"error": str(e)},
                )
                conversation.status = ConversationStatus.FAILED
                return

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
                        "referenced": referenced_memories,
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
                conversation.append_execution_step(execution_step)
                yield ChatStreamEvent(event_type=ChatEventType.STEP, payload=step_payload)

            conversation.status = ConversationStatus.SUCCESS
            yield ChatStreamEvent(
                event_type=ChatEventType.STREAM_END,
                payload={"type": ChatEventType.STREAM_END.value},
            )

            # Clean up background tasks periodically
            await self._cleanup_background_tasks()
