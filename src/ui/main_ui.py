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
- Set up PWA features and static file serving

The UI follows a modular design where presentation logic is isolated from
service operations, enabling easy testing and maintenance.
"""

import structlog
from nicegui import ui

from config import config
from src.models.chat import ConversationState, MessageRole, ChatMessage
from src.services.chat_service import ChatService




def setup_ui(chat_service: ChatService) -> None:
    """Set up the main user interface for the MammoChat application.

    This function initializes the complete UI layout including:
    - Theme configuration and color schemes
    - PWA setup with manifest and service worker
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

    # Use NiceGUI's default dark mode functionality
    dark = ui.dark_mode()

    # Set comprehensive MammoChat colors for both light and dark themes
    # Set brand colors
    ui.colors(
        primary=scene["palette"]["primary"],
        secondary=scene["palette"]["secondary"],
        accent=scene["palette"]["accent"],
        positive=scene["status"]["positive"],
        negative=scene["status"]["negative"],
        info=scene["status"]["info"],
        warning=scene["status"]["warning"],
    )

    # Add PWA and Safari theming with brand colors
    ui.add_head_html(f"""
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="{scene['palette']['primary']}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="{config.app_name}">
        <link rel="apple-touch-icon" href="/branding/apple-touch-icon.png">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    """)

    conversation = ConversationState()

    async def send() -> None:
        """Handle sending a user message and processing the AI response."""
        question = text.value
        text.value = ""
        if not question.strip():
            return

        with message_container:
            with ui.row().classes('w-full justify-end'):
                ui.chat_message(text=question, sent=True).props('bg-color=primary text-color=white').classes('shadow-sm')
            with ui.row().classes('w-full justify-start'):
                response_message = ui.chat_message(sent=False).props('bg-color=accent text-color=dark').classes('shadow-sm')

        await ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

        with response_message:
            ui.spinner()

        response_content = ""
        try:
            async for event in chat_service.stream_chat(conversation, question):
                if event.event_type == "MESSAGE_CHUNK":
                    chunk = event.payload.get("content", "")
                    response_content += chunk
                    response_message.clear()
                    with response_message:
                        ui.markdown(response_content)
                    await ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")
        except Exception as e:
            logger.error("ai_response_failed", error=str(e))
            response_message.clear()
            with response_message:
                ui.label(f'Error: {str(e)}')

    def new_conversation() -> None:
        """Start a new conversation."""
        conversation.clear_messages()
        message_container.clear()
        with message_container:
            with ui.row().classes('w-full justify-start'):
                ui.chat_message(text=scene["chat"]["welcome_message"], sent=False).props('bg-color=accent text-color=dark').classes('shadow-sm')
        logger.info("new_conversation_started")

    # Clean header with white logo and visible tagline
    with ui.header().classes("q-header"):
        with ui.row().classes("w-full items-center justify-between px-2 sm:px-4 py-3 max-w-4xl mx-auto"):
            # Left side: Logo and tagline
            with ui.row().classes('items-center gap-2 sm:gap-3 flex-shrink-0'):
                ui.html(f'<img src="/branding/logo-full-white.svg" alt="MammoChat" class="h-10 flex-shrink-0">', sanitize=False).classes('flex-shrink-0'),
                ui.label('Your journey, together').classes('text-xs text-white opacity-75 leading-tight')

            # Right side: Theme toggle
            def toggle_theme():
                dark.toggle()
                theme_btn.icon = 'dark_mode' if dark.value else 'light_mode'

            # Right side - Clean controls
            with ui.row().classes('items-center gap-2'):
                theme_btn = ui.button(on_click=toggle_theme).props('flat dense color=white').classes('flex-shrink-0')
                theme_btn.icon = 'dark_mode' if dark.value else 'light_mode'

    # Chat Area
    with ui.column().classes(scene["chat"]["container_classes"]):
        message_container = ui.column().classes(scene["chat"]["message_container_classes"])
        with message_container:
            with ui.row().classes('w-full justify-start'):
                ui.chat_message(text=scene["chat"]["welcome_message"], sent=False).props('bg-color=accent text-color=dark').classes('shadow-sm')

    # Standard Footer
    with ui.footer().classes(f'{scene["footer"]["background"]} {scene["footer"]["border_top"]}'):
        with ui.row().classes(f'w-full max-w-2xl mx-auto {scene["footer"]["padding"]} items-center'):
            ui.button(icon="add", on_click=new_conversation, color='primary').props('flat round').classes('hover:scale-105 transition-transform').tooltip('New conversation')
            text = ui.input(placeholder="Share what's on your mind...").classes('flex-grow').props('filled dense').on("keydown.enter", send).tooltip('Type your message here')
            ui.button(icon="send", on_click=send).props('flat round color=primary').classes('hover:scale-105 transition-transform').tooltip('Send message')