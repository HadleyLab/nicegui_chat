#!/usr/bin/env python3
"""MammoChat - Compassionate AI support for breast cancer patients.

Modern, sophisticated UI built with pure NiceGUI, Tailwind, and Quasar.
"""

import structlog
from functools import partial
from nicegui import ui

from src.ai_service import AIService
from src.config import config
from src.theme_service import theme_service
from src.components import mammochat_logo, welcome_message, header_layout

logger = structlog.get_logger()

# Validate configuration
try:
    config.validate()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print("Please create a .env file with your DEEPSEEK_API_KEY")
    exit(1)

# Initialize AI service
ai_service = AIService()

# Conversation history
messages: list[dict[str, str]] = []


@ui.page("/")
def main() -> None:
    """Main chat page with sophisticated modern design."""

    logger.info("page_loaded", path="/")

    # Initialize styling and PWA
    theme_service.initialize_app_styling()

    # Styling and PWA are now handled by theme_service.initialize_app_styling()

    # The queries below are used to expand the content down to the footer
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    async def send() -> None:
        """Send message and get AI response."""
        question = text.value
        text.value = ""

        if not question.strip():
            logger.warning("empty_message_submitted")
            return

        logger.info("user_message_received", length=len(question))

        # Add user message
        messages.append({"role": "user", "content": question})

        # Display messages following NiceGUI example pattern - EXACT structure
        with message_container:
            ui.chat_message(text=question, name="You", sent=True)
            # Assistant response: use branded grey background
            response_message = ui.chat_message(name="MammoChat", sent=False).props('bg-color=grey-2')

        # Scroll down after user message is sent
        await ui.run_javascript("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")

        # Minimal thinking indicator
        with response_message:
            ui.spinner(type="dots", size="sm", color="primary").classes('opacity-60')

        logger.info("streaming_ai_response", history_length=len(messages)-1)

        # Stream AI response
        response = ""
        chunk_count = 0
        try:
            async for chunk in ai_service.stream_chat(question, messages[:-1]):
                response += chunk
                chunk_count += 1

                # Update the message in real-time
                response_message.clear()
                with response_message:
                    ui.markdown(response)
                ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

            logger.info("ai_response_complete", chunks=chunk_count, length=len(response))
        except Exception as e:
            logger.error("ai_response_failed", error=str(e))
            response_message.clear()
            with response_message:
                ui.markdown(f"⚠️ Error: {str(e)}")

        # Store response in message history (thinking indicator auto-cleared when message updated)
        messages.append({"role": "assistant", "content": response})

        # Auto-scroll to bottom
        ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

    def new_conversation() -> None:
        """Start a new conversation."""
        messages.clear()
        message_container.clear()
        logger.info("new_conversation_started")

    # Full-width responsive layout
    ui.query(".q-page").classes("flex")
    ui.query(".nicegui-content").classes("w-full")

    # Create dark mode instance - start with False (light mode) to allow toggling
    dark = ui.dark_mode(value=False)

    # Header - clean and simple
    with ui.header().classes("q-header"):
        with ui.row().classes("w-full items-center justify-between px-6 py-3 max-w-5xl mx-auto"):
            # Logo using extracted component
            with ui.row().classes('items-center gap-3'):
                mammochat_logo()

            # Right side: tagline, dark mode toggle, and menu button
            with ui.row().classes('items-center gap-4'):
                # Tagline - warmer color for better cohesion
                ui.label(config.app_tagline).classes('text-sm').style(f'color: {config.text_secondary}')

                # Dark mode toggle button
                dark_toggle = ui.button().props('flat round')
                dark_toggle.bind_icon_from(dark, 'value', lambda v: 'light_mode' if v else 'dark_mode')
                dark_toggle.on('click', lambda: dark.toggle())

                # Menu button
                with ui.button(icon='palette').props('flat round'):
                    with ui.menu() as menu:
                        for theme_name in theme_service.get_available_themes().keys():
                            ui.menu_item(theme_name, on_click=partial(theme_service.switch_theme, theme_name))

    # Spacious, comfortable message area
    with ui.column().classes("w-full max-w-3xl mx-auto flex-grow items-stretch py-6 px-4"):
        message_container = ui.column().classes("items-stretch")

        # Welcome message when app first loads
        with message_container:
            welcome = ui.chat_message(name="MammoChat", sent=False).props('bg-color=grey-1')
            with welcome:
                ui.markdown('''
I'm here to support you on your breast cancer journey. I can help you:

- 💊 **Find Clinical Trials** – Discover and match you with trials that fit your specific diagnosis and situation
- 👥 **Connect with Peers** – Match you with other patients who share similar experiences and understand your journey
- 💪 **Make Informed Decisions** – Feel confident and empowered about your healthcare path

I remember our conversations and your unique situation, so you never have to repeat yourself. Whether you need clinical trial matches, peer connections, or just someone to talk to, I'm here to walk alongside you every step of the way.

**How can I support you today?** 💗
                '''.strip())

    # Footer with sophisticated glass-morphism effect
    with ui.footer().classes("q-footer"):
        with ui.row().classes("w-full items-center gap-3 px-6 py-3 max-w-5xl mx-auto"):
            # New conversation button
            ui.button(icon="add", on_click=new_conversation) \
                .props("flat round") \
                .tooltip('Start a new conversation')

            # Text input
            text = (
                ui.textarea(placeholder="Share what's on your mind...")
                .props("outlined autogrow rounded")
                .classes("flex-grow")
                .style("max-height: 120px;")
                .on("keydown.enter", send)
            )

            # Send button
            ui.button(icon="send", on_click=send) \
                .props("flat round") \
                .tooltip('Send message')


# Run the application
if __name__ in {"__main__", "__mp_main__"}:
    logger.info("starting_application", host=config.host, port=config.port)
    from src.app import run_app
    run_app()
