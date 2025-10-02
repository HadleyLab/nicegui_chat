"""Shared test fixtures and configuration."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_config_data():
    """Mock configuration data for testing."""
    return {
        "app": {
            "name": "Test MammoChat",
            "host": "127.0.0.1",
            "port": 8081,
            "reload": False,
        },
        "chat": {
            "enable_memory_enrichment": True,
            "store_user_messages": True,
            "stream_chunk_size": 50,
            "max_history_display": 50,
        },
        "llm": {"model": "deepseek-chat", "base_url": "https://api.deepseek.com"},
        "heysol": {"base_url": "https://core.heysol.ai/api/v1"},
        "prompts": {"root": "prompts", "system": "system"},
        "ui": {
            "theme": "dark",
            "primary_color": "#F4B8C5",
            "background_color": "#0f172a",
            "surface_color": "#1e293b",
            "text_color": "#e2e8f0",
            "accent_color": "#818cf8",
            "border_radius": "12px",
            "animation_duration": "0.3s",
            "tagline": "Your journey, together",
            "logo_full_path": "/branding/logo-full-color.svg",
            "logo_icon_path": "/branding/logo-icon.svg",
            "welcome_title": "Welcome to MammoChat",
            "welcome_message": "Test welcome message",
            "input_placeholder": "Type your message...",
            "thinking_text": "Thinking...",
            "send_tooltip": "Send Message",
            "dark_mode_tooltip": "Toggle Dark Mode",
            "new_conversation_tooltip": "New Conversation",
            "logout_tooltip": "Logout",
            "new_conversation_notification": "Started new conversation",
            "logout_notification": "Logged out successfully",
            "response_complete_notification": "Response complete",
        },
    }


@pytest.fixture
def temp_config_file(tmp_path, mock_config_data):
    """Create a temporary config file."""
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(mock_config_data, indent=2))
    return config_file


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "DEEPSEEK_API_KEY": "test_deepseek_key",
        "HEYSOL_API_KEY": "test_heysol_key",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_prompt_file(tmp_path):
    """Create a mock prompt file."""
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_file = prompt_dir / "system.md"
    prompt_file.write_text("You are a helpful AI assistant.")
    return prompt_dir


@pytest.fixture
def mock_heysol_client():
    """Mock HeySol client for testing."""
    client = MagicMock()
    client.search.return_value = {
        "episodes": [
            {
                "episode_id": "test-episode-1",
                "body": "Test memory content",
                "space_id": "test-space",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ],
        "total": 1,
    }
    client.ingest.return_value = {
        "episode_id": "new-episode-id",
        "id": "new-episode-id",
    }
    client.get_spaces.return_value = [
        {"space_id": "space-1", "name": "Test Space 1", "description": "A test space"}
    ]
    return client


@pytest.fixture
def mock_auth_service(mock_heysol_client):
    """Mock authentication service."""
    with patch("src.services.auth_service.HeySolClient") as mock_client_class:
        mock_client_class.return_value = mock_heysol_client
        from src.config import HeysolConfig
        from src.services.auth_service import AuthService

        config = HeysolConfig(
            api_key="test-key", base_url="https://test.heysol.ai/api/v1"
        )
        service = AuthService(config)
        yield service


@pytest.fixture
def mock_memory_service(mock_auth_service):
    """Mock memory service."""
    from src.services.memory_service import MemoryService

    return MemoryService(mock_auth_service)


@pytest.fixture
def mock_agent():
    """Mock chat agent."""
    agent = MagicMock()
    agent.generate.return_value = MagicMock(
        reply="Test response", referenced_memories=["memory-1"]
    )
    return agent


@pytest.fixture
def sample_conversation():
    """Sample conversation state for testing."""
    from src.models.chat import ChatMessage, ConversationState, MessageRole

    conversation = ConversationState(conversation_id="test-conv-123")
    conversation.append_message(
        ChatMessage(role=MessageRole.USER, content="Hello, how are you?")
    )
    conversation.append_message(
        ChatMessage(role=MessageRole.ASSISTANT, content="I'm doing well, thank you!")
    )
    return conversation


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    from src.models.chat import ChatMessage, MessageRole

    return ChatMessage(role=MessageRole.USER, content="Test message content")


@pytest.fixture
def sample_memory_episode():
    """Sample memory episode for testing."""
    from src.models.memory import MemoryEpisode

    return MemoryEpisode(
        episode_id="test-episode-123", body="Test memory content", space_id="test-space"
    )


@pytest.fixture
def sample_memory_search_result():
    """Sample memory search result for testing."""
    from src.models.memory import MemoryEpisode, MemorySearchResult

    return MemorySearchResult(
        episodes=[
            MemoryEpisode(
                episode_id="episode-1", body="First memory", space_id="space-1"
            ),
            MemoryEpisode(
                episode_id="episode-2", body="Second memory", space_id="space-1"
            ),
        ],
        total=2,
    )
