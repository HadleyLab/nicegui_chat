"""User Interface Layer for MammoChat™.

This module implements the presentation layer of the MammoChat™ application,
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

from nicegui import ui

from config import config
from src.models.chat import ConversationState
from src.services.chat_service import ChatService
from src.utils.text_processing import strip_markdown


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
    """Set up PWA meta tags and fonts without custom CSS generation."""
    ui.add_head_html(
        f"""
        <meta name="theme-color" content="{scene['palette']['primary']}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="apple-touch-icon" href="/branding/apple-touch-icon.png">
        <link rel="manifest" href="/public/manifest.json">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

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

            .q-message--received {{
                max-height: none !important;
                overflow: visible !important;
            }}
        </style>
    """
    )


def create_header(scene, dark):
    """Build the MammoChat header."""
    header_classes = scene.get("header_styles", {}).get(
        "classes",
        "w-full p-6 bg-gradient-to-br from-rose-200 to-pink-300 shadow-lg transition-all duration-300 items-center justify-between",
    )
    header = ui.header().classes(header_classes)
    with header:
        # Main header row with responsive layout
        with ui.row().classes("w-full items-center justify-between gap-4 py-2 flex-nowrap"):
            # Left side: Logo and tagline
            with ui.row().classes("items-center gap-3 md:gap-6 flex-shrink-0 min-w-0 flex-1"):
                # Use HTML img tag for reliable logo display
                logo_src = scene.get("logo", {}).get("src", "/branding/logo-full-white.svg")
                logo_alt = scene.get("logo", {}).get("alt", "MammoChat Logo")
                logo_classes = scene.get("header_logo", {}).get(
                    "classes", "h-8 sm:h-10 md:h-12 lg:h-16 w-auto max-w-[120px] sm:max-w-[150px] md:max-w-[200px] lg:max-w-[250px] object-contain flex-shrink-0"
                )
                ui.html(
                    f'<img src="{logo_src}" alt="{logo_alt}" class="{logo_classes}">',
                    sanitize=False,
                )

                # Tagline with proper responsive styling - ensure visibility
                tagline = scene.get("header", {}).get("tagline", "Your journey, together")
                tagline_classes = scene.get("header", {}).get(
                    "tagline_classes",
                    "text-sm md:text-base text-white leading-tight drop-shadow-lg flex-shrink-0",
                )
                ui.label(tagline).classes(tagline_classes)

            # Right side: Theme toggle button
            with ui.row().classes("gap-2 flex-shrink-0"):
                def toggle_theme():
                    dark.toggle()
                    theme_btn.icon = "dark_mode" if dark.value else "light_mode"
                    # Update document class for CSS targeting
                    if dark.value:
                        ui.run_javascript("document.body.classList.add('dark-theme')")
                        ui.run_javascript(
                            "document.documentElement.setAttribute('data-theme', 'dark')"
                        )
                    else:
                        ui.run_javascript("document.body.classList.remove('dark-theme')")
                        ui.run_javascript(
                            "document.documentElement.setAttribute('data-theme', 'light')"
                        )

                theme_btn_props = scene.get("header", {}).get(
                    "theme_btn_props", "flat dense color=white"
                )
                theme_btn_classes = scene.get("header", {}).get(
                    "theme_btn_classes", "flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10"
                )
                theme_btn = (
                    ui.button(on_click=toggle_theme)
                    .props(theme_btn_props)
                    .classes(theme_btn_classes)
                )
                theme_btn.icon = "dark_mode" if dark.value else "light_mode"

    return header


def create_chat_area(scene, conversation):
    """Build the main chat interface."""
    with ui.column().classes("w-full h-screen"):
        scroll_classes = scene.get("chat", {}).get(
            "scroll_area_classes", "flex-grow w-full p-4"
        )
        with ui.scroll_area().classes(scroll_classes):
            container_classes = scene.get("chat", {}).get(
                "container_classes", "w-full max-w-4xl mx-auto gap-4"
            )
            chat_container = ui.column().classes(container_classes)

            # Add welcome message
            with chat_container:
                assistant_row_classes = scene.get("chat", {}).get(
                    "assistant_row_classes", "w-full justify-start"
                )
                welcome_props = scene.get("chat", {}).get(
                    "welcome_message_props", "bg-color=accent text-color=grey-8"
                )
                welcome_classes = scene.get("chat", {}).get(
                    "welcome_message_classes",
                    "bg-white border border-slate-200 text-slate-700 shadow-md rounded-2xl p-5 max-w-[70%] animate-[slideIn_0.3s_ease-out] leading-relaxed transition-all duration-300",
                )
                with ui.row().classes(assistant_row_classes):
                    ui.chat_message(
                        text=scene["chat"]["welcome_message"], sent=False
                    ).props(welcome_props).classes(welcome_classes)
    return chat_container


def create_footer(scene, send, new_conversation):
    footer_classes = scene.get("footer", {}).get(
        "classes",
        "w-full items-center backdrop-blur-md bg-white/25 border-t border-white/20 transition-all duration-300",
    )
    with ui.footer().classes(footer_classes):
        row_classes = scene.get("footer", {}).get(
            "row_classes", "w-full max-w-4xl mx-auto px-6 py-4 items-center gap-3"
        )
        with ui.row().classes(row_classes):
            new_btn_props = scene.get("footer", {}).get("new_btn_props", "flat round")
            new_btn_classes = scene.get("footer", {}).get(
                "new_btn_classes",
                "hover:scale-105 transition-all duration-300 backdrop-blur-sm",
            )
            new_btn_tooltip = scene.get("footer", {}).get(
                "new_btn_tooltip", "New conversation"
            )
            ui.button(icon="add", on_click=new_conversation, color="primary").props(
                new_btn_props
            ).classes(new_btn_classes).tooltip(new_btn_tooltip)

            input_classes = scene.get("footer", {}).get(
                "input_classes", "flex-grow backdrop-blur-sm"
            )
            input_props = scene.get("footer", {}).get("input_props", "filled dense")
            input_placeholder = scene.get("footer", {}).get(
                "input_placeholder", "Share what's on your mind..."
            )
            input_tooltip = scene.get("footer", {}).get(
                "input_tooltip", "Type your message here"
            )
            text = (
                ui.input(placeholder=input_placeholder)
                .classes(input_classes)
                .props(input_props)
                .on("keydown.enter", send)
                .tooltip(input_tooltip)
            )

            send_btn_props = scene.get("footer", {}).get(
                "send_btn_props", "flat round color=primary"
            )
            send_btn_classes = scene.get("footer", {}).get(
                "send_btn_classes",
                "hover:scale-105 transition-all duration-300 backdrop-blur-sm",
            )
            send_btn_tooltip = scene.get("footer", {}).get(
                "send_btn_tooltip", "Send message"
            )
            send_btn = (
                ui.button(icon="send", on_click=send)
                .props(send_btn_props)
                .classes(send_btn_classes)
                .tooltip(send_btn_tooltip)
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

    scene = config.scene

    dark = ui.dark_mode()

    # Initialize theme state on page load
    ui.run_javascript(
        f"""
        document.addEventListener('DOMContentLoaded', function() {{
            const isDark = {str(dark.value).lower()};
            if (isDark) {{
                document.body.classList.add('dark-theme');
                document.documentElement.setAttribute('data-theme', 'dark');
            }} else {{
                document.body.classList.remove('dark-theme');
                document.documentElement.setAttribute('data-theme', 'light');
            }}
        }});
    """
    )

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
            user_row_classes = scene.get("chat", {}).get(
                "user_row_classes", "w-full justify-end"
            )
            user_props = scene.get("chat", {}).get(
                "user_message_props", "bg-color=primary text-color=white"
            )
            user_classes = scene.get("chat", {}).get(
                "user_message_classes",
                "bg-gradient-to-br from-rose-200 to-pink-300 ml-auto text-white border-none shadow-md rounded-2xl p-5 max-w-[70%] animate-[slideIn_0.3s_ease-out] leading-relaxed transition-all duration-300",
            )
            with ui.row().classes(user_row_classes):
                ui.chat_message(text=question, sent=True).props(user_props).classes(
                    user_classes
                )

            assistant_row_classes = scene.get("chat", {}).get(
                "assistant_row_classes", "w-full justify-start"
            )
            assistant_props = scene.get("chat", {}).get(
                "assistant_message_props", "bg-color=accent text-color=grey-8"
            )
            assistant_classes = scene.get("chat", {}).get(
                "assistant_message_classes",
                "bg-white border border-slate-200 text-slate-700 shadow-md rounded-2xl p-5 max-w-[70%] animate-[slideIn_0.3s_ease-out] leading-relaxed transition-all duration-300",
            )
            with ui.row().classes(assistant_row_classes):
                response_message = (
                    ui.chat_message(sent=False)
                    .props(assistant_props)
                    .classes(assistant_classes)
                )

        with response_message:
            ui.spinner()

        # Use NiceGUI's native task processing with refreshable UI
        response_state = {"content": "", "error": None}

        @ui.refreshable
        def response_display():
            """Refreshable UI component for streaming response."""
            if response_state["error"]:
                ui.label(f"Error: {response_state['error']}").classes("text-left")
            elif not response_state["content"]:
                ui.spinner()
            else:
                ui.label(strip_markdown(response_state["content"])).classes("text-left")

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
            assistant_row_classes = scene.get("chat", {}).get(
                "assistant_row_classes", "w-full justify-start"
            )
            welcome_props = scene.get("chat", {}).get(
                "welcome_message_props", "bg-color=accent text-color=grey-8"
            )
            welcome_classes = scene.get("chat", {}).get(
                "welcome_message_classes",
                "bg-white border border-slate-200 text-slate-700 shadow-md rounded-2xl p-5 max-w-[70%] animate-[slideIn_0.3s_ease-out] leading-relaxed transition-all duration-300",
            )
            with ui.row().classes(assistant_row_classes):
                ui.chat_message(
                    text=scene["chat"]["welcome_message"], sent=False
                ).props(welcome_props).classes(welcome_classes)

    create_header(scene, dark)
    message_container = create_chat_area(scene, conversation)
    text, send_btn = create_footer(scene, send, new_conversation)
