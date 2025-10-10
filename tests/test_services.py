"""Unit tests for services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.chat import ConversationState, MessageRole
from src.services.agent_service import AgentDependencies, AgentOutput, AgentResult, ChatAgent
from src.services.ai_service import AIService
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.utils.exceptions import AuthenticationError, ChatServiceError


class TestAuthService:
    """Test AuthService."""

    def test_authenticated_with_api_key(self):
        """Test authentication when API key is present."""
        config = MagicMock()
        config.api_key = "test_key"
        config.base_url = "https://api.example.com"

        auth = AuthService(config)
        assert auth.is_authenticated is True
        assert auth.api_key == "test_key"
        assert auth.base_url == "https://api.example.com"

    def test_not_authenticated_without_api_key(self):
        """Test authentication when API key is missing."""
        config = MagicMock()
        config.api_key = None
        config.base_url = "https://api.example.com"

        auth = AuthService(config)
        assert auth.is_authenticated is False


class TestChatService:
    """Test ChatService."""

    @pytest.fixture
    def mock_config(self):
        """Mock config."""
        config = MagicMock()
        config.memory = MagicMock()
        config.memory.api_key = "test_key"
        config.chat_store_user_messages = True
        config.chat_enable_memory_enrichment = True
        config.chat_stream_chunk_size = 10
        return config

    @pytest.fixture
    def mock_auth_service(self):
        """Mock auth service."""
        auth = MagicMock()
        auth.is_authenticated = True
        return auth

    @pytest.fixture
    def mock_memory_service(self):
        """Mock memory service."""
        return MagicMock()

    @pytest.fixture
    def mock_agent(self):
        """Mock agent."""
        agent = MagicMock()
        agent.generate_stream = AsyncMock()
        return agent

    @pytest.fixture
    def chat_service(self, mock_auth_service, mock_memory_service, mock_config, mock_agent):
        """Create ChatService instance."""
        return ChatService(mock_auth_service, mock_memory_service, mock_config, mock_agent)

    @pytest.mark.asyncio
    async def test_stream_chat_success(self, chat_service, mock_agent):
        """Test successful chat streaming."""
        conversation = ConversationState()
        user_message = "Hello"

        # Mock agent stream
        async def mock_stream():
            yield "chunk", "Hi"
            yield "final", MagicMock(referenced_memories=["mem1"])

        mock_agent.generate_stream = mock_stream

        events = []
        async for event in chat_service.stream_chat(conversation, user_message):
            events.append(event)

        assert len(events) >= 3  # start, chunk, end, step, stream_end
        assert events[0].event_type.value == "MESSAGE_START"
        assert conversation.status.value == "success"

    @pytest.mark.asyncio
    async def test_stream_chat_not_authenticated(self, chat_service, mock_auth_service):
        """Test chat streaming when not authenticated."""
        mock_auth_service.is_authenticated = False
        conversation = ConversationState()

        with pytest.raises(AuthenticationError):
            async for _ in chat_service.stream_chat(conversation, "Hello"):
                pass

    @pytest.mark.asyncio
    async def test_stream_chat_empty_message(self, chat_service):
        """Test chat streaming with empty message."""
        conversation = ConversationState()

        with pytest.raises(ChatServiceError):
            async for _ in chat_service.stream_chat(conversation, ""):
                pass

    def test_chunk_reply(self, chat_service):
        """Test reply chunking."""
        reply = "This is a test message"
        chunks = chat_service._chunk_reply(reply)
        assert len(chunks) > 0
        assert "".join(chunks) == reply

    def test_chunk_reply_empty(self, chat_service):
        """Test chunking empty reply."""
        chunks = chat_service._chunk_reply("")
        assert chunks == []

    def test_chunk_reply_single_chunk(self, chat_service):
        """Test chunking with single chunk."""
        reply = "Short reply"
        chunks = chat_service._chunk_reply(reply)
        assert len(chunks) == 1
        assert chunks[0] == reply

    def test_chunk_reply_multiple_chunks(self, chat_service):
        """Test chunking with multiple chunks."""
        reply = "This is a longer reply that should be chunked into smaller pieces for streaming"
        chunks = chat_service._chunk_reply(reply)
        assert len(chunks) > 1
        assert "".join(chunks) == reply

    def test_chunk_reply_custom_chunk_size(self, chat_service):
        """Test chunking with custom chunk size."""
        # Create a service with different chunk size by mocking config
        with patch.object(chat_service, '_app_config') as mock_config:
            mock_config.chat_stream_chunk_size = 5
            reply = "HelloWorld"
            chunks = chat_service._chunk_reply(reply)
            assert len(chunks) == 2
            assert chunks[0] == "Hello"
            assert chunks[1] == "World"


class TestMemoryService:
    """Test MemoryService."""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock auth service."""
        auth = MagicMock()
        auth.is_authenticated = True
        auth.api_key = "test_key"
        auth.base_url = "https://api.example.com"
        return auth

    @pytest.fixture
    def memory_service(self, mock_auth_service):
        """Create MemoryService instance."""
        return MemoryService(mock_auth_service)

    @pytest.mark.asyncio
    async def test_search_success(self, memory_service):
        """Test successful memory search."""
        with patch("src.services.memory_service.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {"episodes": [], "total": 0}
            mock_client_class.return_value = mock_client

            result = await memory_service.search("test query")
            assert result is not None

    @pytest.mark.asyncio
    async def test_search_not_authenticated(self, memory_service, mock_auth_service):
        """Test search when not authenticated."""
        mock_auth_service.is_authenticated = False

        with pytest.raises(AuthenticationError):
            await memory_service.search("test")

    @pytest.mark.asyncio
    async def test_add_success(self, memory_service):
        """Test successful memory add."""
        with patch("src.services.memory_service.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.return_value = {"episode_id": "123"}
            mock_client_class.return_value = mock_client

            result = await memory_service.add("test message")
            assert result.episode_id == "123"
            assert result.body == "test message"

    @pytest.mark.asyncio
    async def test_list_spaces_success(self, memory_service):
        """Test successful list spaces."""
        with patch("src.services.memory_service.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_spaces.return_value = [{"id": "1", "name": "Test Space"}]
            mock_client_class.return_value = mock_client

            result = await memory_service.list_spaces()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_not_authenticated_duplicate(self, memory_service, mock_auth_service):
        """Test search when not authenticated (duplicate for coverage)."""
        mock_auth_service.is_authenticated = False

        with pytest.raises(AuthenticationError):
            await memory_service.search("test")

    @pytest.mark.asyncio
    async def test_add_not_authenticated(self, memory_service, mock_auth_service):
        """Test add when not authenticated."""
        mock_auth_service.is_authenticated = False

        with pytest.raises(AuthenticationError):
            await memory_service.add("test message")

    @pytest.mark.asyncio
    async def test_list_spaces_not_authenticated(self, memory_service, mock_auth_service):
        """Test list spaces when not authenticated."""
        mock_auth_service.is_authenticated = False

        with pytest.raises(AuthenticationError):
            await memory_service.list_spaces()

    @pytest.mark.asyncio
    async def test_search_with_exception(self, memory_service):
        """Test search with exception to cover error handling."""
        with patch("src.services.memory_service.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            with pytest.raises(ChatServiceError, match="Memory search failed"):
                await memory_service.search("test")

    @pytest.mark.asyncio
    async def test_add_with_exception(self, memory_service):
        """Test add with exception to cover error handling."""
        with patch("src.services.memory_service.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.ingest.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            with pytest.raises(ChatServiceError, match="Memory add failed"):
                await memory_service.add("test message")

    @pytest.mark.asyncio
    async def test_list_spaces_with_exception(self, memory_service):
        """Test list spaces with exception to cover error handling."""
        with patch("src.services.memory_service.HeySolClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_spaces.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            with pytest.raises(ChatServiceError, match="Failed to list memory spaces"):
                await memory_service.list_spaces()


class TestAIService:
    """Test AIService."""

    @pytest.fixture
    def mock_config(self):
        """Mock config."""
        config = MagicMock()
        config.deepseek_api_key = "test_key"
        config.deepseek_model = "test-model"
        config.deepseek_base_url = "https://api.example.com"
        config.heysol_api_key = "heysol_key"
        config.system_prompt = "You are a helpful assistant."
        return config

    @pytest.fixture
    def ai_service(self, mock_config):
        """Create AIService instance."""
        with patch("src.services.ai_service.HeySolClient"), \
             patch("src.services.ai_service.Agent"), \
             patch("src.services.ai_service.DeepSeekProvider"):
            return AIService()

    @pytest.mark.asyncio
    async def test_stream_chat_no_api_key(self, ai_service):
        """Test streaming without API key."""
        ai_service.api_key = None

        chunks = []
        async for chunk in ai_service.stream_chat("Hello"):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert "not configured" in chunks[0]

    @pytest.mark.asyncio
    async def test_stream_chat_with_agent(self, ai_service):
        """Test streaming with agent."""
        with patch.object(ai_service, "agent") as mock_agent:
            mock_result = MagicMock()
            mock_output = MagicMock()
            mock_output.reply = "Test response"
            mock_output.referenced_memories = []
            mock_result.output = mock_output
            mock_agent.run = AsyncMock(return_value=mock_result)

            chunks = []
            async for chunk in ai_service.stream_chat("Hello"):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert "Test response" in "".join(chunks)

    @pytest.mark.asyncio
    async def test_stream_chat_fallback_api(self, ai_service):
        """Test fallback to direct API."""
        ai_service.agent = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = AsyncMock(return_value=[
                'data: {"choices":[{"delta":{"content":"Hi"}}]}',
                'data: [DONE]'
            ])

            mock_client = MagicMock()
            mock_client.stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_client.stream.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            chunks = []
            async for chunk in ai_service.stream_chat("Hello"):
                chunks.append(chunk)

            assert "Hi" in "".join(chunks)

    @pytest.mark.asyncio
    async def test_stream_chat_agent_strips_markdown(self, ai_service):
        """Test that agent responses have markdown stripped."""
        with patch.object(ai_service, "agent") as mock_agent, \
             patch("src.services.ai_service.strip_markdown") as mock_strip:

            mock_result = MagicMock()
            mock_output = MagicMock()
            mock_output.reply = "**Bold** and *italic* text"
            mock_output.referenced_memories = []
            mock_result.output = mock_output
            mock_agent.run = AsyncMock(return_value=mock_result)

            mock_strip.return_value = "Bold and italic text"

            chunks = []
            async for chunk in ai_service.stream_chat("Hello"):
                chunks.append(chunk)

            # Verify strip_markdown was called with the markdown reply
            mock_strip.assert_called_once_with("**Bold** and *italic* text")
            # Verify the stripped text is yielded
            assert "Bold and italic text" in "".join(chunks)

    def test_ai_service_initialization_without_heysol(self, mock_config):
        """Test AI service initialization without HeySol client."""
        mock_config.heysol_api_key = None

        with patch("src.services.ai_service.HeySolClient") as mock_heysol, \
             patch("src.services.ai_service.Agent") as mock_agent, \
             patch("src.services.ai_service.DeepSeekProvider") as mock_provider:

            mock_heysol.return_value = None  # HeySol not available
            mock_agent.return_value = None  # Agent not available

            service = AIService()

            assert service.heysol_client is None
            assert service.agent is None

    def test_ai_service_initialization_with_heysol(self, mock_config):
        """Test AI service initialization with HeySol client."""
        mock_config.heysol_api_key = "test_key"

        with patch("src.services.ai_service.HeySolClient") as mock_heysol_class, \
             patch("src.services.ai_service.Agent") as mock_agent, \
             patch("src.services.ai_service.DeepSeekProvider") as mock_provider:

            mock_heysol_instance = MagicMock()
            mock_heysol_class.return_value = mock_heysol_instance
            mock_agent.return_value = None  # Agent not available

            service = AIService()

            mock_heysol_class.assert_called_once_with(api_key="test_key")
            assert service.heysol_client == mock_heysol_instance

    def test_ai_service_initialization_with_agent(self, mock_config):
        """Test AI service initialization with Pydantic AI agent."""
        with patch("src.services.ai_service.HeySolClient"), \
             patch("src.services.ai_service.Agent") as mock_agent_class, \
             patch("src.services.ai_service.DeepSeekProvider") as mock_provider_class, \
             patch("src.services.ai_service.OpenAIChatModel") as mock_model_class:

            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            service = AIService()

            # Verify agent initialization was attempted
            mock_provider_class.assert_called_once_with(api_key="test_key")
            mock_model_class.assert_called_once()
            mock_agent_class.assert_called_once()

    def test_ai_service_initialization_agent_failure(self, mock_config):
        """Test AI service initialization when agent creation fails."""
        with patch("src.services.ai_service.HeySolClient"), \
             patch("src.services.ai_service.Agent") as mock_agent_class:

            mock_agent_class.side_effect = Exception("Agent init failed")

            service = AIService()

            assert service.agent is None


class TestAgentService:
    """Test AgentService."""

    @pytest.fixture
    def mock_config(self):
        """Mock config."""
        config = MagicMock()
        config.api_key = "test_key"
        config.model = "test-model"
        config.system_prompt = "You are a helpful assistant. {tools}"
        config.ensure_valid = MagicMock()
        return config

    @pytest.fixture
    def mock_memory_service(self):
        """Mock memory service."""
        return MagicMock()

    @pytest.fixture
    def agent_service(self, mock_memory_service, mock_config):
        """Create ChatAgent instance."""
        with patch("src.services.agent_service.DeepSeekProvider"), \
             patch("src.services.agent_service.OpenAIChatModel"), \
             patch("src.services.agent_service.Agent"):
            return ChatAgent(mock_memory_service, config=mock_config)

    @pytest.mark.asyncio
    async def test_generate_success(self, agent_service):
        """Test successful generation."""
        conversation = ConversationState()

        with patch.object(agent_service._agent, "run") as mock_run:
            mock_result = MagicMock()
            mock_output = MagicMock()
            mock_output.reply = "Test reply"
            mock_output.referenced_memories = ["mem1"]
            mock_result.output = mock_output
            mock_run.return_value = mock_result

            result = await agent_service.generate(conversation, "Hello")
            assert result.reply == "Test reply"
            assert result.referenced_memories == ["mem1"]

    @pytest.mark.asyncio
    async def test_generate_stream_success(self, agent_service):
        """Test successful streaming generation."""
        conversation = ConversationState()

        with patch.object(agent_service._agent, "run_stream") as mock_run_stream:
            mock_output = MagicMock()
            mock_output.reply = "Test reply"
            mock_output.referenced_memories = ["mem1"]

            mock_result = MagicMock()
            mock_result.stream_output = AsyncMock(return_value=[mock_output])
            mock_run_stream.return_value.__aenter__ = AsyncMock(return_value=mock_result)
            mock_run_stream.return_value.__aexit__ = AsyncMock(return_value=None)

            events = []
            async for event_type, data in agent_service.generate_stream(conversation, "Hello"):
                events.append((event_type, data))

            assert len(events) >= 1
            assert events[-1][0] == "final"

    @pytest.mark.asyncio
    async def test_generate_stream_with_exception(self, agent_service):
        """Test streaming generation with exception to cover error handling."""
        conversation = ConversationState()

        with patch.object(agent_service._agent, "run_stream") as mock_run_stream:
            # Make run_stream raise an exception
            mock_run_stream.return_value.__aenter__.side_effect = Exception("Test error")
            mock_run_stream.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(ChatServiceError, match="Agent streaming failed"):
                async for _ in agent_service.generate_stream(conversation, "Hello"):
                    pass

    def test_build_system_prompt(self, agent_service):
        """Test building system prompt with tools."""
        prompt = agent_service._build_system_prompt()
        assert "memory_search" in prompt
        assert "memory_ingest" in prompt
        assert "{tools}" not in prompt  # Should be replaced

    def test_agent_initialization(self, mock_memory_service, mock_config):
        """Test agent initialization."""
        with patch("src.services.agent_service.DeepSeekProvider"), \
             patch("src.services.agent_service.OpenAIChatModel"), \
             patch("src.services.agent_service.Agent") as mock_agent_class:

            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = ChatAgent(mock_memory_service, config=mock_config)

            # Verify agent was created
            mock_agent_class.assert_called_once()
            assert agent._memory_service == mock_memory_service
            assert agent._config == mock_config

    def test_agent_dependencies_creation(self):
        """Test AgentDependencies model."""
        deps = AgentDependencies(selected_space_ids=["space1", "space2"])
        assert deps.selected_space_ids == ["space1", "space2"]

    def test_agent_output_creation(self):
        """Test AgentOutput model."""
        output = AgentOutput(
            reply="Test reply",
            referenced_memories=["mem1"],
            follow_up_actions=["action1"]
        )
        assert output.reply == "Test reply"
        assert output.referenced_memories == ["mem1"]
        assert output.follow_up_actions == ["action1"]

    def test_agent_result_creation(self):
        """Test AgentResult model."""
        result = AgentResult(reply="Reply", referenced_memories=["mem1"])
        assert result.reply == "Reply"
        assert result.referenced_memories == ["mem1"]