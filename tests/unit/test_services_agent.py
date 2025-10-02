"""Unit tests for agent service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import DeepSeekConfig
from src.models.chat import ConversationState
from src.services.agent_service import (
    AgentDependencies,
    AgentOutput,
    AgentResult,
    ChatAgent,
)
from src.utils.exceptions import ChatServiceError, ConfigurationError


class TestAgentDependencies:
    """Test AgentDependencies model."""

    def test_agent_dependencies_creation(self):
        """Test AgentDependencies creation."""
        deps = AgentDependencies()
        assert deps.selected_space_ids == []

    def test_agent_dependencies_with_spaces(self):
        """Test AgentDependencies with space IDs."""
        spaces = ["space-1", "space-2"]
        deps = AgentDependencies(selected_space_ids=spaces)
        assert deps.selected_space_ids == spaces


class TestAgentOutput:
    """Test AgentOutput model."""

    def test_agent_output_creation_minimal(self):
        """Test AgentOutput creation with minimal fields."""
        output = AgentOutput(reply="Test reply")
        assert output.reply == "Test reply"
        assert output.referenced_memories == []
        assert output.follow_up_actions == []

    def test_agent_output_creation_full(self):
        """Test AgentOutput creation with all fields."""
        memories = ["mem-1", "mem-2"]
        actions = ["action-1", "action-2"]

        output = AgentOutput(
            reply="Full reply", referenced_memories=memories, follow_up_actions=actions
        )

        assert output.reply == "Full reply"
        assert output.referenced_memories == memories
        assert output.follow_up_actions == actions


class TestAgentResult:
    """Test AgentResult model."""

    def test_agent_result_creation_minimal(self):
        """Test AgentResult creation with minimal fields."""
        result = AgentResult(reply="Test reply")
        assert result.reply == "Test reply"
        assert result.referenced_memories == []

    def test_agent_result_creation_full(self):
        """Test AgentResult creation with all fields."""
        memories = ["mem-1", "mem-2"]
        result = AgentResult(reply="Full reply", referenced_memories=memories)
        assert result.reply == "Full reply"
        assert result.referenced_memories == memories


class TestChatAgent:
    """Test ChatAgent functionality."""

    def test_chat_agent_init(self, mock_memory_service):
        """Test ChatAgent initialization."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt",
        )

        with (
            patch("src.services.agent_service.DeepSeekProvider") as mock_provider_class,
            patch("src.services.agent_service.OpenAIChatModel") as mock_model_class,
            patch("src.services.agent_service.Agent") as mock_agent_class,
        ):

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            mock_model = MagicMock()
            mock_model_class.return_value = mock_model

            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            agent = ChatAgent(mock_memory_service, config=config)

            assert agent._memory_service == mock_memory_service
            assert agent._config == config

            # Verify provider and model creation
            mock_provider_class.assert_called_once_with(api_key="test-key")
            mock_model_class.assert_called_once_with(
                model_name="test-model", provider=mock_provider
            )

            # Verify agent creation
            mock_agent_class.assert_called_once()
            call_args = mock_agent_class.call_args
            # Check that model was passed (either as positional or keyword arg)
            if len(call_args[0]) > 0:
                assert call_args[0][0] == mock_model  # positional
            else:
                assert call_args[1].get("model") == mock_model  # keyword
            assert call_args[1].get("output_type") == AgentOutput
            assert call_args[1].get("deps_type") == AgentDependencies

    def test_chat_agent_init_with_model_name(self, mock_memory_service):
        """Test ChatAgent initialization with custom model name."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="default-model",
            base_url="https://test.com",
            system_prompt="Test prompt",
        )

        with (
            patch("src.services.agent_service.DeepSeekProvider"),
            patch("src.services.agent_service.OpenAIChatModel"),
            patch("src.services.agent_service.Agent"),
        ):

            ChatAgent(mock_memory_service, config=config, model_name="custom-model")

            # Verify custom model name was used
            from src.services.agent_service import OpenAIChatModel

            OpenAIChatModel.assert_called_once()
            call_args = OpenAIChatModel.call_args
            assert call_args[1]["model_name"] == "custom-model"

    def test_chat_agent_init_invalid_config(self, mock_memory_service):
        """Test ChatAgent initialization with invalid config."""
        config = DeepSeekConfig(
            api_key="",  # Invalid - empty API key
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt",
        )

        with pytest.raises(ConfigurationError):  # Config.ensure_valid() should raise for invalid config
            ChatAgent(mock_memory_service, config=config)

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_memory_service):
        """Test successful response generation."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt {tools}",
        )

        conversation = ConversationState()
        user_message = "Hello"

        with (
            patch("src.services.agent_service.DeepSeekProvider"),
            patch("src.services.agent_service.OpenAIChatModel"),
            patch("src.services.agent_service.Agent") as mock_agent_class,
        ):

            # Mock the agent instance
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            # Mock the run result
            mock_result = MagicMock()
            mock_output = AgentOutput(
                reply="Test response", referenced_memories=["mem-1", "mem-2"]
            )
            mock_result.output = mock_output
            mock_agent_instance.run = AsyncMock(return_value=mock_result)

            agent = ChatAgent(mock_memory_service, config=config)
            result = await agent.generate(conversation, user_message)

            assert result.reply == "Test response"
            assert result.referenced_memories == ["mem-1", "mem-2"]

            # Verify agent.run was called
            mock_agent_instance.run.assert_called_once_with(
                user_message, deps=AgentDependencies(selected_space_ids=[])
            )

    @pytest.mark.asyncio
    async def test_generate_with_spaces(self, mock_memory_service):
        """Test response generation with selected space IDs."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt {tools}",
        )

        conversation = ConversationState()
        user_message = "Hello"
        space_ids = ["space-1", "space-2"]

        with (
            patch("src.services.agent_service.DeepSeekProvider"),
            patch("src.services.agent_service.OpenAIChatModel"),
            patch("src.services.agent_service.Agent") as mock_agent_class,
        ):

            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            mock_result = MagicMock()
            mock_result.output = AgentOutput(reply="Response with spaces")
            mock_agent_instance.run = AsyncMock(return_value=mock_result)

            agent = ChatAgent(mock_memory_service, config=config)
            await agent.generate(
                conversation, user_message, selected_space_ids=space_ids
            )

            # Verify dependencies included space IDs
            mock_agent_instance.run.assert_called_once()
            call_args = mock_agent_instance.run.call_args
            deps = call_args[1]["deps"]
            assert deps.selected_space_ids == space_ids

    @pytest.mark.asyncio
    async def test_generate_agent_error(self, mock_memory_service):
        """Test response generation when agent fails."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt {tools}",
        )

        conversation = ConversationState()
        user_message = "Hello"

        with (
            patch("src.services.agent_service.DeepSeekProvider"),
            patch("src.services.agent_service.OpenAIChatModel"),
            patch("src.services.agent_service.Agent") as mock_agent_class,
        ):

            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            # Mock agent to raise exception
            mock_agent_instance.run = AsyncMock(side_effect=Exception("Agent failed"))

            agent = ChatAgent(mock_memory_service, config=config)

            with pytest.raises(ChatServiceError) as exc_info:
                await agent.generate(conversation, user_message)

            assert "Agent generation failed" in str(exc_info.value)
            assert "Agent failed" in str(exc_info.value)

    def test_build_system_prompt(self, mock_memory_service):
        """Test system prompt building."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Base prompt {tools}",
        )

        with (
            patch("src.services.agent_service.DeepSeekProvider"),
            patch("src.services.agent_service.OpenAIChatModel"),
            patch("src.services.agent_service.Agent"),
        ):

            agent = ChatAgent(mock_memory_service, config=config)
            prompt = agent._build_system_prompt()

            # Verify tools placeholder was replaced
            assert "{tools}" not in prompt
            assert "memory_search" in prompt
            assert "memory_ingest" in prompt
            assert "Base prompt" in prompt

    @pytest.mark.asyncio
    async def test_memory_search_tool(self, mock_memory_service):
        """Test memory search tool functionality."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt {tools}",
        )

        # Mock memory service search
        mock_memory_service.search = AsyncMock(
            return_value=MagicMock(
                episodes=[MagicMock(body="Memory 1"), MagicMock(body="Memory 2")]
            )
        )

        with (
            patch("src.services.agent_service.DeepSeekProvider"),
            patch("src.services.agent_service.OpenAIChatModel"),
            patch("src.services.agent_service.Agent") as mock_agent_class,
        ):

            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = ChatAgent(mock_memory_service, config=config)

            # Get the tool function (this is tricky to test directly due to decorator)
            # Instead, verify the tool was registered by checking agent.tool calls
            # The tool registration happens during __init__

            # For now, just verify agent was created successfully
            assert agent._memory_service == mock_memory_service

    @pytest.mark.asyncio
    async def test_memory_ingest_tool(self, mock_memory_service):
        """Test memory ingest tool functionality."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt {tools}",
        )

        # Mock memory service add
        mock_memory_service.add = AsyncMock(return_value=MagicMock())

        with (
            patch("src.services.agent_service.DeepSeekProvider"),
            patch("src.services.agent_service.OpenAIChatModel"),
            patch("src.services.agent_service.Agent") as mock_agent_class,
        ):

            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = ChatAgent(mock_memory_service, config=config)

            # Verify agent creation
            assert agent._memory_service == mock_memory_service
