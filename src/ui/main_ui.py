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

import structlog
from nicegui import ui

from config import config
from src.models.chat import ConversationState
from src.services.chat_service import ChatService


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

    # Add Safari theming with brand colors
    ui.add_head_html(
        f"""
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            html, body {{
                overflow-x: hidden;
            }}
            .q-message--sent .q-message-bubble::after {{
                content: '';
                position: absolute;
                left: -8px;
                top: 12px;
                border: 8px solid transparent;
                border-right-color: var(--q-primary);
                border-left: 0;
            }}
            .q-message--received .q-message-bubble::after {{
                content: '';
                position: absolute;
                left: -8px;
                top: 12px;
                border: 8px solid transparent;
                border-right-color: var(--q-accent);
                border-left: 0;
            }}
        </style>
        <script>
        if ('serviceWorker' in navigator) {{
          navigator.serviceWorker.getRegistrations().then(function(registrations) {{
            for(let registration of registrations) {{
              registration.unregister();
            }}
          }});
        }}
        </script>
    """
    )

    conversation = ConversationState()

    # Scroll handler for header fade
    last_scroll_top = [0]

    def handle_scroll(e):
        scroll_top = e.vertical_position
        if scroll_top > last_scroll_top[0] and scroll_top > 100:
            ui.run_javascript(
                f"document.getElementById('{header.id}').style.opacity = '0'"
            )
        else:
            ui.run_javascript(
                f"document.getElementById('{header.id}').style.opacity = '1'"
            )
        last_scroll_top[0] = scroll_top

    async def send() -> None:
        """Handle sending a user message and processing the AI response."""
        question = text.value
        text.value = ""
        if not question.strip():
            return

        with message_container:
            with ui.row().classes("w-full justify-end"):
                ui.chat_message(text=question, sent=True).props(
                    "bg-color=primary text-color=grey-8"
                ).classes("shadow-sm")
            with ui.row().classes("w-full justify-start"):
                response_message = (
                    ui.chat_message(sent=False)
                    .props("bg-color=accent text-color=grey-8")
                    .classes("shadow-sm")
                )

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
                    await ui.run_javascript(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
        except Exception as e:
            logger.error("ai_response_failed", error=str(e))
            response_message.clear()
            with response_message:
                ui.label(f"Error: {str(e)}")

    def new_conversation() -> None:
        """Start a new conversation."""
        conversation.clear_messages()
        message_container.clear()
        with message_container:
            with ui.row().classes("w-full justify-start"):
                ui.chat_message(
                    text=scene["chat"]["welcome_message"], sent=False
                ).props("bg-color=accent text-color=grey-8").classes("shadow-sm")
        logger.info("new_conversation_started")

    # Header with overflow effect - fixed positioning with scroll detection
    header = ui.header().classes(
        f"{scene['header']['fixed_classes']} {scene['header']['classes']}"
    )
    with header:
        with ui.row().classes(
            "w-full items-center justify-between px-4 py-3 max-w-4xl mx-auto"
        ):
            # Left side: Logo and tagline
            with ui.row().classes("items-center gap-2 sm:gap-3 flex-shrink-0"):
                ui.html(
                    '<img src="/branding/logo-full-color.svg" alt="MammoChat" class="h-10 flex-shrink-0">',
                    sanitize=False,
                ).classes("flex-shrink-0"),
                ui.label("Your journey, together").classes(
                    "text-xs text-grey-8 leading-tight"
                )

            # Right side: Theme toggle
            def toggle_theme():
                dark.toggle()
                theme_btn.icon = "dark_mode" if dark.value else "light_mode"

            # Right side - Clean controls
            with ui.row().classes("items-center gap-2"):
                theme_btn = (
                    ui.button(on_click=toggle_theme)
                    .props("flat dense color=grey-8")
                    .classes("flex-shrink-0")
                )
                theme_btn.icon = "dark_mode" if dark.value else "light_mode"

    # Initialize header transition
    ui.run_javascript(
        f"document.getElementById('{header.id}').style.transition = 'opacity 0.3s ease'"
    )

    # Main layout container with proper spacing for fixed header and footer
    with ui.column().classes(
        f"min-h-screen pt-20 pb-16 {scene['layout']['content_classes']}"
    ):
        # Chat Area with proper scroll container
        with ui.column().classes(f"{scene['chat']['container_classes']} flex-grow"):
            message_container = ui.scroll_area().classes(
                f"{scene['chat']['message_container_classes']} flex-grow"
            )
            message_container.on_scroll(handle_scroll)
            with message_container:
                with ui.row().classes("w-full justify-start"):
                    ui.chat_message(
                        text=scene["chat"]["welcome_message"], sent=False
                    ).props("bg-color=accent text-color=grey-8").classes("shadow-sm")

    # Enhanced Footer with dynamic effects and fixed bottom positioning
    with ui.footer().classes(
        f'{scene["footer"]["fixed_classes"]} {scene["footer"]["classes"]}'
    ):
        with ui.row().classes(
            f'w-full max-w-4xl mx-auto {scene["footer"]["padding"]} items-center gap-3'
        ):
            ui.button(icon="add", on_click=new_conversation, color="primary").props(
                "flat round"
            ).classes(
                "hover:scale-105 transition-all duration-300 backdrop-blur-sm"
            ).tooltip(
                "New conversation"
            )
            text = (
                ui.input(placeholder="Share what's on your mind...")
                .classes("flex-grow backdrop-blur-sm")
                .props("filled dense")
                .on("keydown.enter", send)
                .tooltip("Type your message here")
            )
            ui.button(icon="send", on_click=send).props(
                "flat round color=primary"
            ).classes(
                "hover:scale-105 transition-all duration-300 backdrop-blur-sm"
            ).tooltip(
                "Send message"
            )
