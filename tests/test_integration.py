"""Integration tests for external APIs (only run with real API keys)."""

import pytest
from unittest.mock import patch

from config import config
from src.services.ai_service import AIService
from src.services.memory_service import MemoryService
from src.services.auth_service import AuthService
from src.services.agent_service import ChatAgent


@pytest.mark.skipif(
    not config.deepseek_api_key,
    reason="DEEPSEEK_API_KEY not set - skipping integration tests"
)
class TestAIServiceIntegration:
    """Integration tests for AI service with real API calls."""

    @pytest.fixture
    def ai_service(self):
        """Real AI service instance."""
        return AIService()

    @pytest.mark.asyncio
    async def test_real_stream_chat_with_agent(self, ai_service):
        """Test streaming chat with real agent."""
        if not ai_service.agent:
            pytest.skip("Pydantic AI agent not available")

        chunks = []
        async for chunk in ai_service.stream_chat("Hello, this is a test message"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert any("Hello" in chunk or "test" in chunk for chunk in chunks)

    @pytest.mark.asyncio
    async def test_real_stream_chat_fallback(self, ai_service):
        """Test streaming chat with fallback API."""
        # Force fallback by disabling agent
        ai_service.agent = None

        chunks = []
        async for chunk in ai_service.stream_chat("Hello from fallback API"):
            chunks.append(chunk)

        assert len(chunks) > 0
        # Should not contain error messages
        assert not any("not configured" in chunk for chunk in chunks)


@pytest.mark.skipif(
    not config.heysol_api_key,
    reason="HEYSOL_API_KEY not set - skipping integration tests"
)
class TestMemoryServiceIntegration:
    """Integration tests for memory service with real API calls."""

    @pytest.fixture
    def memory_service(self):
        """Real memory service instance."""
        auth_service = AuthService(config.memory)
        return MemoryService(auth_service)

    @pytest.mark.asyncio
    async def test_real_memory_search(self, memory_service):
        """Test real memory search."""
        result = await memory_service.search("test query", limit=5)
        # Result should be valid even if empty
        assert hasattr(result, 'episodes')
        assert isinstance(result.episodes, list)

    @pytest.mark.asyncio
    async def test_real_memory_add(self, memory_service):
        """Test real memory addition."""
        episode = await memory_service.add(
            "Integration test memory entry",
            source="test"
        )
        assert episode.episode_id
        assert episode.body == "Integration test memory entry"

    @pytest.mark.asyncio
    async def test_real_list_spaces(self, memory_service):
        """Test real space listing."""
        spaces = await memory_service.list_spaces()
        assert isinstance(spaces, list)
        # Should have at least some spaces or empty list
        for space in spaces:
            assert space.space_id
            assert space.name


@pytest.mark.skipif(
    not config.deepseek_api_key,
    reason="DEEPSEEK_API_KEY not set - skipping integration tests"
)
@pytest.mark.skipif(
    not config.heysol_api_key,
    reason="HEYSOL_API_KEY not set - skipping integration tests"
)
class TestChatAgentIntegration:
    """Integration tests for chat agent with real APIs."""

    @pytest.fixture
    def chat_agent(self):
        """Real chat agent instance."""
        from src.services.memory_service import MemoryService
        from src.services.auth_service import AuthService

        auth_service = AuthService(config.memory)
        memory_service = MemoryService(auth_service)
        return ChatAgent(memory_service, config=config.llm)

    @pytest.mark.asyncio
    async def test_real_agent_generate(self, chat_agent):
        """Test real agent generation."""
        from src.models.chat import ConversationState

        conversation = ConversationState()
        result = await chat_agent.generate(conversation, "Hello, test message")

        assert result.reply
        assert isinstance(result.referenced_memories, list)

    @pytest.mark.asyncio
    async def test_real_agent_stream(self, chat_agent):
        """Test real agent streaming."""
        from src.models.chat import ConversationState

        conversation = ConversationState()
        events = []

        async for event_type, data in chat_agent.generate_stream(conversation, "Stream test"):
            events.append((event_type, data))

        assert len(events) > 0
        assert events[-1][0] == "final"


@pytest.mark.skipif(
    not config.deepseek_api_key or not config.heysol_api_key,
    reason="API keys not set - skipping full integration tests"
)
class TestFullChatFlowIntegration:
    """Full integration tests for the complete chat flow."""

    @pytest.mark.asyncio
    async def test_complete_chat_flow_with_real_services(self):
        """Test complete chat flow with real services."""
        from src.services.chat_service import ChatService
        from src.services.auth_service import AuthService
        from src.services.memory_service import MemoryService
        from src.models.chat import ConversationState

        # Set up real services
        auth_service = AuthService(config.memory)
        memory_service = MemoryService(auth_service)
        chat_service = ChatService(auth_service, memory_service, config)

        conversation = ConversationState()

        # Test streaming chat
        events = []
        async for event in chat_service.stream_chat(conversation, "Integration test message"):
            events.append(event)

        assert len(events) >= 3  # At least start, chunk, end
        assert conversation.status.value == "success"