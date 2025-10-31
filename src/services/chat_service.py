"""Chat orchestration leveraging a local Pydantic AI agent."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from ..config import AppConfig, ChatConfig
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


class ChatService:
    """Coordinates persistence, MCP memory and the local DeepSeek-backed agent."""

    def __init__(
        self,
        auth_service: AuthService,
        memory_service: MemoryService,
        app_config: AppConfig,
        agent: ChatAgent | None = None,
    ) -> None:
        self._auth_service = auth_service
        self._memory_service = memory_service
        self._app_config = app_config
        self._chat_config: ChatConfig = app_config.chat
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
        """Stream chat responses from the agent."""
        # Allow demo mode without authentication
        demo_mode = not self._app_config.llm.api_key

        if not demo_mode and not self._auth_service.is_authenticated:
            raise AuthenticationError("Authentication is required")
        if not user_message.strip():
            raise ChatServiceError("Cannot send an empty message")

        conversation.status = ConversationStatus.RUNNING

        if store_user_message and self._chat_config.store_user_messages:
            user_chat_message = ChatMessage(
                message_id=str(uuid4()),
                role=MessageRole.USER,
                content=user_message,
            )
            conversation.append_message(user_chat_message)

        # Generate response using the agent or demo response
        if demo_mode:
            # Demo mode: return variable-length demo responses for UI testing
            import random
            from dataclasses import dataclass

            demo_responses = [
                "**Demo Mode Active** 🎨\n\nThis is a short demo response to test the UI.",

                "**Demo Mode Active** 🎨\n\nThis is a medium-length demo response. It includes multiple sentences to help you test how the chat bubbles look with different amounts of content.\n\nYou can see how the gradient background appears with paragraphs and line breaks. The streaming effect should also be visible as this text appears character by character.",

                "**Demo Mode Active** 🎨\n\nThis is a longer demo response designed to test the UI with more substantial content. When you're building a chat interface, it's important to see how it handles various message lengths.\n\n### Key Features Being Tested:\n\n- **Gradient Background**: The pink-to-rose gradient should be clearly visible\n- **Text Readability**: White text on gradient background\n- **Message Bubbles**: Rounded corners and proper spacing\n- **Streaming Effect**: Watch as text appears gradually\n\nThe MammoChat interface uses a beautiful design with glassmorphism effects, custom gradients, and smooth animations. This demo mode lets you test all these features without needing API credentials.\n\n### To Enable Full Functionality:\n\nAdd your `DEEPSEEK_API_KEY` to the `.env` file to connect to the AI service and get real responses!",

                "**Demo Response** ✨\n\nHere's another example with **markdown formatting**:\n\n1. First item\n2. Second item\n3. Third item\n\nThis helps test how lists appear in the chat bubbles with the gradient background.",

                "**Short test** 👋\n\nJust a quick message to verify the UI handles brief responses elegantly.",
            ]

            @dataclass
            class DemoResult:
                reply: str
                referenced_memories: list = None

                def __post_init__(self):
                    if self.referenced_memories is None:
                        self.referenced_memories = []

            # Pick a random response for variety
            agent_result = DemoResult(reply=random.choice(demo_responses))
        else:
            # Generate response using the agent
            agent_result = await self._agent.generate(
                conversation,
                user_message,
                selected_space_ids=selected_space_ids,
                metadata=metadata,
                prefetch_memory=self._chat_config.enable_memory_enrichment,
            )

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

        # In demo mode, add a delay before streaming to show the thinking indicator
        if demo_mode:
            import asyncio
            await asyncio.sleep(2.0)  # 2 second delay to see the thinking indicator

        # Stream the response in chunks
        for chunk in self._chunk_reply(agent_result.reply):
            assistant_message.content += chunk
            yield ChatStreamEvent(
                event_type=ChatEventType.MESSAGE_CHUNK, payload={"content": chunk}
            )
            # In demo mode, add small delays between chunks for realistic streaming effect
            if demo_mode:
                import asyncio
                await asyncio.sleep(0.03)  # 30ms delay between chunks

        yield ChatStreamEvent(
            event_type=ChatEventType.MESSAGE_END,
            payload={"content": assistant_message.content},
        )

        # Add execution steps for memory references
        if agent_result.referenced_memories:
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
        """Chunk the reply for streaming."""
        if not reply:
            return []
        step = max(self._chat_config.stream_chunk_size, 1)
        return [reply[i : i + step] for i in range(0, len(reply), step)]
