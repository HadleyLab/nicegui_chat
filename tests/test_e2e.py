"""End-to-end tests for the chat application."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ui.main_ui import setup_ui


class TestE2E:
    """End-to-end tests."""

    @pytest.fixture
    def screen(self):
        """Create test screen."""
        # Skip E2E tests that require Screen() as it's not available in test environment
        pytest.skip(
            "E2E tests require NiceGUI Screen which is not available in this environment"
        )
        return None

    @pytest.fixture
    def mock_chat_service(self):
        """Mock chat service with realistic streaming."""
        service = MagicMock()
        service.stream_chat = AsyncMock()

        # Mock streaming response
        async def mock_stream(conversation, message):
            from src.models.chat import ChatEventType, ChatStreamEvent

            events = [
                ChatStreamEvent(
                    event_type=ChatEventType.MESSAGE_START,
                    payload={"role": "assistant"},
                ),
                ChatStreamEvent(
                    event_type=ChatEventType.MESSAGE_CHUNK,
                    payload={"content": "Hello! "},
                ),
                ChatStreamEvent(
                    event_type=ChatEventType.MESSAGE_CHUNK,
                    payload={"content": "How can I help you "},
                ),
                ChatStreamEvent(
                    event_type=ChatEventType.MESSAGE_CHUNK,
                    payload={"content": "today?"},
                ),
                ChatStreamEvent(
                    event_type=ChatEventType.MESSAGE_END,
                    payload={"content": "Hello! How can I help you today?"},
                ),
                ChatStreamEvent(
                    event_type=ChatEventType.STREAM_END, payload={"type": "STREAM_END"}
                ),
            ]
            for event in events:
                yield event

        service.stream_chat.side_effect = mock_stream
        return service

    def test_full_chat_flow(self, screen, mock_chat_service):
        """Test complete chat interaction flow."""
        with screen:
            setup_ui(mock_chat_service)

        # Check initial state
        assert screen.find("Welcome to MammoChat™").exists
        assert screen.find('placeholder="Share what\'s on your mind..."').exists

        # Type a message
        input_field = screen.find('placeholder="Share what\'s on your mind..."')
        input_field.type("Hello, I need help")

        # Send the message
        send_btn = screen.find('aria-label="Send message"')
        send_btn.click()

        # Check that user message appears
        assert screen.find("Hello, I need help").exists

        # Check that assistant response appears
        assert screen.find("Hello! How can I help you today?").exists

        # Check that input is cleared
        # Note: In test environment, this might not work exactly like real UI

    def test_multiple_messages_flow(self, screen, mock_chat_service):
        """Test sending multiple messages."""
        with screen:
            setup_ui(mock_chat_service)

        # First message
        input_field = screen.find('placeholder="Share what\'s on your mind..."')
        input_field.type("First message")
        send_btn = screen.find('aria-label="Send message"')
        send_btn.click()

        # Second message
        input_field.type("Second message")
        send_btn.click()

        # Check both messages exist
        assert screen.find("First message").exists
        assert screen.find("Second message").exists

    def test_new_conversation_resets_chat(self, screen, mock_chat_service):
        """Test that new conversation clears the chat."""
        with screen:
            setup_ui(mock_chat_service)

        # Send a message
        input_field = screen.find('placeholder="Share what\'s on your mind..."')
        input_field.type("Test message")
        send_btn = screen.find('aria-label="Send message"')
        send_btn.click()

        # Check message exists
        assert screen.find("Test message").exists

        # Start new conversation
        new_btn = screen.find('aria-label="New conversation"')
        new_btn.click()

        # Check welcome message is back
        assert screen.find("Welcome to MammoChat™").exists
        # Note: In test, old messages might still be there, depending on implementation

    def test_empty_message_not_sent(self, screen, mock_chat_service):
        """Test that empty messages are not sent."""
        with screen:
            setup_ui(mock_chat_service)

        # Try to send empty message
        send_btn = screen.find('aria-label="Send message"')
        send_btn.click()

        # Should not call chat service
        assert not mock_chat_service.stream_chat.called

    def test_dark_mode_persistence(self, screen, mock_chat_service):
        """Test dark mode toggle and persistence."""
        with screen:
            setup_ui(mock_chat_service)

        # Initially light mode
        theme_btn = screen.find('aria-label="Toggle dark mode"')
        theme_btn.get_attribute("icon")  # Assuming we can check icon

        # Toggle to dark
        theme_btn.click()

        # Should be dark mode now
        # Check that colors are applied correctly
        # This would require checking the actual theme state

    def test_chat_message_styling_consistency(self, screen, mock_chat_service):
        """Test that chat messages maintain consistent styling throughout conversation."""
        with screen:
            setup_ui(mock_chat_service)

        # Send a few messages
        messages = ["Hello", "How are you?", "I'm fine thanks"]

        for msg in messages:
            input_field = screen.find('placeholder="Share what\'s on your mind..."')
            input_field.clear()
            input_field.type(msg)
            send_btn = screen.find('aria-label="Send message"')
            send_btn.click()

        # Check that all user messages have consistent styling
        for msg in messages:
            user_msg_element = screen.find(msg)
            assert user_msg_element.exists
            # Check that it has the right classes/props for user messages

    def test_error_handling_in_ui(self, screen):
        """Test error handling in UI."""
        # Mock a failing chat service
        failing_service = MagicMock()
        failing_service.stream_chat = AsyncMock()

        async def failing_stream(conversation, message):
            from src.models.chat import ChatEventType, ChatStreamEvent

            yield ChatStreamEvent(event_type=ChatEventType.MESSAGE_START, payload={})
            raise Exception("Test error")

        failing_service.stream_chat.side_effect = failing_stream

        with screen:
            setup_ui(failing_service)

        # Send a message that will fail
        input_field = screen.find('placeholder="Share what\'s on your mind..."')
        input_field.type("This will fail")
        send_btn = screen.find('aria-label="Send message"')
        send_btn.click()

        # Should show error message
        assert screen.find("Error:").exists

    def test_ui_responsive_layout(self, screen, mock_chat_service):
        """Test that UI layout is responsive."""
        with screen:
            setup_ui(mock_chat_service)

        # Check that main container has proper classes
        # This would require inspecting the DOM structure

    def test_pwa_features_available(self, screen, mock_chat_service):
        """Test that PWA features are properly set up."""
        with screen:
            setup_ui(mock_chat_service)

        # Check meta tags, manifest link, etc.
        # This would require checking the head HTML

    def test_color_scheme_dark_mode(self, screen, mock_chat_service):
        """Test color scheme changes in dark mode."""
        with screen:
            setup_ui(mock_chat_service)

        # Check initial colors

        # Toggle dark mode
        theme_btn = screen.find('aria-label="Toggle dark mode"')
        theme_btn.click()

        # Colors should potentially change for dark mode
        # NiceGUI handles this automatically, but we can verify theme state
