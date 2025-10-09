#!/usr/bin/env python3

import structlog
from fastapi.responses import FileResponse
from nicegui import app, ui

from src.ai_service import AIService
from src.config import config

logger = structlog.get_logger()

try:
    config.validate()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print("Please create a .env file with your DEEPSEEK_API_KEY")
    exit(1)

ai_service = AIService()
messages: list[dict[str, str]] = []
app.add_static_files("/branding", "branding")
app.add_static_files("/public", "public")


# PWA routes
@app.get("/service_worker.js")
async def service_worker():
    return FileResponse("service_worker.js")


@app.get("/manifest.json")
async def manifest():
    return FileResponse("public/manifest.json")


@ui.page("/")
def main() -> None:

    logger.info("page_loaded", path="/")

    palette = config.palette
    status = config.status_colors

    # Use NiceGUI's default dark mode functionality
    dark = ui.dark_mode()

    # Set comprehensive MammoChat colors for both light and dark themes
    ui.colors(
        primary=palette["primary"],
        secondary=palette["secondary"],
        accent=palette["accent"],
        positive=status["positive"],
        negative=status["negative"],
        info=status["info"],
        warning=status["warning"],
        dark="auto",  # Enable automatic dark mode detection
    )

    ui.add_head_html(
        f"""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="theme-color" content="{palette['primary']}" media="(prefers-color-scheme: light)">
        <meta name="theme-color" content="{palette['text']}" media="(prefers-color-scheme: dark)">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="MammoChat">
        <link rel="apple-touch-icon" href="/branding/apple-touch-icon.png">
        <link rel="manifest" href="/manifest.json">
        <script>
            if ('serviceWorker' in navigator) {{
                window.addEventListener('load', function() {{
                    navigator.serviceWorker.register('/service_worker.js');
                }});
            }}
        </script>
    """
    )

    # Load CSS from separate file
    with open("css/main.css", "r") as f:
        ui.add_css(f.read())

    # Layout styling
    ui.query(".q-page").classes("flex")
    ui.query(".nicegui-content").classes("w-full")

    async def send() -> None:
        question = text.value
        text.value = ""

        if not question.strip():
            logger.warning("empty_message_submitted")
            return

        logger.info("user_message_received", length=len(question))

        # Add user message
        messages.append({"role": "user", "content": question})

        # Display messages with proper NiceGUI theming and sanitization
        with message_container:
            # User message - pink branding colors
            ui.chat_message(text=question, name="You", sent=True).props(
                "bg-color=primary text-color=white"
            )
            # Assistant response - grey styling
            response_message = ui.chat_message(name="MammoChat", sent=False).props(
                "bg-color=grey-3 text-color=grey-9"
            )

        # Scroll down after user message is sent
        await ui.run_javascript(
            "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})"
        )

        # Minimal thinking indicator - use pink color directly
        with response_message:
            ui.spinner(type="dots", size="sm").props("color=pink").classes("opacity-60")

        logger.info("streaming_ai_response", history_length=len(messages) - 1)

        # Stream AI response
        response = ""
        try:
            async for chunk in ai_service.stream_chat(question, messages[:-1]):
                response += chunk

                # Update the message in real-time
                response_message.clear()
                with response_message:
                    ui.html(response, sanitize=False)
                ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")
        except Exception as e:
            logger.error("ai_response_failed", error=str(e))
            response_message.clear()
            with response_message:
                ui.html(f"<p>⚠️ Error: {str(e)}</p>", sanitize=False)

        # Store response in message history (thinking indicator auto-cleared when message updated)
        messages.append({"role": "assistant", "content": response})

        # Auto-scroll to bottom
        ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

    def new_conversation() -> None:
        messages.clear()
        message_container.clear()
        logger.info("new_conversation_started")

    # Clean header with white logo and visible tagline
    with ui.header().classes("q-header"):
        with ui.row().classes(
            "w-full items-center justify-between px-2 sm:px-4 py-3 max-w-4xl mx-auto"
        ):
            # Left side: Logo and tagline
            with ui.row().classes("items-center gap-2 sm:gap-3 flex-shrink-0"):
                ui.html(
                    """
                <div class="flex items-center">
                    <svg width="32" height="32" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="sm:w-10 sm:h-10 w-8 h-8">
                        <path d="M48 16C48 11.5817 44.4183 8 40 8H16C11.5817 8 8 11.5817 8 16V36C8 40.4183 11.5817 44 16 44H20V52L28 44H40C44.4183 44 48 40.4183 48 36V16Z"
                              fill="white" opacity="0.9"/>
                        <path d="M28 20C28 16.6863 30.6863 14 34 14C35.6569 14 37.1569 14.6716 38.2426 15.7574C39.3284 14.6716 40.8284 14 42.4853 14C45.799 14 48.4853 16.6863 48.4853 20C48.4853 21.3062 48.0615 22.512 47.3431 23.4853L38.2426 32.5858L29.1421 23.4853C28.4237 22.512 28 21.3062 28 20Z"
                              fill="white"/>
                    </svg>
                    <span class="text-white font-bold text-lg sm:text-xl ml-2 sm:ml-3">MammoChat</span>
                </div>
                """,
                    sanitize=False,
                ).classes("flex items-center")
                ui.label("Your journey, together").classes(
                    "text-xs sm:text-sm text-white opacity-80 ml-3 sm:ml-4"
                )
                ui.label("Your journey, together").classes(
                    "text-xs sm:text-sm text-white opacity-80 hidden xs:inline"
                )

            # Right side: Dark mode toggle
            with ui.row().classes("items-center gap-2 flex-shrink-0"):
                # Dark mode toggle
                ui.button(icon="dark_mode", on_click=lambda: dark.toggle()).props(
                    "flat dense color=white"
                ).classes("flex-shrink-0")

    # Spacious, comfortable message area
    with ui.column().classes(
        "w-full max-w-3xl mx-auto flex-grow items-stretch py-6 px-4"
    ):
        message_container = ui.column().classes("items-stretch")

        # Welcome message when app first loads - grey AI styling
        with message_container:
            welcome = ui.chat_message(name="MammoChat", sent=False).props(
                "bg-color=grey-3 text-color=grey-9"
            )
            with welcome:
                ui.label(
                    """
Welcome to MammoChat!

I'm here to support you on your breast cancer journey. I can help you:

- Find clinical trials that match your situation
- Connect with communities of patients with similar experiences
- Understand information about treatments and options
- Navigate your healthcare with confidence

How can I support you today?
                """.strip()
                ).classes("whitespace-pre-wrap")

    # Theme-aware footer with input area
    with ui.footer().classes("q-footer"):
        with ui.row().classes("w-full items-center gap-3 px-4 py-3 max-w-4xl mx-auto"):
            # New conversation button - theme-aware styling
            ui.button(icon="add", on_click=new_conversation).props(
                "round unelevated"
            ).classes("theme-aware-footer-btn").tooltip("Start a new conversation")

            # Text input - theme-aware styling
            text = (
                ui.textarea(placeholder="Share what's on your mind...")
                .props("outlined autogrow rounded")
                .classes("flex-grow theme-aware-input")
                .style("max-height: 120px;")
                .on("keydown.enter", send)
            )

            # Send button - theme-aware styling
            ui.button(icon="send", on_click=send).props("round unelevated").classes(
                "theme-aware-footer-btn"
            ).tooltip("Send message")


# Run the application
if __name__ in {"__main__", "__mp_main__"}:
    logger.info("starting_application", host=config.host, port=config.port)
    ui.run(
        title="MammoChat",
        host=config.host,
        port=config.port,
        reload=False,
        show=True,
    )
