"""MammoChat NiceGUI 3.0 single-page chat interface."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from uuid import uuid4

from nicegui import events, ui

from ..config import AppConfig
from ..models.chat import ChatEventType, ConversationState
from ..services.auth_service import AuthService
from ..services.chat_service import ChatService
from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class ChatUI:
    """Modern chat interface built with NiceGUI."""

    def __init__(
        self,
        config: AppConfig,
        auth_service: AuthService,
        chat_service: ChatService,
        memory_service: MemoryService,
    ) -> None:
        self.config = config
        self.auth_service = auth_service
        self.chat_service = chat_service
        self.memory_service = memory_service
        self.conversation = ConversationState(conversation_id=str(uuid4()))

        self.is_streaming = False
        self.message_container: Any | None = None
        self.chat_scroll: Any | None = None
        self.typing_indicator: Any | None = None
        self.input_field: Any | None = None
        self.send_button: Any | None = None
        self.new_chat_button: Any | None = None
        self.dark_mode: Any | None = None
        self.dark_mode_button: Any | None = None

    def build(self) -> None:
        """Construct the full chat layout using NiceGUI 3 building blocks."""
        logger.info("Rendering chat SPA for MammoChat")

        default_dark_mode = self.config.ui.theme.lower() == "dark"
        self.dark_mode = ui.dark_mode(value=default_dark_mode)
        if default_dark_mode:
            self.dark_mode.enable()
        else:
            self.dark_mode.disable()

        with ui.column().classes(
            "min-h-screen w-full flex flex-col bg-rose-50 dark:bg-slate-950 "
            "text-slate-800 dark:text-slate-100 transition-colors duration-300"
        ):
            self._build_header()

            with ui.column().classes(
                "flex-1 w-full px-4 sm:px-6 lg:px-10 py-6 gap-6"
            ):
                self._build_message_panel()

            self._build_input_panel()

    def _build_header(self) -> None:
        """Build the branded header with controls."""
        with ui.column().classes(
            "w-full rounded-2xl border border-rose-100/60 dark:border-slate-800/60 "
            "bg-white/85 dark:bg-slate-900/70 shadow-sm px-5 sm:px-6 py-5 gap-4"
        ):
            with ui.row().classes(
                "w-full items-center justify-between gap-4 flex-wrap"
            ):
                with ui.row().classes("items-center gap-3"):
                    ui.image(self.config.ui.logo_full_path).classes("h-12 w-auto")
                    with ui.column().classes("gap-0"):
                        ui.label("MammoChat").classes(
                            "text-2xl sm:text-3xl font-semibold tracking-tight"
                        )
                        ui.label(self.config.ui.tagline).classes(
                            "text-sm sm:text-base text-slate-500 dark:text-slate-300"
                        )

                with ui.row().classes("items-center gap-3 flex-wrap"):
                    chip_label = (
                        "OncoCore connected"
                        if self.auth_service.is_authenticated
                        else "OncoCore offline"
                    )
                    chip_color = "primary" if self.auth_service.is_authenticated else "warning"
                    ui.chip(chip_label).props(f"color={chip_color} outline size=sm")

                    initial_icon = (
                        "light_mode" if self.dark_mode and self.dark_mode.value else "dark_mode"
                    )
                    self.dark_mode_button = ui.button(
                        icon=initial_icon,
                        on_click=self._toggle_dark_mode,
                    ).props("round flat color=primary")
                    self.dark_mode_button.tooltip(self.config.ui.dark_mode_tooltip)

    def _build_message_panel(self) -> None:
        """Create the scrollable chat history panel."""
        with ui.column().classes(
            "flex-1 w-full rounded-2xl border border-rose-100/60 dark:border-slate-800/60 "
            "bg-white/80 dark:bg-slate-900/70 shadow-sm"
        ):
            self.chat_scroll = ui.scroll_area().classes(
                "w-full flex-1 min-h-[45vh] max-h-[calc(100vh-18rem)] px-4 py-4"
            )
            with self.chat_scroll:
                self.message_container = ui.column().classes(
                    "w-full gap-4 items-stretch"
                )
                self._render_welcome_message()

    def _build_input_panel(self) -> None:
        """Pinned footer-like input panel for chat entry."""
        with ui.column().classes(
            "w-full bg-white/90 dark:bg-slate-950/80 border-t border-rose-100/60 "
            "dark:border-slate-800/70 backdrop-blur px-4 sm:px-6 lg:px-10 py-4 gap-3 "
            "sticky bottom-0"
        ):
            with ui.row().classes(
                "w-full gap-3 flex-col sm:flex-row items-stretch sm:items-end"
            ):
                self.new_chat_button = (
                    ui.button(
                        icon="add",
                        on_click=self._new_conversation,
                    )
                    .props("round color=primary unelevated")
                    .classes("h-12 w-12 sm:h-14 sm:w-14 shrink-0 shadow-md")
                )
                self.new_chat_button.tooltip(self.config.ui.new_conversation_tooltip)

                self.input_field = (
                    ui.textarea(placeholder=self.config.ui.input_placeholder)
                    .props("outlined autogrow clearable")
                    .classes(
                        "flex-1 w-full min-w-0 min-h-[3.25rem] max-h-40 rounded-2xl px-4 py-3 "
                        "bg-white dark:bg-slate-900/70 border border-rose-100/60 "
                        "dark:border-slate-800/70 shadow-inner"
                    )
                )
                self.input_field.on("keydown.enter", self._handle_enter_key)

                self.send_button = ui.button(
                    icon="send",
                    on_click=self._send_message,
                ).props("round color=primary unelevated").classes(
                    "h-12 w-12 sm:h-14 sm:w-14 shrink-0 shadow-md"
                )
                self.send_button.tooltip(self.config.ui.send_tooltip)

    def _render_welcome_message(self) -> None:
        """Display the introductory MammoChat greeting."""
        if not self.message_container:
            return
        with self.message_container:
            with ui.chat_message(
                name="MammoChat",
                avatar=self.config.ui.logo_icon_path,
                sent=False,
            ) as welcome:
                welcome.props("bg-color=grey-2 text-color=grey-9")
                welcome.classes("max-w-[80%] rounded-2xl shadow-sm gap-3")
                ui.label(self.config.ui.welcome_title).classes(
                    "text-lg md:text-xl font-semibold"
                )
                if self.config.ui.welcome_message:
                    ui.markdown(self.config.ui.welcome_message).classes(
                        "prose prose-rose dark:prose-invert max-w-none text-base leading-relaxed"
                    )

    def _render_user_message(self, message: str) -> None:
        """Render a user bubble using NiceGUI chat_message."""
        if not self.message_container:
            return
        with self.message_container:
            bubble = ui.chat_message(
                message,
                name="You",
                sent=True,
            )
            bubble.props("bg-color=pink-4 text-color=white")
            bubble.classes("max-w-[75%] ml-auto rounded-2xl shadow-md text-base")

    def _render_assistant_message(self) -> tuple[Any | None, Any | None]:
        """Create an assistant chat bubble and return the markdown element."""
        if not self.message_container:
            return None, None
        with self.message_container:
            with ui.chat_message(
                name="MammoChat",
                avatar=self.config.ui.logo_icon_path,
                sent=False,
            ) as bubble:
                bubble.props("bg-color=grey-1 text-color=grey-10")
                bubble.classes("max-w-[80%] rounded-2xl shadow-sm gap-3")
                markdown = ui.markdown("").classes(
                    "prose max-w-none text-[0.96rem]"
                )
        return bubble, markdown

    def _render_step_details(self, payload: dict[str, Any]) -> None:
        """Display auxiliary step information such as memory references."""
        references = payload.get("referenced") or payload.get(
            "referenced_memories"
        )
        if not references or not self.message_container:
            return

        with self.message_container:
            with ui.chat_message(
                name="MammoChat",
                avatar=self.config.ui.logo_icon_path,
                sent=False,
            ) as bubble:
                bubble.props("bg-color=blue-1 text-color=blue-9")
                bubble.classes("max-w-[80%] rounded-2xl gap-2 shadow-sm")
                ui.label("Context memories referenced").classes(
                    "text-sm font-semibold"
                )
                with ui.column().classes("gap-1 text-sm"):
                    for entry in references:
                        ui.markdown(f"- {entry}").classes(
                            "text-sm text-slate-600 dark:text-slate-300"
                        )

    async def _handle_enter_key(self, event: events.UIEventArguments) -> None:
        """Send the message when Enter is pressed without Shift."""
        shift_pressed = False
        if hasattr(event, "shift"):
            shift_pressed = bool(getattr(event, "shift", False))
        elif hasattr(event, "args") and isinstance(event.args, dict):
            shift_pressed = bool(event.args.get("shiftKey"))

        if shift_pressed:
            return
        await self._send_message()

    def _show_typing_indicator(self) -> None:
        """Show an animated typing indicator bubble."""
        if not self.message_container:
            return
        self._clear_typing_indicator()
        with self.message_container:
            with ui.chat_message(
                name="MammoChat",
                avatar=self.config.ui.logo_icon_path,
                sent=False,
            ) as indicator:
                indicator.props("bg-color=grey-2 text-color=grey-7")
                indicator.classes("max-w-[80%] rounded-2xl shadow-sm")
                with ui.row().classes(
                    "items-center gap-2 text-slate-500 dark:text-slate-300"
                ):
                    ui.spinner("dots", color="primary", size="sm")
                    ui.label(self.config.ui.thinking_text)
        self.typing_indicator = indicator

    def _clear_typing_indicator(self) -> None:
        """Remove the typing indicator if present."""
        if self.typing_indicator:
            try:
                self.typing_indicator.delete()
            except Exception:  # pragma: no cover - defensive cleanup during disconnects
                logger.debug("Typing indicator already cleaned up", exc_info=True)
            finally:
                self.typing_indicator = None

    async def _scroll_to_bottom(self) -> None:
        """Smoothly scroll the chat view to the most recent message."""
        if not self.chat_scroll:
            return
        await asyncio.sleep(0.05)
        self.chat_scroll.scroll_to(pixels=999999)

    async def _send_message(self) -> None:
        """Send a message and stream the assistant response."""
        if not self.input_field:
            return

        if self.is_streaming:
            ui.notify(
                "Please wait for the current response to complete",
                type="warning",
            )
            return

        message = (self.input_field.value or "").strip()
        if not message:
            ui.notify("Please type a message", type="warning")
            return

        logger.info("Sending user message (%d chars)", len(message))
        send_start = time.perf_counter()
        self.is_streaming = True

        self.input_field.value = ""
        self.input_field.disable()
        if self.send_button:
            self.send_button.disable()

        self._render_user_message(message)
        await self._scroll_to_bottom()

        self._show_typing_indicator()

        assistant_markdown = None
        assistant_content = ""
        chunk_counter = 0

        try:
            async for event in self.chat_service.stream_chat(
                self.conversation,
                message,
                selected_space_ids=self.conversation.memory_space_ids or None,
            ):
                if event.event_type == ChatEventType.MESSAGE_START:
                    self._clear_typing_indicator()
                    _, assistant_markdown = self._render_assistant_message()

                elif event.event_type == ChatEventType.MESSAGE_CHUNK:
                    chunk = event.payload.get("content", "")
                    if not chunk:
                        continue
                    assistant_content += chunk
                    chunk_counter += 1
                    if assistant_markdown:
                        assistant_markdown.content = assistant_content
                    if chunk_counter % 6 == 0:
                        await self._scroll_to_bottom()

                elif event.event_type == ChatEventType.MESSAGE_END:
                    payload_content = event.payload.get("content", "")
                    if assistant_markdown and not assistant_content:
                        assistant_markdown.content = payload_content
                    await self._scroll_to_bottom()
                    ui.notify(
                        self.config.ui.response_complete_notification,
                        type="positive",
                        position="top-right",
                        timeout=1000,
                    )

                elif event.event_type == ChatEventType.STEP:
                    self._render_step_details(event.payload)

                elif event.event_type == ChatEventType.ERROR:
                    raise RuntimeError(event.payload.get("message", "Chat service error"))

                elif event.event_type == ChatEventType.STREAM_END:
                    await self._scroll_to_bottom()

        except Exception as exc:  # pragma: no cover - UI feedback path
            logger.error("Error during message streaming: %s", exc, exc_info=True)
            self._show_error_message(str(exc))

        finally:
            self._clear_typing_indicator()
            self.is_streaming = False
            elapsed = time.perf_counter() - send_start
            logger.info("Message send completed in %.3fs", elapsed)

            if self.input_field:
                self.input_field.enable()
                focus_callable = getattr(self.input_field, "focus", None)
                if callable(focus_callable):
                    focus_callable()
                else:
                    self.input_field.run_method("focus")
            if self.send_button:
                self.send_button.enable()

            await self._scroll_to_bottom()

    def _show_error_message(self, message: str) -> None:
        """Display an error notification and inline bubble."""
        ui.notify(f"Error: {message}", type="negative", position="top", timeout=5000)
        if not self.message_container:
            return
        with self.message_container:
            with ui.chat_message(
                name="MammoChat",
                avatar=self.config.ui.logo_icon_path,
                sent=False,
            ) as bubble:
                bubble.props("bg-color=negative text-color=white")
                bubble.classes("max-w-[80%] rounded-2xl shadow-sm")
                ui.label(message)

    def _new_conversation(self) -> None:
        """Start a fresh conversation session."""
        previous_id = self.conversation.conversation_id
        self.conversation = ConversationState(conversation_id=str(uuid4()))
        logger.info(
            "New conversation created: %s -> %s",
            previous_id[:8],
            self.conversation.conversation_id[:8],
        )

        if self.message_container:
            self.message_container.clear()
            self._render_welcome_message()

        ui.notify(
            self.config.ui.new_conversation_notification,
            type="positive",
            position="top-right",
        )

    def _toggle_dark_mode(self) -> None:
        """Toggle global dark mode state and update icon."""
        if not self.dark_mode:
            return

        if self.dark_mode.value:
            self.dark_mode.disable()
            next_icon = "dark_mode"
        else:
            self.dark_mode.enable()
            next_icon = "light_mode"

        if self.dark_mode_button:
            self.dark_mode_button.props(f"icon={next_icon}")

