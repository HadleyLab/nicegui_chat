"""User Interface Layer for MammoChat.

This module implements the presentation layer of the MammoChat application,
providing a web-based chat interface using the NiceGUI framework. It handles
user interactions, message display, and UI state management while maintaining
clear separation from business logic and data persistence.

Key responsibilities:
- Render chat messages with proper styling and theming
- Handle user input and send messages to the chat service
- Manage conversation state and UI updates
- Provide theme-aware styling for light/dark modes
- Set up static file serving

The UI follows a modular design where presentation logic is isolated from
service operations, enabling easy testing and maintenance.
"""

import asyncio

import structlog
from nicegui import ui

from config import config
from src.models.chat import ConversationState
from src.services.chat_service import ChatService


def setup_colors(scene):
    ui.colors(
        primary=scene["palette"]["primary"],
        secondary=scene["palette"]["secondary"],
        accent=scene["palette"]["accent"],
        positive=scene["status"]["positive"],
        negative=scene["status"]["negative"],
        info=scene["status"]["info"],
        warning=scene["status"]["warning"],
    )


def setup_head_html(scene):
    ui.add_head_html(
        f"""
        <meta name="theme-color" content="{scene['palette']['primary']}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="apple-touch-icon" href="/branding/apple-touch-icon.png">
        <link rel="manifest" href="/manifest.json">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            .q-message--received {{
                max-height: none !important;
                overflow: visible !important;
            }}
        </style>
    """
    )


def create_header(scene, dark):
    header = ui.header().classes(
        f"{scene['header']['fixed_classes']} {scene['header']['classes']}"
    )
    with header:
        with ui.row().classes(scene["header"]["row_classes"]):
            with ui.row().classes(scene["header"]["logo_row_classes"]):
                ui.html(
                    f'<img src="{scene["logo"]["src"]}" alt="{scene["logo"]["alt"]}" class="{scene["logo"]["classes"]}">',
                    sanitize=False,
                ),
                ui.label(scene["header"]["tagline"]).classes(
                    scene["header"]["tagline_classes"]
                )

            def toggle_theme():
                dark.toggle()
                theme_btn.icon = "dark_mode" if dark.value else "light_mode"

            with ui.row().classes("items-center gap-2"):
                theme_btn = (
                    ui.button(on_click=toggle_theme)
                    .props(scene["header"]["theme_btn_props"])
                    .classes(scene["header"]["theme_btn_classes"])
                )
                theme_btn.icon = "dark_mode" if dark.value else "light_mode"

    return header


def create_chat_area(scene, conversation):
    with ui.column().classes(scene["layout"]["root_classes"]):
        with ui.column().classes(f"{scene['chat']['container_classes']}"):
            message_container = ui.column().classes(
                f"{scene['chat']['message_container_classes']}"
            )
            with message_container:
                with ui.row().classes(scene["chat"]["assistant_row_classes"]):
                    ui.chat_message(
                        text=scene["chat"]["welcome_message"], sent=False
                    ).props(scene["chat"]["welcome_message_props"]).classes(
                        scene["chat"]["welcome_message_classes"]
                    )
    return message_container


def create_footer(scene, send, new_conversation):
    with ui.footer().classes(
        f'{scene["footer"]["fixed_classes"]} {scene["footer"]["classes"]}'
    ):
        with ui.row().classes(scene["footer"]["row_classes"]):
            ui.button(icon="add", on_click=new_conversation, color="primary").props(
                scene["footer"]["new_btn_props"]
            ).classes(scene["footer"]["new_btn_classes"]).tooltip(
                scene["footer"]["new_btn_tooltip"]
            )
            text = (
                ui.input(placeholder=scene["footer"]["input_placeholder"])
                .classes(scene["footer"]["input_classes"])
                .props(scene["footer"]["input_props"])
                .on("keydown.enter", send)
                .tooltip(scene["footer"]["input_tooltip"])
            )
            send_btn = (
                ui.button(icon="send", on_click=send)
                .props(scene["footer"]["send_btn_props"])
                .classes(scene["footer"]["send_btn_classes"])
                .tooltip(scene["footer"]["send_btn_tooltip"])
            )
    return text, send_btn


def setup_ui(chat_service: ChatService) -> None:
    """Set up the main user interface for the MammoChat application.

    This function initializes the complete UI layout including:
    - Theme configuration and color schemes
    - Header with branding and dark mode toggle
    - Message display area with chat bubbles
    - Input controls for sending messages
    - Event handlers for user interactions

    The UI is designed to be responsive and theme-aware, supporting
    both light and dark modes with consistent MammoChat branding.

    Args:
        chat_service: The chat service instance for handling message operations.
    """
    logger = structlog.get_logger()

    logger.info("page_loaded", path="/")

    scene = config.scene

    dark = ui.dark_mode()

    setup_colors(scene)
    setup_head_html(scene)

    conversation = ConversationState()

    async def send() -> None:
        """Handle sending a user message and processing the AI response."""
        question = text.value
        text.value = ""
        if not question.strip():
            return

        text.disable()
        send_btn.disable()

        with message_container:
            with ui.row().classes(scene["chat"]["user_row_classes"]):
                ui.chat_message(text=question, sent=True).props(
                    scene["chat"]["user_message_props"]
                ).classes(scene["chat"]["user_message_classes"])
            with ui.row().classes(scene["chat"]["assistant_row_classes"]):
                response_message = (
                    ui.chat_message(sent=False)
                    .props(scene["chat"]["assistant_message_props"])
                    .classes(scene["chat"]["assistant_message_classes"])
                )

        with response_message:
            ui.spinner()

        # Use NiceGUI's native task processing with refreshable UI
        response_state = {"content": "", "error": None}

        @ui.refreshable
        def response_display():
            """Refreshable UI component for streaming response."""
            if response_state["error"]:
                ui.label(f"Error: {response_state['error']}").classes("text-left text-red-500")
            elif not response_state["content"]:
                ui.spinner()
            else:
                ui.label(response_state["content"]).classes("text-left")

        # Clear and show initial spinner
        response_message.clear()
        with response_message:
            response_display()

        async def stream_worker():
            """NiceGUI native worker for streaming chat responses."""
            try:
                async for event in chat_service.stream_chat(conversation, question):
                    if event.event_type == "MESSAGE_CHUNK":
                        chunk = event.payload.get("content", "")
                        response_state["content"] += chunk
                        # Refresh the UI component
                        response_display.refresh()
                    elif event.event_type == "MESSAGE_END":
                        # Final refresh
                        response_display.refresh()
            except Exception as e:
                logger.error("ai_response_failed", error=str(e))
                response_state["error"] = str(e)
                response_display.refresh()
            finally:
                # Re-enable UI controls
                text.enable()
                send_btn.enable()

        # Start the worker using NiceGUI's task system
        ui.timer(0.1, lambda: asyncio.create_task(stream_worker()), once=True)

    def new_conversation() -> None:
        """Start a new conversation."""
        conversation.clear_messages()
        message_container.clear()
        with message_container:
            with ui.row().classes(scene["chat"]["assistant_row_classes"]):
                ui.chat_message(
                    text=scene["chat"]["welcome_message"], sent=False
                ).props(scene["chat"]["welcome_message_props"]).classes(
                    scene["chat"]["welcome_message_classes"]
                )
        logger.info("new_conversation_started")

    create_header(scene, dark)
    message_container = create_chat_area(scene, conversation)
    text, send_btn = create_footer(scene, send, new_conversation)
