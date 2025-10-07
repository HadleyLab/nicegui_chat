#!/usr/bin/env python3
"""MammoChat - Compassionate AI support for breast cancer patients.

Modern, sophisticated UI built with pure NiceGUI, Tailwind, and Quasar.
"""

import structlog
from fastapi.responses import FileResponse
from nicegui import app, ui

from src.ai_service import AIService
from src.config import config

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

# Theme colors from centralized config

# PWA Setup
app.add_static_files("/branding", "branding")


@app.get("/manifest.json")
def manifest() -> FileResponse:
    """Serve PWA manifest."""
    return FileResponse("manifest.json", media_type="application/manifest+json")


@app.get("/service_worker.js")
def service_worker() -> FileResponse:
    """Serve service worker for offline support."""
    return FileResponse("service_worker.js", media_type="application/javascript")


@app.get("/apple-touch-icon.png")
def apple_icon() -> FileResponse:
    """Serve Apple touch icon."""
    return FileResponse("branding/apple-touch-icon.png", media_type="image/png")


@ui.page("/")
def main() -> None:
    """Main chat page with sophisticated modern design."""

    logger.info("page_loaded", path="/")

    # Theme-based color palette
    ui.colors(
        primary=config.primary,
        secondary=config.secondary,
        accent=config.accent,
        positive=config.success,
        negative=config.error,
        info=config.info,
        warning=config.warning,
        dark=config.charcoal,
    )

    # PWA metadata with theme-based colors
    ui.add_head_html(f"""
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="{config.primary}" media="(prefers-color-scheme: light)">
        <meta name="theme-color" content="{config.charcoal}" media="(prefers-color-scheme: dark)">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="{config.app_name}">
        <link rel="apple-touch-icon" href="/apple-touch-icon.png">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
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

    # Enhanced healthcare styling with soft gradients and shadows
    ui.add_css(f"""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

        body {{
            background: linear-gradient(135deg, {config.mint} 0%, {config.background} 30%, #FFFCF9 100%) !important;
            font-family: 'Inter', system-ui, sans-serif !important;
            color: {config.text} !important;
            min-height: 100vh !important;
        }}

        /* Cohesive header with subtle pink tinge */
        .q-header {{
            background: linear-gradient(135deg, rgba(255, 252, 254, 0.90) 0%, rgba(254, 250, 253, 0.85) 100%) !important;
            backdrop-filter: blur(12px) !important;
            border-bottom: 1px solid rgba(232, 212, 218, 0.6) !important;
            box-shadow: 0 2px 10px rgba(244, 184, 197, 0.14) !important;
        }}

        /* Cohesive user messages */
        .q-message-sent .q-message-text {{
            background: linear-gradient(135deg, {config.primary_dark} 0%, {config.success} 100%) !important;
            color: white !important;
            border-radius: 16px !important;
            border-bottom-right-radius: 4px !important;
            box-shadow: 0 2px 10px rgba(199, 229, 212, 0.18) !important;
        }}

        /* Cohesive assistant messages */
        .q-message-received .q-message-text {{
            background: linear-gradient(135deg, {config.surface} 0%, rgba(254, 252, 255, 0.8) 100%) !important;
            color: {config.text} !important;
            border-radius: 16px !important;
            border-bottom-left-radius: 4px !important;
            border: 1px solid rgba(232, 212, 218, 0.7) !important;
            box-shadow: 0 2px 10px rgba(244, 184, 197, 0.08) !important;
        }}

        /* Clean input styling */
        .q-field--outlined .q-field__control {{
            border: 1px solid {config.border} !important;
            border-radius: 8px !important;
            background: {config.surface} !important;
        }}

        .q-field--outlined.q-field__focused .q-field__control {{
            border-color: {config.mint} !important;
            border-width: 2px !important;
        }}

        /* Cohesive button styling */
        .q-btn {{
            background: linear-gradient(135deg, {config.primary_dark} 0%, {config.success} 100%) !important;
            color: white !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px rgba(199, 229, 212, 0.18) !important;
            transition: all 0.2s ease !important;
        }}

        .q-btn:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 14px rgba(199, 229, 212, 0.28) !important;
            background: linear-gradient(135deg, {config.success} 0%, {config.primary_dark} 100%) !important;
        }}

        /* Mint accent elements */
        .q-header .q-btn,
        .accent-button {{
            background: linear-gradient(135deg, {config.mint} 0%, {config.success} 100%) !important;
            box-shadow: 0 2px 8px rgba(199, 229, 212, 0.12) !important;
        }}

        .q-header .q-btn:hover,
        .accent-button:hover {{
            background: linear-gradient(135deg, {config.success} 0%, {config.mint} 100%) !important;
            box-shadow: 0 4px 12px rgba(199, 229, 212, 0.2) !important;
        }}

        /* New conversation button in footer - match Chat text color */
        .q-footer .q-row .q-btn {{
            background: {config.slate_gray} !important;
            color: white !important;
            border: 1px solid {config.slate_gray} !important;
        }}

        .q-footer .q-row .q-btn:hover {{
            background: {config.text} !important;
            border-color: {config.text} !important;
            box-shadow: 0 2px 8px rgba(90, 79, 92, 0.2) !important;
        }}

        /* Cohesive footer */
        .q-footer {{
            background: linear-gradient(135deg, rgba(255, 252, 254, 0.90) 0%, rgba(254, 250, 253, 0.85) 100%) !important;
            backdrop-filter: blur(12px) !important;
            border-top: 1px solid rgba(232, 212, 218, 0.6) !important;
            box-shadow: 0 -2px 10px rgba(244, 184, 197, 0.14) !important;
        }}

        /* Cohesive selection colors */
        ::selection {{
            background: rgba(199, 229, 212, 0.25) !important;
            color: {config.text} !important;
        }}

        /* Enhanced markdown for better readability */
        .markdown p {{
            color: {config.text_secondary} !important;
            line-height: 1.6 !important;
        }}

        .markdown strong {{
            color: {config.text} !important;
        }}

        /* Cohesive healthcare dark mode */
        body.body--dark {{
            background: linear-gradient(135deg, #1A1A1A 0%, #2D1B2E 60%, #1E1E1E 100%) !important;
            color: #F8FAFC !important;
        }}

        body.body--dark .q-header {{
            background: linear-gradient(135deg, rgba(45, 27, 46, 0.92) 0%, rgba(50, 30, 48, 0.88) 100%) !important;
            border-bottom: 1px solid rgba(71, 85, 105, 0.8) !important;
            box-shadow: 0 2px 12px rgba(45, 27, 46, 0.28) !important;
        }}

        body.body--dark .q-header .text-gray-600,
        body.body--dark .q-header .text-amber-400,
        body.body--dark .q-toolbar__title {{
            color: #E2E8F0 !important;
        }}

        body.body--dark .q-footer {{
            background: linear-gradient(135deg, rgba(45, 27, 46, 0.92) 0%, rgba(50, 30, 48, 0.88) 100%) !important;
            border-top: 1px solid rgba(71, 85, 105, 0.8) !important;
            box-shadow: 0 -2px 12px rgba(45, 27, 46, 0.28) !important;
        }}

        body.body--dark .q-message-received .q-message-text {{
            background: #374151 !important;
            color: #F1F5F9 !important;
            border: 1px solid #4B5563 !important;
        }}

        body.body--dark .q-message-received .q-message-text * {{
            color: #F1F5F9 !important;
        }}

        body.body--dark .q-field--outlined .q-field__control {{
            background: #374151 !important;
            border-color: #4B5563 !important;
            color: #F1F5F9 !important;
        }}

        body.body--dark .q-field--outlined.q-field__focused .q-field__control {{
            border-color: {config.mint} !important;
            border-width: 2px !important;
            box-shadow: 0 0 0 3px rgba(199, 229, 212, 0.15) !important;
        }}

        body.body--dark .q-field__native {{
            color: #F1F5F9 !important;
        }}

        body.body--dark .q-field__native::placeholder {{
            color: #9CA3AF !important;
        }}

        /* Cohesive dark mode buttons */
        body.body--dark .q-btn {{
            background: linear-gradient(135deg, {config.primary_dark} 0%, {config.success} 100%) !important;
            color: white !important;
            box-shadow: 0 2px 12px rgba(45, 27, 46, 0.32) !important;
        }}

        body.body--dark .q-btn:hover {{
            background: linear-gradient(135deg, {config.success} 0%, {config.primary_dark} 100%) !important;
            box-shadow: 0 4px 16px rgba(199, 229, 212, 0.24) !important;
        }}

        /* Dark mode footer button */
        body.body--dark .q-footer .q-row .q-btn {{
            background: {config.slate_gray} !important;
            color: white !important;
            border: 1px solid {config.slate_gray} !important;
        }}

        body.body--dark .q-footer .q-row .q-btn:hover {{
            background: {config.text} !important;
            border-color: {config.text} !important;
            box-shadow: 0 2px 8px rgba(90, 79, 92, 0.3) !important;
        }}

        /* Dark mode logo and text */
        body.body--dark .q-header .text-gray-600,
        body.body--dark .q-header .text-amber-400,
        body.body--dark .q-toolbar__title {{
            color: #E2E8F0 !important;
        }}

        /* Dark mode markdown */
        body.body--dark .markdown p {{
            color: #CBD5E1 !important;
        }}

        body.body--dark .markdown strong {{
            color: #F1F5F9 !important;
        }}
    """)

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
            # Logo with SVG - sophisticated tri-color design
            with ui.row().classes('items-center gap-3'):
                ui.html(content=f'''
                    <svg width="200" height="50" viewBox="0 0 300 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <defs>
                        <linearGradient id="heartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" style="stop-color:{config.primary_dark};stop-opacity:1" />
                          <stop offset="100%" style="stop-color:{config.success};stop-opacity:1" />
                        </linearGradient>
                        <linearGradient id="bubbleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" style="stop-color:{config.mint};stop-opacity:0.15" />
                          <stop offset="100%" style="stop-color:{config.secondary};stop-opacity:0.1" />
                        </linearGradient>
                        <filter id="dropshadow" x="-20%" y="-20%" width="140%" height="140%">
                          <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="{config.primary}" flood-opacity="0.2"/>
                        </filter>
                      </defs>
                      <!-- Chat bubble background with mint gradient -->
                      <path d="M60 20C60 14.4772 55.5228 10 50 10H20C14.4772 10 10 14.4772 10 20V45C10 50.5228 14.4772 55 20 55H25V65L35 55H50C55.5228 55 60 50.5228 60 45V20Z"
                            fill="url(#bubbleGradient)" filter="url(#dropshadow)"/>
                      <!-- Heart with enhanced gradient -->
                      <path d="M35 25C35 20.0294 39.0294 16 44 16C46.2091 16 48.1569 17.3431 49.2426 19.2426C50.3284 17.3431 52.2761 16 54.4853 16C59.4559 16 63.4853 20.0294 63.4853 25C63.4853 26.7909 62.8112 28.359 61.732 29.4853L49.2426 40.8284L36.7529 29.4853C35.6737 28.359 35 26.7909 35 25Z"
                            fill="url(#heartGradient)" filter="url(#dropshadow)"/>
                      <!-- Heart highlights -->
                      <circle cx="47" cy="30" r="2" fill="white" opacity="0.9"/>
                      <circle cx="45" cy="27" r="1" fill="white" opacity="0.7"/>
                      <!-- Enhanced MammoChat text with consistent typing color scheme -->
                      <text x="85" y="50" font-family="Inter, system-ui, sans-serif" font-size="36" font-weight="800" fill="{config.primary_dark}" letter-spacing="-1px">Mammo</text>
                      <text x="215" y="50" font-family="Inter, system-ui, sans-serif" font-size="36" font-weight="700" fill="{config.slate_gray}" letter-spacing="-1px">Chat</text>
                    </svg>
                ''', sanitize=False)

            # Right side: tagline and dark mode
            with ui.row().classes('items-center gap-4'):
                # Tagline - warmer color for better cohesion
                ui.label(config.app_tagline).classes('text-sm').style(f'color: {config.text_secondary}')

                # Dark mode toggle - smaller icon for better balance
                toggle = ui.icon('dark_mode', size='md', color='grey-9').classes('cursor-pointer')
                toggle.on('click', lambda: dark.toggle())
                toggle.bind_name_from(dark, 'value', backward=lambda v: 'light_mode' if v else 'dark_mode')

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
                .props("round unelevated") \
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
                .props("round unelevated") \
                .tooltip('Send message')


# Run the application
if __name__ in {"__main__", "__mp_main__"}:
    logger.info("starting_application", host=config.host, port=config.port)
    ui.run(
        title="MammoChat",
        host=config.host,
        port=config.port,
        reload=True,
        show=False,
        reconnect_timeout=30.0,  # Increase reconnect timeout
    )
