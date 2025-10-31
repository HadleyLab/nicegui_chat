"""Modern NiceGUI-based chat interface."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from uuid import uuid4

from nicegui import ui

# Configure logging for verbose output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from ..config import AppConfig
from ..models.chat import ChatEventType, ConversationState
from ..services.auth_service import AuthService
from ..services.chat_service import ChatService
from ..services.memory_service import MemoryService

# Type aliases for NiceGUI elements
UIElement = Any  # NiceGUI elements don't have specific type annotations


class ChatUI:
    """Modern chat interface built with NiceGUI."""

    def __init__(
        self,
        config: AppConfig,
        auth_service: AuthService,
        chat_service: ChatService,
        memory_service: MemoryService,
    ):
        start_time = time.time()
        logger.info("Initializing ChatUI...")

        self.config = config
        self.auth_service: AuthService = auth_service
        self.chat_service: ChatService = chat_service
        self.memory_service: MemoryService = memory_service
        self.conversation = ConversationState(conversation_id=str(uuid4()))
        self.is_streaming = False
        self.current_assistant_message: UIElement | None = None
        self.dark_mode = ui.dark_mode(value=False)  # Start in light mode
        self.dark_mode_button: UIElement | None = None  # Will hold the button reference
        self.header_row: UIElement | None = None  # Will hold the header reference
        self.header_subtitle: UIElement | None = None
        self.header_buttons: list[UIElement] = []  # Will hold button references

        init_time = time.time() - start_time
        logger.info(f"ChatUI initialized in {init_time:.3f}s with conversation ID: {self.conversation.conversation_id}")

    def build(self) -> None:
        """Build the main chat interface."""
        build_start = time.time()
        logger.info("Building chat interface...")

        # Set MammoChat colors using new design system
        logger.debug("Setting custom color scheme")
        ui.colors(
            primary="#E91E63",  # Pink Rose - Primary brand color
            secondary="#FFE0B2",  # Warm Peach - Secondary accent
            accent="#C2185B",  # Deep Rose - Hover states
            dark="#212121",  # Charcoal - Primary text
            positive="#C5E1A5",  # Sage Green - Success states
            negative="#ef4444",  # Red for errors
            info="#1A237E",  # Navy Blue - Professional trust
            warning="#f59e0b",  # Amber for warnings
        )

        # Add custom CSS for the new design system
        logger.debug("Adding custom CSS styles")
        ui.add_head_html('''
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
            <style>
                * {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                }

                html, body {
                    overflow-x: hidden;
                    max-width: 100vw;
                    margin: 0;
                    padding: 0;
                }

                body {
                    background: linear-gradient(135deg, #E1BEE7 0%, #FCE4EC 30%, #FAFAFA 60%, #E1BEE7 100%);
                    background-size: 800% 800%;
                    animation: gradient-animation 30s ease infinite;
                }

                @keyframes gradient-animation {
                    0%, 100% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                }

                @keyframes float {
                    0%, 100% {
                        transform: translate(0, 0) scale(1);
                    }
                    33% {
                        transform: translate(30px, -30px) scale(1.1);
                    }
                    66% {
                        transform: translate(-20px, 20px) scale(0.9);
                    }
                }

                @keyframes float-delayed {
                    0%, 100% {
                        transform: translate(0, 0) scale(1);
                    }
                    33% {
                        transform: translate(-30px, 30px) scale(1.05);
                    }
                    66% {
                        transform: translate(20px, -20px) scale(0.95);
                    }
                }

                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }

                @keyframes slideUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }

                /* Floating blob decorations - matching Tailwind style */
                .floating-blob-1 {
                    position: fixed;
                    top: 5rem;
                    right: -200px;
                    width: 800px;
                    height: 800px;
                    background: linear-gradient(to bottom right, #fbcfe8, #fda4af, #fecdd3);
                    border-radius: 50%;
                    opacity: 0.4;
                    filter: blur(96px);
                    animation: float 20s ease-in-out infinite;
                    pointer-events: none;
                    z-index: 0;
                    overflow: hidden;
                }

                .floating-blob-2 {
                    position: fixed;
                    bottom: -200px;
                    left: -200px;
                    width: 600px;
                    height: 600px;
                    background: linear-gradient(to top right, #fda4af, #fbcfe8, #fda4af);
                    border-radius: 50%;
                    opacity: 0.4;
                    filter: blur(96px);
                    animation: float-delayed 25s ease-in-out infinite;
                    pointer-events: none;
                    z-index: 0;
                    overflow: hidden;
                }

                /* Custom scrollbar */
                ::-webkit-scrollbar {
                    width: 8px;
                }

                ::-webkit-scrollbar-track {
                    background: #f1f1f1;
                }

                ::-webkit-scrollbar-thumb {
                    background: #E91E63;
                    border-radius: 4px;
                }

                ::-webkit-scrollbar-thumb:hover {
                    background: #C2185B;
                }

                /* Focus states for accessibility */
                *:focus {
                    outline: 2px solid #E91E63;
                    outline-offset: 2px;
                }

                /* Card glassmorphism effect */
                .glass-card {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
                }

                /* Chat message animations */
                .message-enter {
                    animation: slideUp 0.5s ease-out;
                }

                /* Gradient text effect */
                .gradient-text {
                    background: linear-gradient(to right, #E91E63, #ec4899, #E91E63);
                    background-clip: text;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-size: 200% auto;
                    animation: gradient-shift 3s ease infinite;
                }

                @keyframes gradient-shift {
                    0%, 100% { background-position: 0% center; }
                    50% { background-position: 100% center; }
                }

                /* Button gradient animation */
                .gradient-button {
                    background: linear-gradient(to right, #ec4899, #f43f5e, #ec4899, #f43f5e);
                    background-size: 200% 100%;
                    background-position: left;
                    transition: background-position 2s ease, box-shadow 0.3s ease;
                }

                .gradient-button:hover {
                    background-position: right;
                    box-shadow: 0 10px 30px rgba(236, 72, 153, 0.3);
                }

                /* Responsive padding for chat area */
                @media (max-width: 768px) {
                    .chat-padding {
                        padding-left: 0.75rem !important;
                        padding-right: 0.75rem !important;
                    }
                    .input-padding {
                        padding-left: 0.75rem !important;
                        padding-right: 0.75rem !important;
                    }
                }

                @media (max-width: 425px) {
                    .chat-padding {
                        padding-left: 0 !important;
                        padding-right: 0 !important;
                    }
                    .input-padding {
                        padding-left: 0.25rem !important;
                        padding-right: 0.25rem !important;
                    }
                    /* Remove NiceGUI scroll area padding on mobile */
                    .q-scrollarea__content.absolute {
                        padding-left: 0 !important;
                        padding-right: 0 !important;
                    }
                }
            </style>
            <script>
                // Chat history localStorage functions
                window.saveChatMessage = function(message, isUser) {
                    const history = JSON.parse(localStorage.getItem('mammoChat_history') || '[]');
                    history.push({ message: message, isUser: isUser, timestamp: Date.now() });
                    localStorage.setItem('mammoChat_history', JSON.stringify(history));
                    console.log('Message saved to localStorage:', message.substring(0, 50));
                };

                window.loadChatHistory = function() {
                    return JSON.parse(localStorage.getItem('mammoChat_history') || '[]');
                };

                window.clearChatHistory = function() {
                    localStorage.removeItem('mammoChat_history');
                    console.log('Chat history cleared from localStorage');
                };
            </script>
        ''')

        # Add floating blob decorations
        ui.html('<div class="floating-blob-1"></div><div class="floating-blob-2"></div>', sanitize=False)

        # Main content
        logger.debug("Creating main layout structure")
        with ui.column().classes("w-full h-screen gap-0").style(
            "position: relative; z-index: 1; overflow-x: hidden; max-width: 100vw;"
        ):
            # Header
            logger.debug("Building header section")
            self._build_header()

            # Chat messages container
            logger.debug("Creating chat scroll area and container")
            with ui.scroll_area().classes("flex-grow w-full") as self.chat_scroll:
                # Add padding container - extra top padding for fixed header and bottom for fixed input
                with ui.column().classes("w-full chat-padding").style("padding: 6rem 1.5rem 8rem 1.5rem;"):
                    self.chat_container = ui.column().classes("w-full mx-auto gap-6").style(
                        "max-width: 900px;"
                    )

                # Add welcome message
                logger.debug("Adding welcome message")
                self._add_welcome_message()

            # Input area
            logger.debug("Building input area")
            self._build_input_area()

        build_time = time.time() - build_start
        logger.info(f"Chat interface built in {build_time:.3f}s")

    def _add_welcome_message(self) -> None:
        """Add the welcome message to the chat."""
        logger.debug("Adding welcome message to chat container")
        with self.chat_container:
            with ui.card().classes("message-enter").style(
                "background: white; "
                "border-radius: 1.5rem; padding: 2.5rem; border: 1px solid #FBCFE8; "
                "box-shadow: 0 4px 12px rgba(233, 30, 99, 0.08);"
            ):
                with ui.row().classes("items-center gap-3").style("margin-bottom: 1.5rem;"):
                    # Chat bubble with heart icon only
                    ui.html('''
                        <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56" fill="none">
                            <defs>
                                <mask id="welcome-chat-mask">
                                    <path d="M48 16C48 11.5817 44.4183 8 40 8H16C11.5817 8 8 11.5817 8 16V36C8 40.4183 11.5817 44 16 44H20V52L28 44H40C44.4183 44 48 40.4183 48 36V16Z" fill="white"></path>
                                    <path d="M28 20C28 16.6863 30.6863 14 34 14C35.6569 14 37.1569 14.6716 38.2426 15.7574C39.3284 14.6716 40.8284 14 42.4853 14C45.799 14 48.4853 16.6863 48.4853 20C48.4853 21.3062 48.0615 22.512 47.3431 23.4853L38.2426 32.5858L29.1421 23.4853C28.4237 22.512 28 21.3062 28 20Z" fill="black"></path>
                                </mask>
                                <linearGradient id="welcome-gradient" x1="8" y1="30" x2="48" y2="30" gradientUnits="userSpaceOnUse">
                                    <stop offset="0%" stop-color="#EC4899"></stop>
                                    <stop offset="100%" stop-color="#F43F5E"></stop>
                                </linearGradient>
                            </defs>
                            <path d="M48 16C48 11.5817 44.4183 8 40 8H16C11.5817 8 8 11.5817 8 16V36C8 40.4183 11.5817 44 16 44H20V52L28 44H40C44.4183 44 48 40.4183 48 36V16Z" fill="url(#welcome-gradient)" mask="url(#welcome-chat-mask)"></path>
                        </svg>
                    ''', sanitize=False)
                    ui.html(
                        f'<h2 class="gradient-text" style="font-size: 1.75rem; font-weight: 400; margin: 0;">{self.config.ui.welcome_title}</h2>',
                        sanitize=False
                    )

                ui.markdown(self.config.ui.welcome_message).style(
                    "color: #212121; font-weight: 300; line-height: 1.8; font-size: 1rem;"
                )
        logger.debug("Welcome message added successfully")

    def _build_header(self) -> None:
        """Build the header section with HIPAA badge."""
        logger.debug("Building header section with logo and controls")
        with ui.card().classes("w-full").props("flat").style(
            "position: fixed; top: 0; left: 0; right: 0; z-index: 50; "
            "background: rgba(255, 255, 255, 0.8) !important; "
            "backdrop-filter: blur(16px) saturate(180%) !important; "
            "-webkit-backdrop-filter: blur(16px) saturate(180%) !important; "
            "border-bottom: 1px solid rgba(229, 231, 235, 0.8); "
            "border-radius: 0 0 1rem 1rem; "
            "box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04); "
            "margin: 0; padding: 0;"
        ):
            with ui.row().classes("w-full items-center justify-between").style(
                "max-width: 1800px; margin: 0 auto; padding: 0.75rem 2rem;"
            ):
                with ui.row().classes("items-center gap-4"):
                    # MammoChat logo
                    logger.debug("Adding MammoChat logo to header")
                    ui.html('''
                        <div class="flex items-center gap-3 scale-75 sm:scale-100 -ml-12 sm:ml-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="250" height="64" viewBox="0 0 250 64" fill="none">
                                <defs>
                                    <mask id="chat-mask">
                                        <path d="M48 16C48 11.5817 44.4183 8 40 8H16C11.5817 8 8 11.5817 8 16V36C8 40.4183 11.5817 44 16 44H20V52L28 44H40C44.4183 44 48 40.4183 48 36V16Z" fill="white"></path>
                                        <path d="M28 20C28 16.6863 30.6863 14 34 14C35.6569 14 37.1569 14.6716 38.2426 15.7574C39.3284 14.6716 40.8284 14 42.4853 14C45.799 14 48.4853 16.6863 48.4853 20C48.4853 21.3062 48.0615 22.512 47.3431 23.4853L38.2426 32.5858L29.1421 23.4853C28.4237 22.512 28 21.3062 28 20Z" fill="black"></path>
                                    </mask>
                                    <linearGradient id="brand-gradient" x1="0" y1="32" x2="250" y2="32" gradientUnits="userSpaceOnUse">
                                        <stop offset="0%" stop-color="#EC4899"></stop>
                                        <stop offset="100%" stop-color="#F43F5E"></stop>
                                    </linearGradient>
                                </defs>
                                <g id="logo-icon">
                                    <path d="M48 16C48 11.5817 44.4183 8 40 8H16C11.5817 8 8 11.5817 8 16V36C8 40.4183 11.5817 44 16 44H20V52L28 44H40C44.4183 44 48 40.4183 48 36V16Z" fill="url(#brand-gradient)" mask="url(#chat-mask)"></path>
                                </g>
                                <g id="logo-text">
                                    <text x="68" y="40" font-family="Inter, sans-serif" font-size="28" font-weight="700" fill="url(#brand-gradient)">Mammo</text>
                                    <text x="175" y="40" font-family="Inter, sans-serif" font-size="28" font-weight="700" fill="url(#brand-gradient)">Chat</text>
                                    <text x="238" y="32" font-family="Inter, sans-serif" font-size="16" font-weight="700" fill="url(#brand-gradient)">™</text>
                                </g>
                            </svg>
                        </div>
                    ''', sanitize=False)
                    # Tagline - hidden on small screens
                    ui.label("Your journey, together").classes("text-sm gt-xs").style("color: #757575; font-weight: 300;")

                # HIPAA Compliant Badge on the right
                logger.debug("Adding HIPAA badge to header")
                ui.html('''
                    <div style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.25rem 1rem;
                                border-radius: 9999px; background: linear-gradient(to right, #FCE4EC, #fda4af);
                                border: 1px solid #FBCFE8; color: #BE185D; font-size: 0.75rem; font-weight: 500;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        HIPAA Compliant
                    </div>
                ''', sanitize=False)
        logger.debug("Header section completed")


    def _toggle_dark_mode(self) -> None:
        """Toggle dark mode and update the button icon."""
        current_mode = "dark" if self.dark_mode.value else "light"
        new_mode = "light" if self.dark_mode.value else "dark"

        logger.info(f"Toggling dark mode: {current_mode} -> {new_mode}")

        if self.dark_mode.value:
            self.dark_mode.disable()
            if self.dark_mode_button:
                self.dark_mode_button.props(
                    remove="icon=dark_mode", add="icon=light_mode"
                )
                logger.debug("Dark mode disabled, light mode icon set")
        else:
            self.dark_mode.enable()
            if self.dark_mode_button:
                self.dark_mode_button.props(
                    remove="icon=light_mode", add="icon=dark_mode"
                )
                logger.debug("Dark mode enabled, dark mode icon set")

    def _build_input_area(self) -> None:
        """Build the input area with gradient border."""
        logger.debug("Building input area with text field and send button")
        with ui.card().classes("w-full").props("flat").style(
            "position: fixed; bottom: 0; left: 0; right: 0; z-index: 50; "
            "background: rgba(255, 255, 255, 0.8) !important; "
            "backdrop-filter: blur(16px) saturate(180%) !important; "
            "-webkit-backdrop-filter: blur(16px) saturate(180%) !important; "
            "border-top: 1px solid rgba(229, 231, 235, 0.8); "
            "border-radius: 1rem 1rem 0 0; "
            "box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.04); "
            "margin: 0; padding: 0;"
        ):
            # Centered container with max-width
            with ui.column().classes("w-full input-padding").style(
                "max-width: 1800px; margin: 0 auto; padding: 1.5rem;"
            ):
                # Input row with new conversation button
                with ui.row().classes("w-full items-center gap-3").style("max-width: 900px; margin: 0 auto;"):
                    # New conversation button - gradient with plus icon (matches input height)
                    new_conv_btn = ui.button(on_click=self._new_conversation).props(
                        "round flat"
                    ).style(
                        "background: linear-gradient(to right, lab(56.9303 76.8162 -8.07021) 0%, lab(56.101 79.4328 31.4532) 100%); "
                        "color: white; width: 3rem; height: 3rem; "
                        "min-width: 3rem; min-height: 3rem; padding: 0; "
                        "transition: transform 0.2s ease, box-shadow 0.2s ease;"
                    )
                    new_conv_btn.tooltip(self.config.ui.new_conversation_tooltip)
                    with new_conv_btn:
                        ui.html('''
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                                 fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                 stroke-linejoin="round" style="color: white;">
                                <line x1="12" y1="5" x2="12" y2="19"></line>
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                            </svg>
                        ''', sanitize=False)
                    logger.debug("New conversation button added to input area")

                    # Input container with gray background
                    with ui.row().classes("flex-grow items-center gap-2").style(
                        "background: #f3f4f6; border-radius: 9999px; "
                        "padding: 0.5rem 1rem; border: 1px solid #d1d5db; "
                        "min-height: 3rem; align-items: center;"
                    ):
                        self.input_field = (
                            ui.input(placeholder=self.config.ui.input_placeholder)
                            .props("borderless dense")
                            .classes("flex-grow")
                            .style(
                                "background: transparent; font-weight: 300; font-size: 0.875rem; "
                                "color: #6b7280; align-self: center;"
                            )
                            .on(
                                "keydown.enter",
                                lambda: self._send_message() if not self.is_streaming else None,
                            )
                        )
                        logger.debug("Input field created with enter key handler")

                        # Send button - gradient style
                        send_btn = ui.button(icon="send", on_click=self._send_message).props(
                            "round flat"
                        ).style(
                            "background: linear-gradient(to right, lab(56.9303 76.8162 -8.07021) 0%, lab(56.101 79.4328 31.4532) 100%); "
                            "color: white; width: 2rem; height: 2rem; "
                            "min-width: 2rem; min-height: 2rem; padding: 0; "
                            "transition: transform 0.2s ease, box-shadow 0.2s ease; "
                            "align-self: center; flex-shrink: 0;"
                        )
                        send_btn.tooltip(self.config.ui.send_tooltip)
                        # Update button to use smaller icon
                        send_btn.props(remove="icon=send")
                        with send_btn:
                            ui.html('''
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                                     fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                     stroke-linejoin="round" class="lucide lucide-send" style="color: white;">
                                    <path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"></path>
                                    <path d="m21.854 2.147-10.94 10.939"></path>
                                </svg>
                            ''', sanitize=False)
        logger.debug("Input area completed")

    async def _send_message(self) -> None:
        """Send a message and handle the response using pure NiceGUI patterns."""
        send_start = time.time()
        logger.info("Starting message send process...")

        if self.is_streaming:
            logger.warning("Message send blocked - already streaming")
            ui.notify(
                "Please wait for the current response to complete", type="warning"
            )
            return

        message = self.input_field.value.strip()
        if not message:
            logger.warning("Empty message - user prompted to type message")
            ui.notify("Please type a message", type="warning")
            return

        logger.info(f"Processing user message: {len(message)} characters")

        # Clear input
        self.input_field.value = ""
        self.is_streaming = True
        logger.debug("Input cleared and streaming state set")

        # Display user message
        logger.debug("Displaying user message in chat")
        with self.chat_container, ui.row().classes("w-full justify-end message-enter"):
            with ui.card().props("flat").style(
                "background: linear-gradient(to right, lab(56.9303 76.8162 -8.07021) 0%, lab(56.101 79.4328 31.4532) 100%); border: 1px solid #FBCFE8; border-radius: 1.5rem 0.25rem 1.5rem 1.5rem; "
                "padding: 1.25rem 1.75rem; box-shadow: 0 4px 12px rgba(233, 30, 99, 0.1); max-width: 75%; "
            ):
                ui.label(message).style("color: #ffffff; font-weight: 300; line-height: 1.7; font-size: 1rem;")

        # Save user message to localStorage
        ui.run_javascript(f'saveChatMessage({repr(message)}, true);')

        # Scroll to bottom
        await asyncio.sleep(0.1)
        self.chat_scroll.scroll_to(pixels=10000)
        logger.debug("Scrolled to bottom after user message")

        # Show typing indicator
        logger.debug("Displaying typing indicator")
        with self.chat_container:
            typing_row = ui.row().classes("w-full items-start message-enter").style("gap: 8px;")
            with typing_row:
                # Bot avatar
                ui.html('''
                    <div style="width: 2rem; height: 2rem; border-radius: 9999px;
                                background: linear-gradient(to bottom right, #ec4899, #f43f5e);
                                display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                             stroke-linejoin="round" style="color: white;">
                            <path d="M12 8V4H8"></path>
                            <rect width="16" height="12" x="4" y="8" rx="2"></rect>
                            <path d="M2 14h2"></path>
                            <path d="M20 14h2"></path>
                            <path d="M15 13v2"></path>
                            <path d="M9 13v2"></path>
                        </svg>
                    </div>
                ''', sanitize=False)
                with ui.card().props("flat").style(
                    "background: white; "
                    "border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 0.25rem 1.5rem 1.5rem 1.5rem; "
                    "padding: 1.25rem 1.75rem; max-width: 75%;"
                ):
                    with ui.row().classes("gap-2 items-center"):
                        ui.spinner("dots", size="sm").style("color: white;")
                        ui.label(self.config.ui.thinking_text).style("color: white; font-weight: 300; font-size: 1rem;")

        # Stream response
        assistant_content = ""
        assistant_label = None
        chunk_count = 0

        logger.info("Starting chat service stream...")
        try:
            async for event in self.chat_service.stream_chat(
                self.conversation,
                message,
                selected_space_ids=None,
            ):
                if event.event_type == ChatEventType.MESSAGE_START:
                    logger.debug("Received MESSAGE_START event")
                    # Remove typing indicator
                    typing_row.clear()
                    typing_row.delete()

                    # Create assistant message bubble with gradient background
                    with self.chat_container:
                        message_row = ui.row().classes("w-full items-start message-enter").style("gap: 4px;")
                        with message_row:
                            # Bot avatar
                            ui.html('''
                                <div style="width: 2rem; height: 2rem; border-radius: 9999px;
                                            background: linear-gradient(to bottom right, #ec4899, #f43f5e);
                                            display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                                         fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                         stroke-linejoin="round" style="color: white;">
                                        <path d="M12 8V4H8"></path>
                                        <rect width="16" height="12" x="4" y="8" rx="2"></rect>
                                        <path d="M2 14h2"></path>
                                        <path d="M20 14h2"></path>
                                        <path d="M15 13v2"></path>
                                        <path d="M9 13v2"></path>
                                    </svg>
                                </div>
                            ''', sanitize=False)
                            with ui.card().props("flat").style(
                                "background: linear-gradient(to right, lab(56.9303 76.8162 -8.07021) 0%, lab(56.101 79.4328 31.4532) 100%); "
                                "border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 1.5rem 0.25rem 1.5rem 1.5rem; "
                                "padding: 1.25rem 1.75rem; box-shadow: 0 4px 12px rgba(233, 30, 99, 0.2); max-width: 75%;"
                            ):
                                assistant_label = ui.markdown("").style("color: white; font-weight: 300; line-height: 1.7; font-size: 1rem;")

                elif event.event_type == ChatEventType.MESSAGE_CHUNK:
                    chunk = event.payload.get("content", "")
                    assistant_content += chunk
                    chunk_count += 1
                    if assistant_label:
                        assistant_label.content = assistant_content

                    # Scroll to bottom
                    await asyncio.sleep(0.01)
                    self.chat_scroll.scroll_to(pixels=10000)
                    if chunk_count % 10 == 0:  # Log every 10 chunks
                        logger.debug(f"Processed {chunk_count} chunks, content length: {len(assistant_content)}")

                elif event.event_type == ChatEventType.MESSAGE_END:
                    logger.info(f"Message streaming completed - {chunk_count} chunks, {len(assistant_content)} total characters")

                    # Save assistant message to localStorage
                    ui.run_javascript(f'saveChatMessage({repr(assistant_content)}, false);')

                    ui.notify(
                        self.config.ui.response_complete_notification,
                        type="positive",
                        position="top-right",
                        timeout=1000,
                    )

                elif event.event_type == ChatEventType.STEP:
                    logger.debug("Received STEP event from chat service")
                    # Handle memory references if needed
                    pass

        except Exception as e:
            logger.error(f"Error during message streaming: {e!s}", exc_info=True)
            # Show error message using notification
            ui.notify(f"Error: {e!s}", type="negative", position="top", timeout=5000)

            # Also display in chat
            with self.chat_container:
                with ui.row().classes("w-full"):
                    with (
                        ui.card()
                        .props("flat")
                        .classes(
                            "rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-6"
                        )
                    ):
                        ui.label(f"Error: {e!s}").classes(
                            "text-red-600 dark:text-red-400"
                        )

        finally:
            self.is_streaming = False
            send_time = time.time() - send_start
            logger.info(f"Message send completed in {send_time:.3f}s - {chunk_count} chunks processed")

    def _new_conversation(self) -> None:
        """Start a new conversation session."""
        old_conversation_id = self.conversation.conversation_id
        logger.info(f"Starting new conversation from {old_conversation_id[:8]}...")

        # Clear chat history from localStorage and UI
        ui.run_javascript('clearChatHistory();')
        self.chat_container.clear()

        # Just refresh the conversation ID, keep the welcome message
        self.conversation = ConversationState(conversation_id=str(uuid4()))
        new_conversation_id = self.conversation.conversation_id

        logger.info(f"New conversation created: {old_conversation_id[:8]}... -> {new_conversation_id[:8]}...")
        ui.notify(
            self.config.ui.new_conversation_notification,
            type="positive",
            position="top-right",
        )
