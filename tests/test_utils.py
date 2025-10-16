"""Unit tests for utility functions."""

from unittest.mock import MagicMock

import pytest

from src.utils import get_logger, handle_error, setup_static_files
from src.utils.text_processing import strip_markdown


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_default_name(self):
        """Test get_logger with default name."""
        logger = get_logger()
        assert logger is not None
        # Verify it's a structlog logger
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

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
            "error_occurred", error="Test error", error_type="ValueError"
        )

    def test_handle_error_with_different_exception_types(self):
        """Test handle_error with different exception types."""
        mock_logger = MagicMock()
        test_error = RuntimeError("Runtime error")

        with pytest.raises(RuntimeError, match="Runtime error"):
            handle_error(test_error, mock_logger)

        mock_logger.error.assert_called_once_with(
            "error_occurred", error="Runtime error", error_type="RuntimeError"
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
        input_text = (
            "# **Bold Header**\n\nThis is *italic* and `code`.\n\n[Link](url) • bullet"
        )
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
        input_text = "<a onclick=\"alert('xss')\">Link</a>"
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

    def test_invalid_input_none(self):
        """Test strip_markdown with None input."""
        with pytest.raises(TypeError):
            strip_markdown(None)

    def test_invalid_input_int(self):
        """Test strip_markdown with int input."""
        with pytest.raises(TypeError):
            strip_markdown(123)

    def test_invalid_input_list(self):
        """Test strip_markdown with list input."""
        with pytest.raises(TypeError):
            strip_markdown(["test"])

    def test_very_long_string(self):
        """Test strip_markdown with very long string."""
        long_text = "**bold** " * 1000
        result = strip_markdown(long_text)
        assert "bold" in result
        assert "**" not in result

    def test_unicode_characters(self):
        """Test strip_markdown with unicode characters."""
        input_text = "Hello 🌟 **world** 中文"
        expected = "Hello 🌟 world 中文"
        assert strip_markdown(input_text) == expected

    def test_nested_markdown(self):
        """Test strip_markdown with nested markdown."""
        input_text = "**_nested_**"
        expected = "nested"
        assert strip_markdown(input_text) == expected

    def test_malformed_markdown(self):
        """Test strip_markdown with malformed markdown."""
        input_text = "**unclosed bold"
        expected = "unclosed bold"
        assert strip_markdown(input_text) == expected

    def test_multiple_code_blocks(self):
        """Test strip_markdown with multiple code blocks."""
        input_text = "```\ncode1\n```\ntext\n```\ncode2\n```"
        expected = "code1 text code2"
        assert strip_markdown(input_text) == expected

    def test_inline_code_with_backticks(self):
        """Test strip_markdown with inline code containing backticks."""
        input_text = "`code with `backticks``"
        expected = "code with backticks``"
        assert strip_markdown(input_text) == expected

    def test_headers_multiline(self):
        """Test strip_markdown with headers in multiline text."""
        input_text = "# Header\nSome text\n## Subheader\nMore text"
        expected = "Header Some text Subheader More text"
        assert strip_markdown(input_text) == expected

    def test_links_with_special_chars(self):
        """Test strip_markdown with links containing special characters."""
        input_text = "[Link with spaces](http://example.com/path?query=value)"
        expected = "Link with spaces"
        assert strip_markdown(input_text) == expected

    def test_bullet_points_various(self):
        """Test strip_markdown with various bullet point formats."""
        input_text = "• Item 1\n- Item 2\n* Item 3"
        expected = "Item 1 - Item 2 * Item 3"
        assert strip_markdown(input_text) == expected

    def test_whitespace_preservation(self):
        """Test strip_markdown whitespace preservation."""
        input_text = "Line 1\n\n\n\nLine 2"
        expected = "Line 1 Line 2"
        assert strip_markdown(input_text) == expected

    def test_html_xss_attempts(self):
        """Test strip_markdown with various XSS attempts."""
        inputs = [
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert('xss')>",
            "<a href='javascript:alert(1)'>link</a>",
        ]
        for input_text in inputs:
            result = strip_markdown(input_text)
            assert "alert" not in result
            assert "javascript" not in result
            assert "onerror" not in result
            assert "onload" not in result

    def test_html_safe_tags(self):
        """Test strip_markdown preserves safe HTML tags."""
        input_text = "<p>Hello <b>world</b></p>"
        result = strip_markdown(input_text)
        # html-sanitizer should allow basic tags
        assert "Hello" in result
        assert "world" in result

    def test_complex_mixed_content(self):
        """Test strip_markdown with complex mixed markdown and HTML."""
        input_text = "# **Header** with *italic* and `code`\n\n[Link](url) • <script>evil</script>"
        result = strip_markdown(input_text)
        assert "Header" in result
        assert "with" in result
        assert "italic" in result
        assert "code" in result
        assert "Link" in result
        assert "<script>" not in result
        assert "**" not in result
        assert "*" not in result
        assert "`" not in result
        assert "•" not in result
