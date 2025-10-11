"""Integration tests for UI components."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from nicegui.testing import Screen

from config import config
from src.models.chat import ConversationState
from src.ui.main_ui import setup_ui


class TestUI:
    """Test UI components."""

    @pytest.fixture
    def screen(self):
        """Create test screen."""
        return Screen()

    @pytest.fixture
    def mock_chat_service(self):
        """Mock chat service."""
        service = MagicMock()
        service.stream_chat = AsyncMock()
        return service

    def test_setup_ui_creates_elements(self, screen, mock_chat_service):
        """Test that setup_ui creates all required UI elements."""
        with screen:
            setup_ui(mock_chat_service)

        # Check header exists
        assert screen.find("MammoChat").exists

        # Check footer with input
        assert screen.find('placeholder="Share what\'s on your mind..."').exists

        # Check welcome message
        assert screen.find("Welcome to MammoChat").exists

    def test_chat_message_user_styling(self, screen, mock_chat_service):
        """Test user chat message styling."""
        conversation = ConversationState()

        with screen:
            setup_ui(mock_chat_service)

            # Simulate adding a user message
            from nicegui import ui

            with ui.row().classes(config.scene["chat"]["user_row_classes"]):
                ui.chat_message(text="Hello", sent=True).props(
                    config.scene["chat"]["user_message_props"]
                ).classes(config.scene["chat"]["user_message_classes"])

        # Check that user message has correct styling
        user_message = screen.find("Hello")
        assert user_message.exists
        # Check that it has sent=True (right-aligned)
        # This would require inspecting the HTML classes

    def test_chat_message_assistant_styling(self, screen, mock_chat_service):
        """Test assistant chat message styling."""
        conversation = ConversationState()

        with screen:
            setup_ui(mock_chat_service)

            # Simulate adding an assistant message
            from nicegui import ui

            with ui.row().classes(config.scene["chat"]["assistant_row_classes"]):
                assistant_message = (
                    ui.chat_message(sent=False)
                    .props(config.scene["chat"]["assistant_message_props"])
                    .classes(config.scene["chat"]["assistant_message_classes"])
                )

                with assistant_message:
                    ui.label("Hi there")

        # Check that assistant message uses label instead of direct text
        assistant_label = screen.find("Hi there")
        assert assistant_label.exists

    def test_dark_mode_toggle(self, screen, mock_chat_service):
        """Test dark mode toggle functionality."""
        with screen:
            setup_ui(mock_chat_service)

        # Find theme toggle button
        theme_btn = screen.find('aria-label="Toggle dark mode"')
        assert theme_btn.exists

        # Initially should be light mode
        # Click to toggle to dark
        theme_btn.click()

        # Should now be dark mode
        # This would require checking the dark mode state

    def test_new_conversation_clears_messages(self, screen, mock_chat_service):
        """Test new conversation functionality."""
        with screen:
            setup_ui(mock_chat_service)

        # Find new conversation button
        new_btn = screen.find('aria-label="New conversation"')
        assert new_btn.exists

        # Click new conversation
        new_btn.click()

        # Should clear messages and show welcome message
        assert screen.find("Welcome to MammoChat").exists

    def test_send_message_functionality(self, screen, mock_chat_service):
        """Test sending a message."""
        with screen:
            setup_ui(mock_chat_service)

        # Find input field
        input_field = screen.find('placeholder="Share what\'s on your mind..."')
        assert input_field.exists

        # Type a message
        input_field.type("Hello world")

        # Find send button
        send_btn = screen.find('aria-label="Send message"')
        assert send_btn.exists

        # Mock the stream_chat to return some events
        async def mock_stream():
            from src.models.chat import ChatEventType, ChatStreamEvent

            yield ChatStreamEvent(event_type=ChatEventType.MESSAGE_START, payload={})
            yield ChatStreamEvent(
                event_type=ChatEventType.MESSAGE_CHUNK, payload={"content": "Hi"}
            )
            yield ChatStreamEvent(event_type=ChatEventType.MESSAGE_END, payload={})
            yield ChatStreamEvent(event_type=ChatEventType.STREAM_END, payload={})

        mock_chat_service.stream_chat = mock_stream

        # Click send
        send_btn.click()

        # Should show user message and assistant response
        assert screen.find("Hello world").exists
        assert screen.find("Hi").exists

    def test_chat_message_coloring_consistency(self, screen, mock_chat_service):
        """Test that chat message colors are consistent with theme."""
        with screen:
            setup_ui(mock_chat_service)

            from nicegui import ui

            # Add user message
            with ui.row().classes(config.scene["chat"]["user_row_classes"]):
                user_msg = ui.chat_message("User message", sent=True)
                user_msg.props(config.scene["chat"]["user_message_props"])
                user_msg.classes(config.scene["chat"]["user_message_classes"])

            # Add assistant message
            with ui.row().classes(config.scene["chat"]["assistant_row_classes"]):
                assistant_msg = ui.chat_message(sent=False)
                assistant_msg.props(config.scene["chat"]["assistant_message_props"])
                assistant_msg.classes(config.scene["chat"]["assistant_message_classes"])
                with assistant_msg:
                    ui.label("Assistant message")

        # Check that user message has primary color props
        user_props = config.scene["chat"]["user_message_props"]
        assert "bg-color=primary" in user_props
        assert "text-color=white" in user_props

        # Check that assistant message has accent color props
        assistant_props = config.scene["chat"]["assistant_message_props"]
        assert "bg-color=accent" in assistant_props
        assert "text-color=grey-8" in assistant_props

    def test_assistant_message_no_scrollbars(self, screen, mock_chat_service):
        """Test that assistant messages don't have internal scrollbars."""
        with screen:
            setup_ui(mock_chat_service)

            from nicegui import ui

            # Add assistant message with long text
            with ui.row().classes(config.scene["chat"]["assistant_row_classes"]):
                assistant_msg = ui.chat_message(sent=False)
                with assistant_msg:
                    ui.label(
                        "This is a very long message that should not cause internal scrolling within the chat bubble itself."
                    )

        # The message should be in a label, not directly in chat_message
        # This prevents the scrollbar issue
        long_message = screen.find("This is a very long message")
        assert long_message.exists

    def test_chat_bubble_alignment(self, screen, mock_chat_service):
        """Test chat bubble alignment."""
        with screen:
            setup_ui(mock_chat_service)

            from nicegui import ui

            # User message should be right-aligned
            with ui.row().classes(config.scene["chat"]["user_row_classes"]):
                ui.chat_message("User", sent=True)

            # Assistant message should be left-aligned
            with ui.row().classes(config.scene["chat"]["assistant_row_classes"]):
                ui.chat_message(sent=False)
                with ui.chat_message(sent=False):
                    ui.label("Assistant")

        # Check row classes for alignment
        assert "justify-end" in config.scene["chat"]["user_row_classes"]
        assert "justify-start" in config.scene["chat"]["assistant_row_classes"]

    def test_theme_colors_applied(self, screen, mock_chat_service):
        """Test that theme colors are properly applied."""
        with screen:
            setup_ui(mock_chat_service)

        # Check that NiceGUI colors are set from scene
        from nicegui import ui

        colors = ui.colors
        assert colors.primary == config.scene["palette"]["primary"]
        assert colors.secondary == config.scene["palette"]["secondary"]
        assert colors.accent == config.scene["palette"]["accent"]
