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

# Add routes for PWA assets
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

    ui.add_head_html(f"""
        <!-- PWA Visual Meta Tags -->
        <meta name="theme-color" content="{palette['primary']}" media="(prefers-color-scheme: light)">
        <meta name="theme-color" content="{palette['text']}" media="(prefers-color-scheme: dark)">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

        <!-- Apple PWA Visual Support -->
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="MammoChat">
        <link rel="apple-touch-icon" href="/branding/apple-touch-icon.png">

        <!-- Microsoft PWA Visual Support -->
        <meta name="msapplication-TileColor" content="{palette['primary']}">

        <!-- PWA Manifest for metadata only -->
        <link rel="manifest" href="/manifest.json">

        <script>
            // Minimal service worker registration - just prevents 404 errors
            if ('serviceWorker' in navigator) {{
                window.addEventListener('load', function() {{
                    navigator.serviceWorker.register('/service_worker.js')
                        .catch(function(error) {{
                            console.log('ServiceWorker registration failed: ', error);
                        }});
                }});
            }}
        </script>
    """)


    # Simplified CSS using NiceGUI's built-in dark mode
    ui.add_css(f"""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

        /* Basic styling */
        html, body {{
            font-family: 'Inter', system-ui, sans-serif !important;
            background: linear-gradient(135deg, #FAFBFC 0%, #FFF5F7 100%) !important;
            color: {config.palette["text"]} !important;
        }}

        /* Dark mode handled by NiceGUI's built-in system */
        body.body--dark {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
            color: #f0f0f0 !important;
        }}

        /* MammoChat branding for light mode */
        .q-header {{ background: linear-gradient(135deg, #F4B8C5 0%, #E8A0B8 100%) !important; }}
        .q-footer {{ background: rgba(248, 250, 252, 0.95) !important; }}

        /* Dark mode header and footer handled by NiceGUI */
        body.body--dark .q-header {{ background: linear-gradient(135deg, #2d1b2d 0%, #3d2d4d 100%) !important; }}
        body.body--dark .q-footer {{ background: rgba(30, 30, 30, 0.95) !important; }}

        /* Selection styling */
        ::selection {{ background: rgba(244, 184, 197, 0.3) !important; }}
        body.body--dark ::selection {{ background: rgba(167, 227, 213, 0.3) !important; }}

        /* Responsive header improvements */
        .q-header .row {{
            min-width: 0; /* Prevent flex item overflow */
        }}

        .q-header img {{
            flex-shrink: 0; /* Prevent logo from shrinking */
            max-width: 100%; /* Ensure logo fits container */
        }}

        /* Mobile-first responsive adjustments */
        @media (max-width: 480px) {{
            .q-header .row {{
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }}
            .q-header .q-btn {{ margin-left: 0.25rem; }}
        }}

        /* Ensure logo never overflows on very small screens */
        @media (max-width: 320px) {{
            .q-header img {{
                max-width: 100px !important;
            }}
        }}

        /* Nuclear option - eliminate ALL message backgrounds and labels */
        .q-message,
        .q-message-sent,
        .q-message-received,
        .q-message-label,
        .q-message-label-container,
        .q-message-sent .q-message-label,
        .q-message-received .q-message-label,
        .q-message__label,
        .q-message__label-container,
        [class*="message"],
        [class*="label"],
        div[class*="message"] [class*="label"],
        .q-message > div,
        .q-message-sent > div,
        .q-message-received > div {{
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        /* Hide labels completely */
        .q-message-label,
        .q-message-label-container,
        .q-message__label,
        .q-message__label-container {{
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            position: absolute !important;
            left: -9999px !important;
            top: -9999px !important;
            z-index: -1 !important;
        }}

        /* Force message content to start at top */
        .q-message-text,
        .q-message-sent .q-message-text,
        .q-message-received .q-message-text {{
            margin-top: 0 !important;
            padding-top: 0 !important;
            background: transparent !important;
        }}

        /* Restore default Quasar message pointers/tails with proper styling */
        .q-message-sent::after {{
            display: block !important;
            content: "" !important;
            position: absolute !important;
            bottom: 0 !important;
            right: -8px !important;
            width: 0 !important;
            height: 0 !important;
            border: 8px solid transparent !important;
            border-left: 8px solid #F4B8C5 !important;
            border-bottom: none !important;
        }}

        .q-message-received::before {{
            display: block !important;
            content: "" !important;
            position: absolute !important;
            bottom: 0 !important;
            left: -8px !important;
            width: 0 !important;
            height: 0 !important;
            border: 8px solid transparent !important;
            border-right: 8px solid #f3f4f6 !important;
            border-bottom: none !important;
        }}

        /* Dark mode tails */
        body.body--dark .q-message-sent::after {{
            border-left-color: #F4B8C5 !important;
        }}

        body.body--dark .q-message-received::before {{
            border-right-color: #374151 !important;
        }}

        /* Make message container background blend seamlessly */
        .q-message-container,
        [class*="message"] > div,
        .q-chat__messages,
        .q-chat-message {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        /* Ensure the chat area blends with messages */
        .q-chat,
        .q-chat__content,
        .q-chat__messages-container {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        /* ChatGPT/iMessage style message bubbles */
        .q-message-sent {{
            background-color: #F4B8C5 !important; /* Pink background for user */
            color: white !important;
            border-radius: 18px !important;
            margin: 4px 12px 4px 50px !important; /* Right side spacing */
            padding: 12px 16px !important;
            max-width: 80% !important;
            align-self: flex-end !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: pre-wrap !important;
        }}

        .q-message-received {{
            background-color: #f3f4f6 !important; /* Light grey for AI */
            color: #1f2937 !important; /* Dark text */
            border-radius: 18px !important;
            margin: 4px 50px 4px 12px !important; /* Left side spacing */
            padding: 12px 16px !important;
            max-width: 80% !important;
            align-self: flex-start !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: pre-wrap !important;
        }}

        /* Dark mode styling */
        body.body--dark .q-message-sent {{
            background-color: #F4B8C5 !important;
            color: white !important;
        }}

        body.body--dark .q-message-received {{
            background-color: #374151 !important;
            color: #f9fafb !important;
        }}

        /* Message container styling for proper chat layout */
        .q-message-container {{
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
        }}

        /* Ensure message container allows proper alignment */
        .q-message-container,
        [class*="message"] > div {{
            display: flex !important;
            flex-direction: column !important;
        }}

        /* Ensure text content follows bubble colors */
        .q-message-sent p {{
            color: white !important;
        }}

        .q-message-received p {{
            color: #374151 !important;
        }}

        body.body--dark .q-message-sent p {{
            color: white !important;
        }}

        body.body--dark .q-message-received p {{
            color: #f9fafb !important;
        }}

        /* Chat message text content */
        .q-message-sent div {{
            color: white !important;
        }}

        .q-message-received div {{
            color: #374151 !important;
        }}

        body.body--dark .q-message-sent div {{
            color: white !important;
        }}

        body.body--dark .q-message-received div {{
            color: #f9fafb !important;
        }}

        /* Theme-aware footer elements */
        .theme-aware-footer-btn,
        .q-footer .q-btn {{
            color: var(--q-primary) !important;
            background: rgba(244, 184, 197, 0.1) !important;
            border: 1px solid rgba(244, 184, 197, 0.3) !important;
            transition: all 0.3s ease !important;
        }}

        .theme-aware-footer-btn:hover,
        .q-footer .q-btn:hover {{
            background: rgba(244, 184, 197, 0.2) !important;
            border-color: rgba(244, 184, 197, 0.5) !important;
            transform: translateY(-1px) !important;
        }}

        body.body--dark .theme-aware-footer-btn,
        body.body--dark .q-footer .q-btn {{
            color: var(--q-primary) !important;
            background: rgba(244, 184, 197, 0.15) !important;
            border: 1px solid rgba(244, 184, 197, 0.4) !important;
        }}

        body.body--dark .theme-aware-footer-btn:hover,
        body.body--dark .q-footer .q-btn:hover {{
            background: rgba(244, 184, 197, 0.25) !important;
            border-color: rgba(244, 184, 197, 0.6) !important;
        }}

        /* Theme-aware input styling */
        .theme-aware-input .q-field__control {{
            background: rgba(255, 255, 255, 0.8) !important;
            border-radius: 24px !important;
        }}

        body.body--dark .theme-aware-input .q-field__control {{
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }}

        /* Ensure all interactive elements use theme colors */
        .q-btn {{
            transition: all 0.3s ease !important;
        }}

        /* Theme-aware page background */
        .q-page {{
            background: transparent !important;
        }}

        /* Proper scrollbar styling for both themes */
        ::-webkit-scrollbar {{
            width: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.1);
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--q-primary);
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--q-primary);
            opacity: 0.8;
        }}

        body.body--dark ::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.1);
        }}

        body.body--dark ::-webkit-scrollbar-thumb {{
            background: var(--q-accent);
        }}
    """)

    # Layout styling
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

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
            ui.chat_message(text=question, name="You", sent=True).props('bg-color=primary text-color=white')
            # Assistant response - grey styling
            response_message = ui.chat_message(name="MammoChat", sent=False).props('bg-color=grey-3 text-color=grey-9')

        # Scroll down after user message is sent
        await ui.run_javascript("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")

        # Minimal thinking indicator - use pink color directly
        with response_message:
            ui.spinner(type="dots", size="sm").props('color=pink').classes('opacity-60')

        logger.info("streaming_ai_response", history_length=len(messages)-1)

        # Stream AI response
        response = ""
        chunk_count = 0
        try:
            print(f"📨 [DEBUG] Starting to stream AI response for question: '{question[:50]}...'")
            async for chunk in ai_service.stream_chat(question, messages[:-1]):
                response += chunk
                chunk_count += 1
                print(f"📨 [DEBUG] Received chunk {chunk_count}: '{chunk}' (total: {len(response)})")

                # Update the message in real-time
                response_message.clear()
                with response_message:
                    ui.html(response, sanitize=False)
                ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

            print(f"📨 [DEBUG] AI response streaming completed - {chunk_count} chunks, {len(response)} chars")
            logger.info("ai_response_complete", chunks=chunk_count, length=len(response))
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
                ''', sanitize=False).classes('flex items-center')
                ui.label('Your journey, together').classes('text-xs sm:text-sm text-white opacity-80 ml-3 sm:ml-4')
                ui.label('Your journey, together').classes('text-xs sm:text-sm text-white opacity-80 hidden xs:inline')

            # Right side: Dark mode toggle
            with ui.row().classes('items-center gap-2 flex-shrink-0'):
                # Dark mode toggle
                ui.button(icon='dark_mode', on_click=lambda: dark.toggle()).props('flat dense color=white').classes('flex-shrink-0')

    # Spacious, comfortable message area
    with ui.column().classes("w-full max-w-3xl mx-auto flex-grow items-stretch py-6 px-4"):
        message_container = ui.column().classes("items-stretch")

        # Welcome message when app first loads - grey AI styling
        with message_container:
            welcome = ui.chat_message(name="MammoChat", sent=False).props('bg-color=grey-3 text-color=grey-9')
            with welcome:
                ui.label('''
Welcome to MammoChat!

I'm here to support you on your breast cancer journey. I can help you:

- Find clinical trials that match your situation
- Connect with communities of patients with similar experiences
- Understand information about treatments and options
- Navigate your healthcare with confidence

How can I support you today?
                '''.strip()).classes('whitespace-pre-wrap')

    # Theme-aware footer with input area
    with ui.footer().classes("q-footer"):
        with ui.row().classes("w-full items-center gap-3 px-4 py-3 max-w-4xl mx-auto"):
            # New conversation button - theme-aware styling
            ui.button(icon="add", on_click=new_conversation) \
                .props("round unelevated") \
                .classes("theme-aware-footer-btn") \
                .tooltip('Start a new conversation')

            # Text input - theme-aware styling
            text = (
                ui.textarea(placeholder="Share what's on your mind...")
                .props("outlined autogrow rounded")
                .classes("flex-grow theme-aware-input")
                .style("max-height: 120px;")
                .on("keydown.enter", send)
            )

            # Send button - theme-aware styling
            ui.button(icon="send", on_click=send) \
                .props("round unelevated") \
                .classes("theme-aware-footer-btn") \
                .tooltip('Send message')


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
