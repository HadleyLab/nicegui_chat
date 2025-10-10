"""Unit tests for utility functions."""

import pytest
from unittest.mock import MagicMock, patch

from src.utils import get_logger, setup_static_files, handle_error


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_default_name(self):
        """Test get_logger with default name."""
        logger = get_logger()
        assert logger is not None
        # Verify it's a structlog logger
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')

    def test_get_logger_custom_name(self):
        """Test get_logger with custom name."""
        logger = get_logger("test_logger")
        assert logger is not None
        # The name is passed to structlog.get_logger


class TestSetupStaticFiles:
    """Test setup_static_files function."""

    def test_setup_static_files_mounts_branding(self):
        """Test that setup_static_files mounts branding directory."""
        mock_app = MagicMock()

        setup_static_files(mock_app)

        # Verify mount was called twice
        assert mock_app.mount.call_count == 2

        # Check first mount call (branding)
        calls = mock_app.mount.call_args_list
        assert calls[0][0][0] == "/branding"
        assert calls[0][0][1].directory == "branding"
        assert calls[0][1]["name"] == "branding"

        # Check second mount call (static)
        assert calls[1][0][0] == "/static"
        assert calls[1][0][1].directory == "branding"
        assert calls[1][1]["name"] == "static-branding"


class TestHandleError:
    """Test handle_error function."""

    def test_handle_error_logs_and_reraises(self):
        """Test that handle_error logs the error and re-raises it."""
        mock_logger = MagicMock()
        test_error = ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            handle_error(test_error, mock_logger)

        # Verify error was logged
        mock_logger.error.assert_called_once_with(
            "error_occurred",
            error="Test error",
            error_type="ValueError"
        )

    def test_handle_error_with_different_exception_types(self):
        """Test handle_error with different exception types."""
        mock_logger = MagicMock()
        test_error = RuntimeError("Runtime error")

        with pytest.raises(RuntimeError, match="Runtime error"):
            handle_error(test_error, mock_logger)

        mock_logger.error.assert_called_once_with(
            "error_occurred",
            error="Runtime error",
            error_type="RuntimeError"
        )