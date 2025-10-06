"""Tests for the MammoChat NiceGUI 3 ChatUI implementation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.config import AppConfig
from src.models.chat import ChatEventType, ChatStreamEvent, ConversationState
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.ui.chat_ui import ChatUI


@pytest.fixture
def mock_config() -> AppConfig:
    """Create a mock AppConfig with UI defaults."""
    config = Mock(spec=AppConfig)
    ui_config = Mock()
    ui_config.theme = "dark"
    ui_config.logo_full_path = "/branding/logo-full-color.svg"
    ui_config.logo_icon_path = "/branding/logo-icon.svg"
    ui_config.tagline = "Your journey, together"
    ui_config.welcome_title = "Welcome to MammoChat"
    ui_config.welcome_message = "We are here to support you."
    ui_config.dark_mode_tooltip = "Toggle dark mode"
    ui_config.new_conversation_tooltip = "Start a new conversation"
    ui_config.input_placeholder = "Type your message..."
    ui_config.send_tooltip = "Send"
    ui_config.thinking_text = "Thinking..."
    ui_config.response_complete_notification = "Response complete"
    ui_config.new_conversation_notification = "New conversation started"
    config.ui = ui_config
    return config


@pytest.fixture
def mock_auth_service() -> AuthService:
    service = Mock(spec=AuthService)
    service.is_authenticated = True
    return service


@pytest.fixture
def mock_chat_service() -> ChatService:
    return Mock(spec=ChatService)


@pytest.fixture
def mock_memory_service() -> MemoryService:
    return Mock(spec=MemoryService)


@pytest.fixture
def chat_ui(
    mock_config: AppConfig,
    mock_auth_service: AuthService,
    mock_chat_service: ChatService,
    mock_memory_service: MemoryService,
) -> ChatUI:
    return ChatUI(
        config=mock_config,
        auth_service=mock_auth_service,
        chat_service=mock_chat_service,
        memory_service=mock_memory_service,
    )


def test_initial_state(chat_ui: ChatUI) -> None:
    """The ChatUI should start with unbound UI elements."""
    assert isinstance(chat_ui.conversation, ConversationState)
    assert chat_ui.message_container is None
    assert chat_ui.chat_scroll is None
    assert chat_ui.input_field is None
    assert chat_ui.send_button is None
    assert chat_ui.dark_mode is None
    assert chat_ui.dark_mode_button is None


@patch("src.ui.chat_ui.ui.column")
@patch("src.ui.chat_ui.ui.dark_mode")
def test_build_invokes_sections(
    mock_dark_mode: MagicMock,
    mock_column: MagicMock,
    chat_ui: ChatUI,
) -> None:
    """Building the UI should configure styling and layout sections."""
    column_context = MagicMock()
    column_context.__enter__.return_value = column_context
    column_context.__exit__.return_value = None
    mock_column.return_value = column_context

    dark_mode_handle = MagicMock()
    mock_dark_mode.return_value = dark_mode_handle

    chat_ui._build_header = Mock()
    chat_ui._build_message_panel = Mock()
    chat_ui._build_input_panel = Mock()

    chat_ui.build()
    mock_dark_mode.assert_called_once_with(value=True)
    dark_mode_handle.enable.assert_called_once()
    chat_ui._build_header.assert_called_once()
    chat_ui._build_message_panel.assert_called_once()
    chat_ui._build_input_panel.assert_called_once()


def test_toggle_dark_mode_from_dark(chat_ui: ChatUI) -> None:
    """Toggling dark mode when enabled should disable it and update the icon."""
    chat_ui.dark_mode = MagicMock()
    chat_ui.dark_mode.value = True
    chat_ui.dark_mode_button = MagicMock()

    chat_ui._toggle_dark_mode()

    chat_ui.dark_mode.disable.assert_called_once()
    chat_ui.dark_mode_button.props.assert_called_once_with("icon=dark_mode")


def test_toggle_dark_mode_from_light(chat_ui: ChatUI) -> None:
    """Toggling dark mode when disabled should enable it and update the icon."""
    chat_ui.dark_mode = MagicMock()
    chat_ui.dark_mode.value = False
    chat_ui.dark_mode_button = MagicMock()

    chat_ui._toggle_dark_mode()

    chat_ui.dark_mode.enable.assert_called_once()
    chat_ui.dark_mode_button.props.assert_called_once_with("icon=light_mode")


@patch("src.ui.chat_ui.ui.notify")
def test_new_conversation_resets_state(
    mock_notify: MagicMock,
    chat_ui: ChatUI,
    mock_config: AppConfig,
) -> None:
    """Starting a new conversation should reset state and show welcome."""
    message_column = MagicMock()
    message_column.clear = MagicMock()
    message_column.__enter__.return_value = message_column
    message_column.__exit__.return_value = None
    chat_ui.message_container = message_column
    chat_ui._render_welcome_message = Mock()

    previous_id = chat_ui.conversation.conversation_id

    chat_ui._new_conversation()

    assert chat_ui.conversation.conversation_id != previous_id
    message_column.clear.assert_called_once()
    chat_ui._render_welcome_message.assert_called_once()
    mock_notify.assert_called_once_with(
        mock_config.ui.new_conversation_notification,
        type="positive",
        position="top-right",
    )


@pytest.mark.asyncio
async def test_handle_enter_key_without_shift(chat_ui: ChatUI) -> None:
    """Pressing enter without shift should trigger send."""
    chat_ui._send_message = AsyncMock()
    event = Mock()
    event.shift = False

    await chat_ui._handle_enter_key(event)

    chat_ui._send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_enter_key_with_shift(chat_ui: ChatUI) -> None:
    """Pressing enter with shift should do nothing."""
    chat_ui._send_message = AsyncMock()
    event = Mock()
    event.shift = True

    await chat_ui._handle_enter_key(event)

    chat_ui._send_message.assert_not_called()


@pytest.mark.asyncio
@patch("src.ui.chat_ui.ui.notify")
async def test_send_message_blocks_when_streaming(
    mock_notify: MagicMock,
    chat_ui: ChatUI,
) -> None:
    """Sending while already streaming should warn and return."""
    chat_ui.input_field = MagicMock()
    chat_ui.is_streaming = True

    await chat_ui._send_message()

    mock_notify.assert_called_once_with(
        "Please wait for the current response to complete",
        type="warning",
    )


@pytest.mark.asyncio
@patch("src.ui.chat_ui.ui.notify")
async def test_send_message_requires_content(
    mock_notify: MagicMock,
    chat_ui: ChatUI,
) -> None:
    """Empty messages prompt the user to type something."""
    chat_ui.input_field = MagicMock()
    chat_ui.input_field.value = "   "
    chat_ui.is_streaming = False

    await chat_ui._send_message()

    mock_notify.assert_called_once_with("Please type a message", type="warning")


@pytest.mark.asyncio
async def test_send_message_stream_success(chat_ui: ChatUI, mock_config: AppConfig) -> None:
    """A full streaming cycle should update the assistant markdown and notify completion."""
    chat_ui.input_field = MagicMock()
    chat_ui.input_field.value = "Hello"
    chat_ui.send_button = MagicMock()
    chat_ui._render_user_message = Mock()
    chat_ui._show_typing_indicator = Mock()
    chat_ui._clear_typing_indicator = Mock()
    assistant_markdown = MagicMock()
    chat_ui._render_assistant_message = Mock(return_value=(None, assistant_markdown))
    chat_ui._render_step_details = Mock()
    chat_ui._show_error_message = Mock()
    chat_ui._scroll_to_bottom = AsyncMock()

    events = [
        ChatStreamEvent(event_type=ChatEventType.MESSAGE_START, payload={}),
        ChatStreamEvent(event_type=ChatEventType.MESSAGE_CHUNK, payload={"content": "Hi"}),
        ChatStreamEvent(event_type=ChatEventType.MESSAGE_END, payload={"content": "Hi"}),
        ChatStreamEvent(event_type=ChatEventType.STREAM_END, payload={}),
    ]
    stream_calls: list[tuple[ConversationState, str, list[str] | None]] = []

    async def stream(
        conversation: ConversationState,
        message: str,
        *,
        selected_space_ids: list[str] | None = None,
    ):
        stream_calls.append((conversation, message, selected_space_ids))
        for event in events:
            yield event

    chat_ui.chat_service.stream_chat = stream

    with patch("src.ui.chat_ui.ui.notify") as mock_notify:
        await chat_ui._send_message()

    assert stream_calls and stream_calls[0][1] == "Hello"
    assert assistant_markdown.content == "Hi"
    mock_notify.assert_called_with(
        mock_config.ui.response_complete_notification,
        type="positive",
        position="top-right",
        timeout=1000,
    )
    chat_ui.input_field.enable.assert_called_once()
    chat_ui.input_field.focus.assert_called_once()
    chat_ui.send_button.enable.assert_called_once()
    chat_ui._clear_typing_indicator.assert_called()
    assert chat_ui.is_streaming is False


@pytest.mark.asyncio
async def test_send_message_error_path(chat_ui: ChatUI) -> None:
    """Errors during streaming should surface through the error handler."""
    chat_ui.input_field = MagicMock()
    chat_ui.input_field.value = "Hello"
    chat_ui.send_button = MagicMock()
    chat_ui._render_user_message = Mock()
    chat_ui._show_typing_indicator = Mock()
    chat_ui._clear_typing_indicator = Mock()
    chat_ui._render_assistant_message = Mock(return_value=(None, MagicMock()))
    chat_ui._render_step_details = Mock()
    chat_ui._scroll_to_bottom = AsyncMock()
    chat_ui._show_error_message = Mock()

    async def stream_error(*_args, **_kwargs):
        raise RuntimeError("boom")
        yield  # pragma: no cover - mark as async generator

    chat_ui.chat_service.stream_chat = stream_error

    with patch("src.ui.chat_ui.ui.notify"):
        await chat_ui._send_message()

    chat_ui._show_error_message.assert_called_once_with("boom")
    chat_ui.input_field.enable.assert_called_once()
    chat_ui.send_button.enable.assert_called_once()


@patch("src.ui.chat_ui.ui.notify")
@patch("src.ui.chat_ui.ui.chat_message")
def test_show_error_message_renders_bubble(
    mock_chat_message: MagicMock,
    mock_notify: MagicMock,
    chat_ui: ChatUI,
) -> None:
    """Error helper should emit a notification and render a chat bubble."""
    message_container = MagicMock()
    message_container.__enter__.return_value = message_container
    message_container.__exit__.return_value = None
    chat_ui.message_container = message_container

    chat_ui._show_error_message("Something went wrong")

    mock_notify.assert_called_once()
    mock_chat_message.assert_called_once()
    message_container.__enter__.assert_called_once()


def test_toggle_dark_mode_without_button(chat_ui: ChatUI) -> None:
    """Toggling dark mode without a button should not raise."""
    chat_ui.dark_mode = MagicMock()
    chat_ui.dark_mode.value = False
    chat_ui.dark_mode_button = None

    chat_ui._toggle_dark_mode()

    chat_ui.dark_mode.enable.assert_called_once()
