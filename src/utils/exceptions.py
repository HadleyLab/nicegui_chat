"""Custom Exception Hierarchy for MammoChat.

This module defines the application's exception hierarchy, implementing
a structured error handling system that supports the fail-fast philosophy.
All exceptions inherit from AppError and are categorized by domain:

- AppError: Base exception for all application errors
- ConfigurationError: Invalid or missing configuration
- AuthenticationError: Authentication and authorization failures
- ChatServiceError: Chat service operation failures
- MemoryServiceError: Memory service operation failures

This hierarchy enables precise error handling and logging while maintaining
clear separation of concerns across the modular architecture.
"""


class AppError(Exception):
    """Base exception for all application errors.

    This is the root exception class for the MammoChat application.
    All custom exceptions inherit from this class to enable unified
    error handling and logging across the modular architecture.
    """


class ConfigurationError(AppError):
    """Raised when application configuration is invalid or missing.

    This exception is thrown during application startup when required
    configuration values (like API keys, endpoints, or settings) are
    not properly set or are malformed. It prevents the application
    from running with incorrect configuration.
    """


class AuthenticationError(AppError):
    """Raised when user authentication fails or is required but not provided.

    This exception is thrown when attempting to access protected resources
    without proper authentication credentials. It ensures that sensitive
    operations like chat interactions require valid user sessions.
    """


class ChatServiceError(AppError):
    """Raised when chat service operations encounter errors.

    This exception is thrown when the chat service fails to process
    user messages, generate AI responses, or handle streaming operations.
    It ensures that chat-related failures are properly categorized and
    handled within the service layer.
    """


class MemoryServiceError(AppError):
    """Raised when memory service operations encounter errors.

    This exception is thrown when the memory service fails to store,
    retrieve, or manage conversation data and user memories. It ensures
    that memory-related failures are properly categorized and handled
    within the persistence layer.
    """
