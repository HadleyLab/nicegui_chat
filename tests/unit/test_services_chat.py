"""Unit tests for chat service."""

from unittest.mock import MagicMock

import pytest

from src.services.chat_service import ChatService
from src.utils.exceptions import AuthenticationError, ChatServiceError


class TestChatService:
    """Test ChatService functionality."""

    def test_chat_service_init(self, mock_auth_service, mock_memory_service):
        """Test ChatService initialization."""
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(mock_auth_service, mock_memory_service, mock_config)
        assert service._auth_service == mock_auth_service
        assert service._memory_service == mock_memory_service
        assert service._app_config == mock_config
        # ensure_valid should be called during initialization
        assert mock_config.llm.ensure_valid.call_count >= 1

    @pytest.mark.asyncio
    async def test_stream_chat_not_authenticated(
        self, mock_memory_service, sample_conversation
    ):
        """Test stream_chat when not authenticated."""
        from src.config import HeysolConfig
        from src.services.auth_service import AuthService

        # Create an unauthenticated auth service
        config = HeysolConfig(api_key=None, base_url="https://test.com")
        unauth_auth_service = AuthService(config)

        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(unauth_auth_service, mock_memory_service, mock_config)

        with pytest.raises(AuthenticationError) as exc_info:
            async for _ in service.stream_chat(sample_conversation, "test message"):
                pass

        assert "Authentication is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stream_chat_empty_message(
        self, mock_auth_service, mock_memory_service, sample_conversation
    ):
        """Test stream_chat with empty message."""
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        with pytest.raises(ChatServiceError) as exc_info:
            async for _ in service.stream_chat(sample_conversation, ""):
                pass

        assert "Cannot send an empty message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stream_chat_whitespace_message(
        self, mock_auth_service, mock_memory_service, sample_conversation
    ):
        """Test stream_chat with whitespace-only message."""
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        with pytest.raises(ChatServiceError) as exc_info:
            async for _ in service.stream_chat(sample_conversation, "   "):
                pass

        assert "Cannot send an empty message" in str(exc_info.value)

    def test_chunk_reply_empty_string(self, mock_auth_service, mock_memory_service):
        """Test _chunk_reply with empty string."""
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.chat.stream_chunk_size = 10
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        result = service._chunk_reply("")
        assert result == []

    def test_chunk_reply_normal_chunking(self, mock_auth_service, mock_memory_service):
        """Test _chunk_reply with normal text."""
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.chat.stream_chunk_size = 3
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        result = service._chunk_reply("HelloWorld")
        assert result == ["Hel", "loW", "orl", "d"]

    def test_chunk_reply_chunk_size_larger_than_text(
        self, mock_auth_service, mock_memory_service
    ):
        """Test _chunk_reply when chunk size is larger than text."""
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.chat.stream_chunk_size = 100
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        result = service._chunk_reply("Hi")
        assert result == ["Hi"]

    def test_chunk_reply_chunk_size_zero(self, mock_auth_service, mock_memory_service):
        """Test _chunk_reply handles zero chunk size."""
        mock_config = MagicMock()
        mock_config.chat = MagicMock()
        mock_config.chat.stream_chunk_size = 0  # Should be clamped to 1
        mock_config.llm = MagicMock()
        mock_config.llm.ensure_valid = MagicMock()

        service = ChatService(mock_auth_service, mock_memory_service, mock_config)

        result = service._chunk_reply("ABC")
        assert result == ["A", "B", "C"]  # Each character as separate chunk
