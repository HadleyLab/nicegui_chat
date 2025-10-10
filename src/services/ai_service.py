"""AI service with HeySol client integration and Pydantic AI backend."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import structlog
from pydantic import BaseModel, Field

from config import config

logger = structlog.get_logger()

# Import HeySol client if available
try:
    from heysol import HeySolClient
except ImportError:
    HeySolClient = None  # type: ignore[assignment]

# Import Pydantic AI if available
try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.openai import OpenAIChatModel

    PYDANTIC_AI_AVAILABLE = True

    # Try to import DeepSeek provider
    try:
        from pydantic_ai.providers.deepseek import DeepSeekProvider
        DEEPSEEK_PROVIDER_AVAILABLE = True
    except ImportError:
        DEEPSEEK_PROVIDER_AVAILABLE = False
        DeepSeekProvider = None  # type: ignore[assignment]

except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    DEEPSEEK_PROVIDER_AVAILABLE = False
    Agent = None  # type: ignore[assignment]
    RunContext = None  # type: ignore[assignment]
    OpenAIChatModel = None  # type: ignore[assignment]
    DeepSeekProvider = None  # type: ignore[assignment]


class AgentDependencies(BaseModel):  # type: ignore[misc]
    """Dependencies provided to tool callbacks during agent execution."""

    heysol_client: Any | None = None
    space_ids: list[str] = Field(default_factory=list)


class AgentOutput(BaseModel):  # type: ignore[misc]
    """Structured response returned by the agent."""

    reply: str = Field(description="Assistant reply to present to the user")
    referenced_memories: list[str] = Field(
        default_factory=list,
        description="List of memory entries used in the response",
    )


class AIService:
    """Service for AI chat interactions with HeySol memory integration."""

    def __init__(self):
        """Initialize AI service with optional HeySol client."""
        self.api_key = config.deepseek_api_key
        self.model = config.deepseek_model
        self.base_url = config.deepseek_base_url
        self.heysol_api_key = config.heysol_api_key

        # Initialize HeySol client if API key is available
        self.heysol_client: Any | None = None
        if self.heysol_api_key and HeySolClient is not None:
            try:
                self.heysol_client = HeySolClient(api_key=self.heysol_api_key)
                logger.info("heysol_client_initialized")
            except Exception as e:
                logger.warning("heysol_client_init_failed", error=str(e))

        # Initialize Pydantic AI agent if available
        self.agent: Any | None = None
        if PYDANTIC_AI_AVAILABLE and self.api_key:
            self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize Pydantic AI agent with tools."""
        if not PYDANTIC_AI_AVAILABLE or Agent is None or OpenAIChatModel is None:
            return

        try:
            # Use DeepSeekProvider if available, otherwise use OpenAI-compatible API
            if DEEPSEEK_PROVIDER_AVAILABLE and DeepSeekProvider is not None:
                provider = DeepSeekProvider(api_key=self.api_key)
                model = OpenAIChatModel(model_name=self.model, provider=provider)
            else:
                # Fallback: use OpenAIChatModel with just model name
                model = OpenAIChatModel(model_name=self.model)

            self.agent = Agent(
                model,
                output_type=AgentOutput,
                deps_type=AgentDependencies,
                system_prompt=config.system_prompt,
            )

            # Register memory search tool if HeySol is available
            if self.heysol_client:
                @self.agent.tool  # type: ignore[misc]
                async def memory_search(
                    ctx: RunContext[AgentDependencies],  # type: ignore[valid-type]
                    query: str,
                    limit: int = 5,
                ) -> list[str]:
                    """Search the user's HeySol memory store for episodes related to the query."""
                    deps = ctx.deps
                    if deps.heysol_client is None:
                        return []

                    try:
                        result = deps.heysol_client.search(
                            query,
                            space_ids=deps.space_ids or None,
                            limit=limit,
                        )
                        # Extract episode bodies from search results
                        if hasattr(result, "episodes"):
                            return [ep.body for ep in result.episodes if hasattr(ep, "body")]
                        return []
                    except Exception as e:
                        logger.error("memory_search_failed", error=str(e))
                        return []

                @self.agent.tool  # type: ignore[misc]
                async def memory_ingest(
                    ctx: RunContext[AgentDependencies],  # type: ignore[valid-type]
                    note: str,
                    space_id: str | None = None,
                ) -> str:
                    """Store a new note in the user's HeySol memory."""
                    deps = ctx.deps
                    if deps.heysol_client is None:
                        return "Memory storage unavailable"

                    try:
                        deps.heysol_client.ingest(
                            note,
                            space_id=space_id,
                            source="chat_agent",
                        )
                        return f"Memory stored: {note[:50]}..."
                    except Exception as e:
                        logger.error("memory_ingest_failed", error=str(e))
                        return f"Failed to store memory: {str(e)}"

            logger.info("pydantic_ai_agent_initialized")
        except Exception as e:
            logger.error("agent_init_failed", error=str(e))
            self.agent = None

    async def stream_chat(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        space_ids: list[str] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat responses using Pydantic AI agent or fallback to direct API.

        Args:
            message: User's message
            history: Previous conversation history
            space_ids: Optional list of HeySol space IDs to search

        Yields:
            Response text chunks
        """
        if not self.api_key:
            yield "⚠️ AI service not configured. Please set DEEPSEEK_API_KEY in your .env file."
            return

        # Try using Pydantic AI agent first
        if self.agent is not None:
            try:
                deps = AgentDependencies(
                    heysol_client=self.heysol_client,
                    space_ids=space_ids or [],
                )

                # Build conversation context
                conversation_context = []
                if history:
                    for msg in history:
                        conversation_context.append(f"{msg.get('role', 'user')}: {msg.get('content', '')}")

                # Run agent
                result = await self.agent.run(
                    message,
                    deps=deps,
                )

                # Stream the response
                output: AgentOutput = result.output

                # Yield the reply in chunks for streaming effect
                chunk_size = 20
                for i in range(0, len(output.reply), chunk_size):
                    yield output.reply[i:i + chunk_size]

                # If there are referenced memories, mention them
                if output.referenced_memories:
                    yield "\n\n_Context from your memories used._"

                return

            except Exception as e:
                logger.error("agent_run_failed", error=str(e))
                # Fall through to direct API call

        # Fallback to direct API streaming
        import json

        import httpx

        messages = [{"role": "system", "content": config.system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                        "temperature": 0.7,
                    },
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPStatusError as e:
            logger.error("ai_service_http_error", status_code=e.response.status_code)
            yield f"⚠️ Error communicating with AI service (Status {e.response.status_code})"
        except Exception as e:
            logger.error("ai_service_error", error=str(e))
            yield f"⚠️ Unexpected error: {str(e)}"