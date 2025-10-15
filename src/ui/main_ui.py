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
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

            :root {{
                --primary-color: {scene['palette']['primary']};
                --secondary-color: {scene['palette']['secondary']};
                --background-color: {scene['palette']['background']};
                --surface-color: {scene['palette']['surface']};
                --text-color: {scene['palette']['text']};
                --text-secondary: {scene['palette']['text_secondary']};
                --accent-color: {scene['palette']['accent']};
                --success-color: {scene['palette']['success']};
                --border-color: {scene['palette']['border']};
                --border-radius: 12px;
                --animation-duration: 0.3s;
            }}

            body {{
                background: linear-gradient(135deg, #FAFBFC 0%, #FFF5F7 100%);
                color: var(--text-color);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}

            .mammochat-header {{
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                box-shadow: 0 4px 20px rgba(244, 184, 197, 0.2);
            }}

            .message-bubble {{
                border-radius: var(--border-radius);
                padding: 1.25rem 1.5rem;
                max-width: 70%;
                animation: slideIn var(--animation-duration) ease-out;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                line-height: 1.6;
            }}

            .user-message {{
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                margin-left: auto;
                color: white;
                border: none;
            }}

            .assistant-message {{
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                color: var(--text-color);
            }}

            .typing-indicator {{
                display: flex;
                gap: 0.5rem;
                padding: 1rem;
                align-items: center;
            }}

            .typing-dot {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--primary-color);
                animation: typing 1.4s infinite;
            }}

            .typing-dot:nth-child(2) {{
                animation-delay: 0.2s;
            }}

            .typing-dot:nth-child(3) {{
                animation-delay: 0.4s;
            }}

            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateY(10px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            @keyframes typing {{
                0%, 60%, 100% {{
                    transform: translateY(0);
                    opacity: 0.7;
                }}
                30% {{
                    transform: translateY(-8px);
                    opacity: 1;
                }}
            }}

            .input-container {{
                background: var(--surface-color);
                border-radius: var(--border-radius);
                padding: 1rem;
                border: 2px solid var(--border-color);
                transition: all var(--animation-duration);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            }}

            .input-container:focus-within {{
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(244, 184, 197, 0.1);
            }}

            .btn-send {{
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                border: none;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all var(--animation-duration);
                color: white;
            }}

            .btn-send:hover {{
                transform: scale(1.05);
                box-shadow: 0 4px 16px rgba(244, 184, 197, 0.4);
            }}

            .btn-send:active {{
                transform: scale(0.98);
            }}

            .btn-secondary {{
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                color: var(--text-color);
                transition: all var(--animation-duration);
            }}

            .btn-secondary:hover {{
                background: var(--primary-color);
                color: white;
                border-color: var(--primary-color);
            }}

            /* Community badge */
            .community-badge {{
                background: linear-gradient(135deg, #FED7C8 0%, #FCA5A5 50%);
                padding: 0.25rem 0.75rem;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                color: var(--text-color);
            }}

            /* Trial match indicator */
            .trial-match {{
                background: linear-gradient(135deg, var(--success-color) 0%, #6EE7B7 100%);
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-size: 0.875rem;
                color: var(--text-color);
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .q-message--received {{
                max-height: none !important;
                overflow: visible !important;
            }}
        </style>
    """
    )


def create_header(scene, dark):
    """Build the MammoChat header."""
    header = ui.header().classes('w-full p-4 mammochat-header items-center justify-between')
    with header:
        with ui.row().classes('items-center gap-3'):
            # Use heart icon for MammoChat
            ui.icon('favorite', size='2rem', color='white')
            with ui.column().classes('gap-0'):
                ui.label('MammoChat').classes('text-2xl font-bold text-white')
                ui.label('Your journey, together').classes('text-sm text-white opacity-80')

        with ui.row().classes('gap-2'):
            ui.button(
                icon='people',
                on_click=lambda: None  # Placeholder for community
            ).props('flat round color=white').tooltip('Community')

            ui.button(
                icon='science',
                on_click=lambda: None  # Placeholder for trials
            ).props('flat round color=white').tooltip('Clinical Trials')

            ui.button(
                icon='refresh',
                on_click=lambda: None  # Placeholder for new conversation
            ).props('flat round color=white').tooltip('New Conversation')

            def toggle_theme():
                dark.toggle()
                theme_btn.icon = "dark_mode" if dark.value else "light_mode"

            theme_btn = (
                ui.button(on_click=toggle_theme)
                .props('flat dense color=white')
                .classes('flex-shrink-0')
            )
            theme_btn.icon = "dark_mode" if dark.value else "light_mode"

    return header


def create_chat_area(scene, conversation):
    """Build the main chat interface."""
    with ui.column().classes('w-full h-screen'):
        with ui.scroll_area().classes('flex-grow w-full p-4') as chat_scroll:
            chat_container = ui.column().classes('w-full max-w-4xl mx-auto gap-4')

            # Add welcome message
            with chat_container:
                with ui.row().classes('w-full'):
                    with ui.card().classes('message-bubble assistant-message max-w-full'):
                        ui.markdown("""
                        ### Welcome to MammoChat 💗

                        I'm here to support you on your breast cancer journey. I can help you:

                        - 🔬 **Find clinical trials** that match your situation
                        - 👥 **Connect with communities** of patients with similar experiences
                        - 📚 **Understand information** about treatments and options
                        - 💪 **Navigate your healthcare** with confidence

                        How can I support you today?
                        """)
    return chat_container


def create_footer(scene, send, new_conversation):
    with ui.footer().classes('w-full items-center backdrop-blur-md bg-white/25 border-t border-white/20 transition-all duration-300'):
        with ui.row().classes('w-full max-w-4xl mx-auto px-6 py-4 items-center gap-3'):
            ui.button(icon="add", on_click=new_conversation, color="primary").props('flat round').classes('hover:scale-105 transition-all duration-300 backdrop-blur-sm').tooltip('New conversation')
            text = (
                ui.input(placeholder='Share what\'s on your mind...')
                .classes('flex-grow backdrop-blur-sm')
                .props('filled dense')
                .on("keydown.enter", send)
                .tooltip('Type your message here')
            )
            send_btn = (
                ui.button(icon="send", on_click=send)
                .props('flat round color=primary')
                .classes('hover:scale-105 transition-all duration-300 backdrop-blur-sm')
                .tooltip('Send message')
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
