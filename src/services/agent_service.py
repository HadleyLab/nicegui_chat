"""LLM agent orchestration built on Pydantic AI for chat generation."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

from ..config import DeepSeekConfig
from ..models.chat import ChatMessage, ConversationState, MessageRole
from ..models.memory import MemorySearchResult
from ..services.memory_service import MemoryService
from ..utils.exceptions import ChatServiceError


class AgentDependencies(BaseModel):
    """Dependencies provided to tool callbacks during agent execution."""
    selected_space_ids: List[str] = Field(default_factory=list)


class AgentOutput(BaseModel):
    """Structured response returned by the agent."""
    reply: str = Field(description="Assistant reply to present to the user")
    referenced_memories: List[str] = Field(
        default_factory=list,
        description="List of memory entries used in the response",
    )
    follow_up_actions: List[str] = Field(
        default_factory=list,
        description="Optional follow up actions to suggest to the user",
    )


class AgentResult(BaseModel):
    """Aggregated result returned to the chat service."""
    reply: str
    referenced_memories: List[str] = Field(default_factory=list)


class ChatAgent:
    """Wrapper around pydantic-ai to generate responses with DeepSeek and MCP tools."""

    def __init__(
        self,
        memory_service: MemoryService,
        *,
        config: DeepSeekConfig,
        model_name: Optional[str] = None,
    ) -> None:
        self._memory_service = memory_service
        self._config = config

        config.ensure_valid()

        resolved_model = model_name or config.model
        provider = DeepSeekProvider(api_key=config.api_key)
        model = OpenAIChatModel(model_name=resolved_model, provider=provider)

        instructions = self._build_system_prompt()
        self._agent: Agent[AgentDependencies, AgentOutput] = Agent(
            model,
            output_type=AgentOutput,
            deps_type=AgentDependencies,
            system_prompt=instructions,
        )

        # Register memory search tool
        @self._agent.tool
        async def memory_search(
            ctx: RunContext[AgentDependencies],
            query: str,
            limit: int = 5,
        ) -> List[str]:
            """Search the user's HeySol memory store for episodes related to the query."""
            deps = ctx.deps
            result = await self._memory_service.search(
                query,
                space_ids=deps.selected_space_ids or None,
                limit=limit,
            )
            return [episode.body for episode in result.episodes]

        # Register memory ingest tool
        @self._agent.tool
        async def memory_ingest(
            ctx: RunContext[AgentDependencies],
            note: str,
            space_id: Optional[str] = None,
        ) -> str:
            """Store a new note in the user's HeySol memory."""
            await self._memory_service.add(
                note,
                space_id=space_id,
                source="chat_agent",
            )
            return f"Memory stored: {note[:50]}..."

    def _build_system_prompt(self) -> str:
        """Build the system prompt with tool descriptions."""
        tools_desc = """
- `memory_search(query: str, limit: int = 5)`: Search memory for relevant episodes
- `memory_ingest(note: str, space_id: Optional[str] = None)`: Store new information in memory
"""
        return self._config.system_prompt.replace("{tools}", tools_desc)

    async def generate(
        self,
        conversation: ConversationState,
        user_message: str,
        *,
        selected_space_ids: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
        prefetch_memory: bool = True,
    ) -> AgentResult:
        """Generate a response using the LLM agent."""
        try:
            # Create dependencies
            deps = AgentDependencies(
                selected_space_ids=selected_space_ids or []
            )

            # Run the agent - let it handle the conversation internally
            # Don't pass message_history as it causes the error
            result = await self._agent.run(
                user_message,
                deps=deps,
            )

            # Extract output
            output = result.output
            
            return AgentResult(
                reply=output.reply,
                referenced_memories=output.referenced_memories,
            )

        except Exception as exc:
            raise ChatServiceError(f"Agent generation failed: {exc}") from exc
