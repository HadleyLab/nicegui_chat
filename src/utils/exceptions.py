"""Custom exceptions for the NiceGUI Chat application."""


class AppError(Exception):
    """Base exception for application errors."""
    pass


class ConfigurationError(AppError):
    """Raised when configuration is invalid or missing."""
    pass


class AuthenticationError(AppError):
    """Raised when authentication fails or is required."""
    pass


class ChatServiceError(AppError):
    """Raised when chat service operations fail."""
    pass


class MemoryServiceError(AppError):
    """Raised when memory service operations fail."""
    pass
