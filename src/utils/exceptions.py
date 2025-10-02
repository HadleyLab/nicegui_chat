"""Custom exceptions for the NiceGUI Chat application."""


class AppError(Exception):
    """Base exception for application errors."""


class ConfigurationError(AppError):
    """Raised when configuration is invalid or missing."""


class AuthenticationError(AppError):
    """Raised when authentication fails or is required."""


class ChatServiceError(AppError):
    """Raised when chat service operations fail."""


class MemoryServiceError(AppError):
    """Raised when memory service operations fail."""
