"""Integration tests for chat functionality."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.chat import ConversationState, MessageRole
from src.services.chat_service import ChatService


class TestChatIntegration:
    """Integration tests for chat service functionality."""

    @pytest.mark.asyncio
    async def test_chat_service_full_integration(
        self, mock_auth_service, mock_memory_service
    ):
        """Test full chat service integration with mocked agent."""
        # Create config
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.chat.store_user_messages = True
        mock_config.chat.enable_memory_enrichment = False
        mock_config.chat.stream_chunk_size = 10
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        # Create service
        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        # Mock the agent
        mock_agent_result = MagicMock()
        mock_agent_result.reply = "Hello from agent"
        mock_agent_result.referenced_memories = []
        service._agent.generate = AsyncMock(return_value=mock_agent_result)

        # Create conversation
        conversation = ConversationState()

        # Test the stream_chat method
        events = []
        async for event in service.stream_chat(conversation, "Hello"):
            events.append(event)

        # Verify conversation was updated
        assert conversation.status.value == "success"
        assert len(conversation.messages) == 2  # user + assistant
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[1].role == MessageRole.ASSISTANT
        assert conversation.messages[1].content == "Hello from agent"

        # Verify events were generated
        # "Hello from agent" (15 chars) with chunk_size=10 produces 2 chunks
        assert len(events) == 5  # START, CHUNK(1), CHUNK(2), END, STREAM_END

    @pytest.mark.asyncio
    async def test_chat_service_with_memory_integration(
        self, mock_auth_service, mock_memory_service
    ):
        """Test chat service with memory integration."""
        # Create config
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.chat.store_user_messages = True
        mock_config.chat.enable_memory_enrichment = True
        mock_config.chat.stream_chunk_size = 50
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        # Create service
        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        # Mock the agent with memory references
        mock_agent_result = MagicMock()
        mock_agent_result.reply = "Based on your memory"
        mock_agent_result.referenced_memories = ["mem-1", "mem-2"]
        service._agent.generate = AsyncMock(return_value=mock_agent_result)

        # Create conversation
        conversation = ConversationState()

        # Test the stream_chat method
        events = []
        async for event in service.stream_chat(conversation, "What do you remember?"):
            events.append(event)

        # Verify execution step was added
        assert len(conversation.execution_history) == 1
        step = conversation.execution_history[0]
        assert step.skill_name == "memory"
        assert step.status == "complete"
        assert step.data["observation"]["referenced"] == ["mem-1", "mem-2"]

    @pytest.mark.asyncio
    async def test_chat_service_chunking_integration(
        self, mock_auth_service, mock_memory_service
    ):
        """Test chat service response chunking."""
        # Create config with small chunk size
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.chat.store_user_messages = False
        mock_config.chat.enable_memory_enrichment = False
        mock_config.chat.stream_chunk_size = 3
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        # Create service
        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        # Mock the agent
        mock_agent_result = MagicMock()
        mock_agent_result.reply = "HelloWorld"
        mock_agent_result.referenced_memories = []
        service._agent.generate = AsyncMock(return_value=mock_agent_result)

        # Create conversation
        conversation = ConversationState()

        # Test the stream_chat method
        events = []
        async for event in service.stream_chat(conversation, "Test"):
            events.append(event)

        # Verify chunking worked
        from src.models.chat import ChatEventType

        chunk_events = [
            e for e in events if e.event_type == ChatEventType.MESSAGE_CHUNK
        ]
        assert len(chunk_events) == 4  # "Hel", "loW", "orl", "d"
        assert chunk_events[0].payload["content"] == "Hel"
        assert chunk_events[1].payload["content"] == "loW"
        assert chunk_events[2].payload["content"] == "orl"
        assert chunk_events[3].payload["content"] == "d"
