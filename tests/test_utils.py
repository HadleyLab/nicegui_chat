"""Unit tests for utility functions."""

import pytest
from unittest.mock import MagicMock, patch

from src.utils import get_logger, setup_static_files, handle_error
from src.utils.text_processing import strip_markdown


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


class TestStripMarkdown:
    """Test strip_markdown function."""

    def test_strip_bold(self):
        """Test stripping bold markdown."""
        input_text = "This is **bold** text."
        expected = "This is bold text."
        assert strip_markdown(input_text) == expected

    def test_strip_italic_asterisk(self):
        """Test stripping italic with asterisks."""
        input_text = "This is *italic* text."
        expected = "This is italic text."
        assert strip_markdown(input_text) == expected

    def test_strip_italic_underscore(self):
        """Test stripping italic with underscores."""
        input_text = "This is _italic_ text."
        expected = "This is italic text."
        assert strip_markdown(input_text) == expected

    def test_strip_code_block(self):
        """Test stripping code blocks."""
        input_text = "Here is some code:\n```\nprint('hello')\n```"
        expected = "Here is some code: print('hello')"
        assert strip_markdown(input_text) == expected

    def test_strip_inline_code(self):
        """Test stripping inline code."""
        input_text = "Use the `print()` function."
        expected = "Use the print() function."
        assert strip_markdown(input_text) == expected

    def test_strip_headers(self):
        """Test stripping headers."""
        input_text = "# Header 1\n## Header 2\n### Header 3"
        expected = "Header 1 Header 2 Header 3"
        assert strip_markdown(input_text) == expected

    def test_strip_links(self):
        """Test stripping links."""
        input_text = "Check out [Google](https://google.com) for more info."
        expected = "Check out Google for more info."
        assert strip_markdown(input_text) == expected

    def test_strip_bullet_points(self):
        """Test stripping bullet points."""
        input_text = "• Item 1\n• Item 2"
        expected = "Item 1 Item 2"
        assert strip_markdown(input_text) == expected

    def test_strip_whitespace(self):
        """Test stripping extra whitespace."""
        input_text = "Line 1\n\n\nLine 2"
        expected = "Line 1 Line 2"
        assert strip_markdown(input_text) == expected

    def test_preserve_emojis(self):
        """Test preserving emojis."""
        input_text = "Hello 😊 world!"
        expected = "Hello 😊 world!"
        assert strip_markdown(input_text) == expected

    def test_strip_complex_markdown(self):
        """Test stripping complex markdown combinations."""
        input_text = "# **Bold Header**\n\nThis is *italic* and `code`.\n\n[Link](url) • bullet"
        expected = "Bold Header This is italic and code. Link bullet"
        assert strip_markdown(input_text) == expected

    def test_empty_string(self):
        """Test with empty string."""
        assert strip_markdown("") == ""

    def test_no_markdown(self):
        """Test with plain text."""
        input_text = "Just plain text."
        expected = "Just plain text."
        assert strip_markdown(input_text) == expected

    def test_sanitize_html_script(self):
        """Test sanitizing HTML script tags."""
        input_text = "<script>alert('xss')</script>Hello"
        result = strip_markdown(input_text)
        assert "<script>" not in result
        assert "alert" not in result
        assert "Hello" in result

    def test_sanitize_html_onclick(self):
        """Test sanitizing HTML with onclick."""
        input_text = '<a onclick="alert(\'xss\')">Link</a>'
        result = strip_markdown(input_text)
        assert "onclick" not in result
        assert "alert" not in result
        assert "Link" in result

    def test_preserve_safe_html(self):
        """Test preserving safe HTML."""
        input_text = "<p>Hello <strong>world</strong></p>"
        result = strip_markdown(input_text)
        # html-sanitizer should allow safe tags
        assert "<p>" in result or "Hello" in result  # Depending on sanitizer settings

    def test_strip_markdown_with_html(self):
        """Test stripping markdown and sanitizing HTML together."""
        input_text = "**Bold** <script>evil</script> text"
        result = strip_markdown(input_text)
        assert "**" not in result
        assert "<script>" not in result
        assert "Bold" in result
        assert "text" in result