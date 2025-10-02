"""Modern NiceGUI-based chat interface."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from nicegui import ui

from ..config import AppConfig
from ..models.chat import ChatEventType, ConversationState
from ..services.auth_service import AuthService
from ..services.chat_service import ChatService
from ..services.memory_service import MemoryService


class ChatUI:
    """Modern chat interface built with NiceGUI."""

    def __init__(
        self,
        config: AppConfig,
        auth_service: AuthService,
        chat_service: ChatService,
        memory_service: MemoryService,
    ):
        self.config = config
        self.auth_service = auth_service
        self.chat_service = chat_service
        self.memory_service = memory_service
        self.conversation = ConversationState(conversation_id=str(uuid4()))
        self.is_streaming = False
        self.current_assistant_message = None
        self.dark_mode = ui.dark_mode(value=False)  # Start in light mode
        self.dark_mode_button = None  # Will hold the button reference
        self.header_row = None  # Will hold the header reference
        self.header_subtitle = None
        self.header_buttons = []  # Will hold button references

    def build(self):
        """Build the main chat interface."""
        # Set MammoChat colors using NiceGUI color system
        ui.colors(
            primary='#F4B8C5',      # Rose Quartz - soft pink
            secondary='#E8A0B8',    # Soft Mauve
            accent='#E8A0B8',       # Soft Mauve for accents
            dark='#334155',         # Charcoal for dark mode
            positive='#10b981',     # Default green for success
            negative='#ef4444',     # Default red for errors
            info='#3b82f6',         # Default blue for info
            warning='#f59e0b',      # Default amber for warnings
        )
        
        # Main content
        with ui.column().classes('w-full h-screen gap-0'):
            # Header
            self._build_header()
            
            # Chat messages container
            with ui.scroll_area().classes('flex-grow w-full p-4') as self.chat_scroll:
                self.chat_container = ui.column().classes('w-full max-w-4xl mx-auto gap-4')
                
                # Add welcome message
                self._add_welcome_message()
            
            # Input area
            self._build_input_area()

    def _add_welcome_message(self):
        """Add the welcome message to the chat."""
        with self.chat_container:
            with ui.card().props('bordered'):
                with ui.row().classes('items-center gap-3'):
                    ui.html(f'<img src="{self.config.ui.logo_icon_path}" style="height: 32px; width: auto;" />')
                    ui.label(self.config.ui.welcome_title).classes('text-xl font-bold')
                
                ui.markdown(self.config.ui.welcome_message)

    def _build_header(self):
        """Build the header section."""
        with ui.card().classes('w-full').props('flat'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.row().classes('items-center gap-3'):
                    # MammoChat logo
                    ui.html('<img src="/branding/logo-full-color.svg" style="height: 48px; width: auto;" />')
                    # Tagline - hidden on small screens
                    ui.label('Your journey, together').classes('gt-xs')
                
                with ui.row().classes('gap-2'):
                    # Single dark mode toggle button
                    self.dark_mode_button = ui.button(
                        icon='light_mode',
                        on_click=self._toggle_dark_mode
                    ).props('flat round')
                    self.dark_mode_button.tooltip(self.config.ui.dark_mode_tooltip)
                    
                    ui.button(
                        icon='refresh',
                        on_click=self._new_conversation
                    ).props('flat round').tooltip(self.config.ui.new_conversation_tooltip)
                    
                    ui.button(
                        icon='logout',
                        on_click=self._logout
                    ).props('flat round').tooltip(self.config.ui.logout_tooltip)
    
    def _toggle_dark_mode(self):
        """Toggle dark mode and update the button icon."""
        if self.dark_mode.value:
            self.dark_mode.disable()
            if self.dark_mode_button:
                self.dark_mode_button.props(remove='icon=dark_mode', add='icon=light_mode')
        else:
            self.dark_mode.enable()
            if self.dark_mode_button:
                self.dark_mode_button.props(remove='icon=light_mode', add='icon=dark_mode')

    def _build_input_area(self):
        """Build the input area."""
        with ui.card().classes('w-full').props('flat'):
            with ui.row().classes('w-full p-2 gap-3 items-center max-w-4xl mx-auto'):
                self.input_field = ui.input(
                    placeholder=self.config.ui.input_placeholder
                ).props('outlined rounded dense').classes('flex-grow').on(
                    'keydown.enter',
                    lambda: self._send_message() if not self.is_streaming else None
                )
                
                # Send button
                ui.button(
                    icon='send',
                    on_click=self._send_message
                ).props('round color=primary').tooltip(self.config.ui.send_tooltip)

    async def _send_message(self):
        """Send a message and handle the response using pure NiceGUI patterns."""
        if self.is_streaming:
            ui.notify('Please wait for the current response to complete', type='warning')
            return
        
        message = self.input_field.value.strip()
        if not message:
            ui.notify('Please type a message', type='warning')
            return
        
        # Clear input
        self.input_field.value = ''
        self.is_streaming = True
        
        # Display user message
        with self.chat_container:
            with ui.row().classes('w-full justify-end'):
                with ui.card().classes('max-w-[70%] bg-primary text-white').props('bordered'):
                    ui.label(message)
        
        # Scroll to bottom
        await asyncio.sleep(0.1)
        self.chat_scroll.scroll_to(pixels=10000)
        
        # Show typing indicator
        with self.chat_container:
            typing_row = ui.row().classes('w-full')
            with typing_row:
                with ui.card().props('flat'):
                    with ui.row().classes('gap-2 items-center'):
                        ui.spinner('dots', size='sm', color='primary')
                        ui.label(self.config.ui.thinking_text)
        
        # Stream response
        assistant_content = ""
        assistant_label = None
        
        try:
            async for event in self.chat_service.stream_chat(
                self.conversation,
                message,
                selected_space_ids=None,
            ):
                if event.event_type == ChatEventType.MESSAGE_START:
                    # Remove typing indicator
                    typing_row.clear()
                    typing_row.delete()
                    
                    # Create assistant message bubble
                    with self.chat_container:
                        with ui.row().classes('w-full'):
                            with ui.card().classes('max-w-[70%]').props('bordered'):
                                assistant_label = ui.markdown('')
                
                elif event.event_type == ChatEventType.MESSAGE_CHUNK:
                    chunk = event.payload.get('content', '')
                    assistant_content += chunk
                    if assistant_label:
                        assistant_label.content = assistant_content
                    
                    # Scroll to bottom
                    await asyncio.sleep(0.01)
                    self.chat_scroll.scroll_to(pixels=10000)
                
                elif event.event_type == ChatEventType.MESSAGE_END:
                    ui.notify(
                        self.config.ui.response_complete_notification,
                        type='positive',
                        position='top-right',
                        timeout=1000
                    )
                
                elif event.event_type == ChatEventType.STEP:
                    # Handle memory references if needed
                    pass
        
        except Exception as e:
            # Show error message using notification
            ui.notify(f'Error: {str(e)}', type='negative', position='top', timeout=5000)
            
            # Also display in chat
            with self.chat_container:
                with ui.row().classes('w-full'):
                    with ui.card().props('flat').classes(
                        'rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-6'
                    ):
                        ui.label(f'Error: {str(e)}').classes('text-red-600 dark:text-red-400')
        
        finally:
            self.is_streaming = False

    def _new_conversation(self):
        """Start a new conversation."""
        self.conversation = ConversationState(conversation_id=str(uuid4()))
        self.chat_container.clear()
        self._add_welcome_message()  # Re-add welcome message
        ui.notify(
            self.config.ui.new_conversation_notification,
            type='positive',
            position='top-right'
        )

    def _logout(self):
        """Logout the user."""
        self.auth_service.logout()
        ui.notify(
            self.config.ui.logout_notification,
            type='info',
            position='top'
        )
        # Reload the page to return to initial state
        ui.navigate.reload()
