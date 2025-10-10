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
    ui.colors(
        primary=scene["palette"]["primary"],
        secondary=scene["palette"]["secondary"],
        accent=scene["palette"]["accent"],
        positive=scene["status"]["positive"],
        negative=scene["status"]["negative"],
        info=scene["status"]["info"],
        warning=scene["status"]["warning"],
        dark="auto",  # Enable automatic dark mode detection
    )

    ui.add_head_html(f"""
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="{config.primary}" media="(prefers-color-scheme: light)">
        <meta name="theme-color" content="{config.text}" media="(prefers-color-scheme: dark)">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="{config.app_name}">
        <link rel="apple-touch-icon" href="/apple-touch-icon.png">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

        <!-- PWA Theme Color for MammoChat -->
        <meta name="msapplication-TileColor" content="{config.primary}">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    """)

    # Register service worker
    ui.add_body_html("""
        <script>
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/service_worker.js')
                    .then(reg => console.log('Service Worker registered', reg))
                    .catch(err => console.log('Service Worker registration failed', err));
            }
        </script>
    """)


    # Layout styling
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    conversation = ConversationState()

    async def send() -> None:
        """Handle sending a user message and processing the AI response.

        This function:
        - Retrieves and clears the user input
        - Validates the message is not empty
        - Adds the user message to the conversation
        - Displays the user message in the UI
        - Streams the AI response from the chat service
        - Updates the UI with streaming chunks
        - Handles errors gracefully with user feedback
        - Ensures proper scrolling and UI updates
        """
        question = text.value
        text.value = ""

        if not question.strip():
            logger.warning("empty_message_submitted")
            return

        logger.info("user_message_received", length=len(question))

        # Add user message to conversation
        user_message = ChatMessage(role=MessageRole.USER, content=question)
        conversation.append_message(user_message)

        # Display user message
        with message_container:
            ui.chat_message(text=question, name="You", sent=True, sanitize=True).props('bg-color=primary text-color=white').classes('rounded-borders q-pa-md q-ma-sm self-end max-w-[80%]')
            response_message = ui.chat_message(name="MammoChat", sent=False, sanitize=True).props('bg-color=grey-3 text-color=grey-9').classes('rounded-borders q-pa-md q-ma-sm self-start max-w-[80%]')

        # Scroll down after user message is sent
        await ui.run_javascript("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")

        # Minimal thinking indicator
        with response_message:
            ui.spinner(type="dots", size="sm").props('color=pink').classes('opacity-60')

        logger.info("streaming_ai_response", history_length=len(conversation.messages)-1)

        # Stream AI response
        response_content = ""
        try:
            async for event in chat_service.stream_chat(conversation, question):
                if event.event_type == "MESSAGE_CHUNK":
                    chunk = event.payload.get("content", "")
                    response_content += chunk
                    response_message.clear()
                    with response_message:
                        ui.markdown(response_content).classes('whitespace-pre-wrap leading-tight space-y-0')
                    ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")
                elif event.event_type == "ERROR":
                    error_msg = event.payload.get("error", "Unknown error")
                    logger.error("ai_response_failed", error=error_msg)
                    response_message.clear()
                    with response_message:
                        ui.label(f"⚠️ Error: {error_msg}").classes('whitespace-pre-wrap')
                    break

            logger.info("ai_response_complete", length=len(response_content))
        except Exception as e:
            logger.error("ai_response_failed", error=str(e))
            response_message.clear()
            with response_message:
                ui.label(f"⚠️ Error: {str(e)}").classes('whitespace-pre-wrap')

        # Auto-scroll to bottom
        ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

    def new_conversation() -> None:
        """Start a new conversation by clearing the current chat history.

        This function:
        - Clears all messages from the conversation state
        - Resets the UI message container
        - Re-displays the welcome message
        - Logs the conversation reset event

        Useful for users who want to start fresh without previous context.
        """
        conversation.clear_messages()
        message_container.clear()
        # Re-add welcome message
        with message_container:
            welcome = ui.chat_message(name="MammoChat", sent=False, sanitize=True).props('bg-color=grey-3 text-color=grey-9').classes('rounded-borders q-pa-md q-ma-sm self-start max-w-[80%]')
            with welcome:
                ui.markdown(config.ui_welcome_message).classes('whitespace-pre-wrap leading-tight space-y-0')
        logger.info("new_conversation_started")

    # Clean header with white logo and visible tagline
    with ui.header().classes("q-header bg-primary"):
        with ui.row().classes("w-full items-center justify-between px-2 sm:px-4 py-3 max-w-4xl mx-auto"):
            # Left side: Logo and tagline
            with ui.row().classes('items-center gap-2 sm:gap-3 flex-shrink-0'):
                ui.html('''
                <div class="flex items-center">
                    <svg width="32" height="32" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="sm:w-10 sm:h-10 w-8 h-8">
                        <path d="M48 16C48 11.5817 44.4183 8 40 8H16C11.5817 8 8 11.5817 8 16V36C8 40.4183 11.5817 44 16 44H20V52L28 44H40C44.4183 44 48 40.4183 48 36V16Z"
                              fill="white" opacity="0.9"/>
                        <path d="M28 20C28 16.6863 30.6863 14 34 14C35.6569 14 37.1569 14.6716 38.2426 15.7574C39.3284 14.6716 40.8284 14 42.4853 14C45.799 14 48.4853 16.6863 48.4853 20C48.4853 21.3062 48.0615 22.512 47.3431 23.4853L38.2426 32.5858L29.1421 23.4853C28.4237 22.512 28 21.3062 28 20Z"
                              fill="white"/>
                    </svg>
                    <span class="text-white font-bold text-lg sm:text-xl ml-2 sm:ml-3">MammoChat</span>
                </div>
                ''', sanitize=False).classes('flex items-center'),
                ui.label('Your journey, together').classes('text-xs sm:text-sm text-white opacity-80 ml-3 sm:ml-4')
                ui.label('Your journey, together').classes('text-xs sm:text-sm text-white opacity-80 hidden xs:inline')

            # Right side: Dark mode toggle
            ui.button(icon='dark_mode', on_click=lambda: dark.toggle()).props('flat dense color=white').classes('flex-shrink-0')

    # Spacious, comfortable message area
    with ui.column().classes("w-full max-w-3xl mx-auto flex-grow items-stretch py-6 px-4"):
        message_container = ui.column().classes("items-stretch")

        # Welcome message when app first loads - grey AI styling with sanitization
        with message_container:
            welcome = ui.chat_message(name="MammoChat", sent=False, sanitize=True).props('bg-color=grey-3 text-color=grey-9').classes('rounded-borders q-pa-md q-ma-sm self-start max-w-[80%]')
            with welcome:
                ui.markdown('''
Welcome to MammoChat!

I'm here to support you on your breast cancer journey. I can help you:

- Find clinical trials that match your situation
- Connect with communities of patients with similar experiences
- Understand information about treatments and options
- Navigate your healthcare with confidence

How can I support you today?
                '''.strip()).classes('whitespace-pre-wrap leading-tight space-y-0')

    # Theme-aware footer with input area
    with ui.footer().classes("q-footer bg-grey-1"):
        with ui.row().classes("w-full items-center gap-3 px-4 py-3 max-w-4xl mx-auto"):
            # New conversation button - theme-aware styling
            ui.button(icon="add", on_click=new_conversation) \
                .props("round unelevated color=primary") \
                .classes("") \
                .tooltip('Start a new conversation')

            # Text input - theme-aware styling
            text = (
                ui.textarea(placeholder="Share what's on your mind...")
                .props("outlined autogrow rounded")
                .classes("flex-grow")
                .style("max-height: 120px;")
                .on("keydown.enter", send)
            )

            # Send button - theme-aware styling
            ui.button(icon="send", on_click=send) \
                .props("round unelevated color=primary") \
                .classes("") \
                .tooltip('Send message')