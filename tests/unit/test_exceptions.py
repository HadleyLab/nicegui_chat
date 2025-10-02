"""Unit tests for custom exceptions."""

import pytest

from src.utils.exceptions import (
    AppError,
    AuthenticationError,
    ChatServiceError,
    ConfigurationError,
    MemoryServiceError,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_app_error_base_class(self):
        """Test AppError base exception."""
        error = AppError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        error = ConfigurationError("Config file not found")
        assert str(error) == "Config file not found"
        assert isinstance(error, AppError)
        assert isinstance(error, Exception)

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, AppError)
        assert isinstance(error, Exception)

    def test_chat_service_error(self):
        """Test ChatServiceError exception."""
        error = ChatServiceError("Chat service failed")
        assert str(error) == "Chat service failed"
        assert isinstance(error, AppError)
        assert isinstance(error, Exception)

    def test_memory_service_error(self):
        """Test MemoryServiceError exception."""
        error = MemoryServiceError("Memory service failed")
        assert str(error) == "Memory service failed"
        assert isinstance(error, AppError)
        assert isinstance(error, Exception)

    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from AppError."""
        exceptions = [
            ConfigurationError("test"),
            AuthenticationError("test"),
            ChatServiceError("test"),
            MemoryServiceError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AppError)
            assert isinstance(exc, Exception)

    def test_exception_with_custom_message(self):
        """Test exceptions with custom messages."""
        custom_messages = [
            "Configuration validation failed",
            "API key is invalid",
            "Chat streaming error",
            "Memory search timeout",
        ]

        exception_classes = [
            ConfigurationError,
            AuthenticationError,
            ChatServiceError,
            MemoryServiceError,
        ]

        for exc_class, message in zip(exception_classes, custom_messages):
            error = exc_class(message)
            assert str(error) == message

    def test_exception_inheritance_depth(self):
        """Test exception inheritance depth."""
        # All should be AppError -> Exception -> BaseException
        error = ConfigurationError("test")
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, AppError)
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)

    def test_exception_raising(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Test config error")

        assert str(exc_info.value) == "Test config error"
        assert isinstance(exc_info.value, ConfigurationError)
        assert isinstance(exc_info.value, AppError)

    def test_multiple_exception_types(self):
        """Test handling multiple exception types."""

        def raise_config_error():
            raise ConfigurationError("Config error")

        def raise_auth_error():
            raise AuthenticationError("Auth error")

        def raise_chat_error():
            raise ChatServiceError("Chat error")

        def raise_memory_error():
            raise MemoryServiceError("Memory error")

        # Test each exception type can be raised and caught
        with pytest.raises(ConfigurationError):
            raise_config_error()

        with pytest.raises(AuthenticationError):
            raise_auth_error()

        with pytest.raises(ChatServiceError):
            raise_chat_error()

        with pytest.raises(MemoryServiceError):
            raise_memory_error()

    def test_exception_chaining(self):
        """Test exception chaining with cause."""
        original_error = ValueError("Original error")
        try:
            raise ConfigurationError("Config failed") from original_error
        except ConfigurationError as config_error:
            assert str(config_error) == "Config failed"
            assert config_error.__cause__ is original_error
            assert isinstance(config_error.__cause__, ValueError)
