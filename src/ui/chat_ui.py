"""Modern NiceGUI-based chat interface."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from uuid import uuid4

from nicegui import ui

# Configure logging for verbose output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from ..config import Config
from ..models.chat import ChatEventType, ConversationState
from ..services.auth_service import AuthService
from ..services.chat_service import ChatService
from ..services.memory_service import MemoryService

# Type aliases for NiceGUI elements
UIElement = Any  # NiceGUI elements don't have specific type annotations


class ChatUI:
    """Modern chat interface built with NiceGUI."""

    def __init__(
        self,
        config: Config,
        auth_service: AuthService,
        chat_service: ChatService,
        memory_service: MemoryService,
    ):
        start_time = time.time()
        logger.info("Initializing ChatUI...")

        self.config = config
        self.auth_service: AuthService = auth_service
        self.chat_service: ChatService = chat_service
        self.memory_service: MemoryService = memory_service
        self.conversation = ConversationState(conversation_id=str(uuid4()))
        self.is_streaming = False
        self.current_assistant_message: UIElement | None = None
        self.dark_mode = ui.dark_mode(value=False)  # Start in light mode
        self.dark_mode_button: UIElement | None = None  # Will hold the button reference
        self.header_row: UIElement | None = None  # Will hold the header reference
        self.header_subtitle: UIElement | None = None
        self.header_buttons: list[UIElement] = []  # Will hold button references

        init_time = time.time() - start_time
        logger.info(f"ChatUI initialized in {init_time:.3f}s with conversation ID: {self.conversation.conversation_id}")

    def build(self) -> None:
        """Build the main chat interface."""
        build_start = time.time()
        logger.info("Building chat interface...")

        # Set MammoChat colors using NiceGUI color system
        logger.debug("Setting custom color scheme")
        ui.colors(
            primary="#F4B8C5",  # Rose Quartz - soft pink
            secondary="#E8A0B8",  # Soft Mauve
            accent="#E8A0B8",  # Soft Mauve for accents
            dark="#334155",  # Charcoal for dark mode
            positive="#10b981",  # Default green for success
            negative="#ef4444",  # Default red for errors
            info="#3b82f6",  # Default blue for info
            warning="#f59e0b",  # Default amber for warnings
        )

        # Main content
        logger.debug("Creating main layout structure")
        with ui.column().classes("w-full h-screen gap-0"):
            # Header
            logger.debug("Building header section")
            self._build_header()

            # Chat messages container
            logger.debug("Creating chat scroll area and container")
            with ui.scroll_area().classes("flex-grow w-full p-4") as self.chat_scroll:
                self.chat_container = ui.column().classes(
                    "w-full max-w-4xl mx-auto gap-4"
                )

                # Add welcome message
                logger.debug("Adding welcome message")
                self._add_welcome_message()

            # Input area
            logger.debug("Building input area")
            self._build_input_area()

        build_time = time.time() - build_start
        logger.info(f"Chat interface built in {build_time:.3f}s")

    def _add_welcome_message(self) -> None:
        """Add the welcome message to the chat."""
        logger.debug("Adding welcome message to chat container")
        with self.chat_container:
            with ui.card().props("bordered"):
                with ui.row().classes("items-center gap-3"):
                    ui.html(
                        f'<img src="{self.config.ui_logo_icon_path}" style="height: 32px; width: auto;" />'
                    )
                    ui.label(self.config.ui_welcome_title).classes("text-xl font-bold")

                ui.markdown(self.config.ui_welcome_message)
        logger.debug("Welcome message added successfully")

    def _build_header(self) -> None:
        """Build the header section."""
        logger.debug("Building header section with logo and controls")
        with ui.card().classes("w-full").props("flat"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-3"):
                    # MammoChat logo
                    logger.debug("Adding MammoChat logo to header")
                    ui.html(
                        '<img src="/branding/logo-full-color.svg" style="height: 48px; width: auto;" />'
                    )
                    # Tagline - hidden on small screens
                    ui.label("Your journey, together").classes("gt-xs")

                with ui.row().classes("gap-2"):
                    logger.debug("Adding control buttons to header")
                    # Single dark mode toggle button
                    self.dark_mode_button = ui.button(
                        icon="light_mode", on_click=self._toggle_dark_mode
                    ).props("flat round")
                    self.dark_mode_button.tooltip(self.config.ui_dark_mode_tooltip)

                    ui.button(icon="refresh", on_click=self._new_conversation).props(
                        "flat round"
                    ).tooltip(self.config.ui_new_conversation_tooltip)
        logger.debug("Header section completed")


    def _toggle_dark_mode(self) -> None:
        """Toggle dark mode and update the button icon."""
        current_mode = "dark" if self.dark_mode.value else "light"
        new_mode = "light" if self.dark_mode.value else "dark"

        logger.info(f"Toggling dark mode: {current_mode} -> {new_mode}")

        if self.dark_mode.value:
            self.dark_mode.disable()
            if self.dark_mode_button:
                self.dark_mode_button.props(
                    remove="icon=dark_mode", add="icon=light_mode"
                )
                logger.debug("Dark mode disabled, light mode icon set")
        else:
            self.dark_mode.enable()
            if self.dark_mode_button:
                self.dark_mode_button.props(
                    remove="icon=light_mode", add="icon=dark_mode"
                )
                logger.debug("Dark mode enabled, dark mode icon set")

    def _build_input_area(self) -> None:
        """Build the input area."""
        logger.debug("Building input area with text field and send button")
        with ui.card().classes("w-full").props("flat"):
            with ui.row().classes("w-full p-2 gap-3 items-center max-w-4xl mx-auto"):
                self.input_field = (
                    ui.input(placeholder=self.config.ui_input_placeholder)
                    .props("outlined rounded dense")
                    .classes("flex-grow")
                    .on(
                        "keydown.enter",
                        lambda: self._send_message() if not self.is_streaming else None,
                    )
                )
                logger.debug("Input field created with enter key handler")

                # Send button
                ui.button(icon="send", on_click=self._send_message).props(
                    "round color=primary"
                ).tooltip(self.config.ui_send_tooltip)
        logger.debug("Input area completed")

    async def _send_message(self) -> None:
        """Send a message and handle the response using pure NiceGUI patterns."""
        send_start = time.time()
        logger.info("Starting message send process...")

        if self.is_streaming:
            logger.warning("Message send blocked - already streaming")
            ui.notify(
                "Please wait for the current response to complete", type="warning"
            )
            return

        message = self.input_field.value.strip()
        if not message:
            logger.warning("Empty message - user prompted to type message")
            ui.notify("Please type a message", type="warning")
            return

        logger.info(f"Processing user message: {len(message)} characters")
        message_content = message  # Store for logging

        # Clear input
        self.input_field.value = ""
        self.is_streaming = True
        logger.debug("Input cleared and streaming state set")

        # Display user message
        logger.debug("Displaying user message in chat")
        with self.chat_container, ui.row().classes("w-full justify-end"):
            with (
                ui.card().classes("max-w-[70%] bg-primary text-white").props("bordered")
            ):
                ui.label(message)

        # Scroll to bottom
        await asyncio.sleep(0.1)
        self.chat_scroll.scroll_to(pixels=10000)
        logger.debug("Scrolled to bottom after user message")

        # Show typing indicator
        logger.debug("Displaying typing indicator")
        with self.chat_container:
            typing_row = ui.row().classes("w-full")
            with typing_row, ui.card().props("flat"):
                with ui.row().classes("gap-2 items-center"):
                    ui.spinner("dots", size="sm", color="primary")
                    ui.label(self.config.ui_thinking_text)

        # Stream response
        assistant_content = ""
        assistant_label = None
        chunk_count = 0

        logger.info("Starting chat service stream...")
        try:
            async for event in self.chat_service.stream_chat(
                self.conversation,
                message,
                selected_space_ids=None,
            ):
                if event.event_type == ChatEventType.MESSAGE_START:
                    logger.debug("Received MESSAGE_START event")
                    # Remove typing indicator
                    typing_row.clear()
                    typing_row.delete()

                    # Create assistant message bubble
                    with self.chat_container, ui.row().classes("w-full"):
                        with ui.card().classes("max-w-[70%]").props("bordered"):
                            assistant_label = ui.markdown("")

                elif event.event_type == ChatEventType.MESSAGE_CHUNK:
                    chunk = event.payload.get("content", "")
                    assistant_content += chunk
                    chunk_count += 1
                    if assistant_label:
                        assistant_label.content = assistant_content

                    # Scroll to bottom
                    await asyncio.sleep(0.01)
                    self.chat_scroll.scroll_to(pixels=10000)
                    if chunk_count % 10 == 0:  # Log every 10 chunks
                        logger.debug(f"Processed {chunk_count} chunks, content length: {len(assistant_content)}")

                elif event.event_type == ChatEventType.MESSAGE_END:
                    logger.info(f"Message streaming completed - {chunk_count} chunks, {len(assistant_content)} total characters")
                    ui.notify(
                        self.config.ui_response_complete_notification,
                        type="positive",
                        position="top-right",
                        timeout=1000,
                    )

                elif event.event_type == ChatEventType.STEP:
                    logger.debug("Received STEP event from chat service")
                    # Handle memory references if needed
                    pass

        except Exception as e:
            logger.error(f"Error during message streaming: {e!s}", exc_info=True)
            # Show error message using notification
            ui.notify(f"Error: {e!s}", type="negative", position="top", timeout=5000)

            # Also display in chat
            with self.chat_container:
                with ui.row().classes("w-full"):
                    with (
                        ui.card()
                        .props("flat")
                        .classes(
                            "rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-6"
                        )
                    ):
                        ui.label(f"Error: {e!s}").classes(
                            "text-red-600 dark:text-red-400"
                        )

        finally:
            self.is_streaming = False
            send_time = time.time() - send_start
            logger.info(f"Message send completed in {send_time:.3f}s - {chunk_count} chunks processed")

    def _new_conversation(self) -> None:
        """Start a new conversation session."""
        old_conversation_id = self.conversation.conversation_id
        logger.info(f"Starting new conversation from {old_conversation_id[:8]}...")

        # Just refresh the conversation ID, keep the welcome message
        self.conversation = ConversationState(conversation_id=str(uuid4()))
        new_conversation_id = self.conversation.conversation_id

        logger.info(f"New conversation created: {old_conversation_id[:8]}... -> {new_conversation_id[:8]}...")
        ui.notify(
            self.config.ui_new_conversation_notification,
            type="positive",
            position="top-right",
        )
