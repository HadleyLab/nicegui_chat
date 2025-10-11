"""AI service with HeySol client integration and Pydantic AI backend."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

import structlog
from pydantic import BaseModel, Field

from config import config

from ..utils.text_processing import strip_markdown

logger = structlog.get_logger()

# Connection pool configuration for performance optimization
HTTPX_CONNECTION_LIMITS = {
    "max_keepalive_connections": 20,
    "max_connections": 100,
    "keepalive_expiry": 30.0,
}

# Request timeout configuration
REQUEST_TIMEOUTS = {
    "connect": 10.0,
    "read": 60.0,
    "write": 10.0,
    "pool": 10.0,
}

# Import HeySol client if available
try:
    from heysol import HeySolClient
except ImportError:
    HeySolClient = None  # type: ignore[assignment,misc]

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
        DeepSeekProvider = None  # type: ignore[assignment,misc]

except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    DEEPSEEK_PROVIDER_AVAILABLE = False
    Agent = None  # type: ignore[assignment,misc]
    RunContext = None  # type: ignore[assignment,misc]
    OpenAIChatModel = None  # type: ignore[assignment,misc]
    DeepSeekProvider = None  # type: ignore[assignment,misc]


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
    """Service for AI chat interactions with HeySol memory integration and connection pooling."""

    def __init__(self):
        """Initialize AI service with optional HeySol client and HTTP connection pool."""
        self.api_key = config.deepseek_api_key
        self.model = config.deepseek_model
        self.base_url = config.deepseek_base_url
        self.heysol_api_key = config.heysol_api_key

        # Circuit breaker for network resilience
        self._failure_count = 0
        self._last_failure_time = 0
        self._circuit_open = False
        self._circuit_open_until = 0

        # Initialize persistent HTTP client with connection pooling
        self._http_client: Any | None = None
        self._initialize_http_client()

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

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should allow requests."""
        current_time = time.time()

        # Reset circuit breaker after timeout
        if self._circuit_open and current_time > self._circuit_open_until:
            logger.info("circuit_breaker_reset")
            self._circuit_open = False
            self._failure_count = 0

        return not self._circuit_open

    def _record_failure(self):
        """Record a failure for circuit breaker logic."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        # Open circuit after 3 failures in 60 seconds
        if self._failure_count >= 3:
            self._circuit_open = True
            self._circuit_open_until = time.time() + 60  # 60 second timeout
            logger.warning("circuit_breaker_opened", failures=self._failure_count)

    def _record_success(self):
        """Record a success to reset failure count."""
        if self._failure_count > 0:
            self._failure_count = max(0, self._failure_count - 1)

    def _initialize_http_client(self) -> None:
        """Initialize persistent HTTP client with connection pooling."""
        try:
            import httpx

            # Create persistent client with connection pooling for performance
            self._http_client = httpx.AsyncClient(
                limits=httpx.Limits(**HTTPX_CONNECTION_LIMITS),
                timeout=httpx.Timeout(**REQUEST_TIMEOUTS),
                follow_redirects=True,
            )
            logger.info("http_client_initialized", limits=HTTPX_CONNECTION_LIMITS)
        except Exception as e:
            logger.warning("http_client_init_failed", error=str(e))
            self._http_client = None

    async def close(self) -> None:
        """Close HTTP client connections."""
        if self._http_client:
            await self._http_client.aclose()
            logger.info("http_client_closed")

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
                            return [
                                ep.body for ep in result.episodes if hasattr(ep, "body")
                            ]
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

        # Check circuit breaker
        if not self._check_circuit_breaker():
            yield "⚠️ AI service temporarily unavailable due to repeated connection issues. Please try again later."
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
                        conversation_context.append(
                            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                        )

                # Run agent
                result = await self.agent.run(
                    message,
                    deps=deps,
                )

                # Stream the response
                output: AgentOutput = result.output

                # Strip markdown formatting for plain text output
                output.reply = strip_markdown(output.reply)

                # Yield the reply in chunks for streaming effect
                chunk_size = 20
                for i in range(0, len(output.reply), chunk_size):
                    yield output.reply[i : i + chunk_size]

                # If there are referenced memories, mention them
                if output.referenced_memories:
                    yield "\n\n_Context from your memories used._"

                return

            except Exception as e:
                logger.error("agent_run_failed", error=str(e))
                # Fall through to direct API call

        # Fallback to direct API streaming with connection pooling
        import json

        messages = [{"role": "system", "content": config.system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        # Use persistent HTTP client if available, otherwise create temporary one
        if self._http_client:
            client = self._http_client
            should_close = False
        else:
            import httpx

            # Add retry configuration for network resilience
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(**REQUEST_TIMEOUTS),
                transport=httpx.AsyncHTTPTransport(retries=2)
            )
            should_close = True

        try:
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

                # More robust streaming with error recovery
                streaming_interrupted = False
                try:
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
                except (httpx.ReadError, httpx.ConnectError) as stream_error:
                    logger.warning("streaming_connection_interrupted", error=str(stream_error))
                    streaming_interrupted = True
                    # Try to yield a partial error message
                    yield " [Connection interrupted - response may be incomplete]"
                except Exception as stream_error:
                    logger.error("streaming_unexpected_error", error=str(stream_error))
                    streaming_interrupted = True
                    yield " [Streaming error occurred]"

                if streaming_interrupted:
                    logger.info("streaming_recovered_from_error")

        except httpx.TimeoutException as e:
            logger.error("ai_service_timeout", error=str(e))
            self._record_failure()
            yield "⚠️ AI service request timed out. Please try again."
        except httpx.ConnectError as e:
            logger.error("ai_service_connection_error", error=str(e))
            self._record_failure()
            yield "⚠️ Unable to connect to AI service. Please check your internet connection."
        except httpx.ReadError as e:
            logger.error("ai_service_read_error", error=str(e))
            self._record_failure()
            yield "⚠️ Connection to AI service was interrupted. Please try again."
        except Exception as e:
            logger.error("ai_service_streaming_error", error=str(e))
            self._record_failure()
            yield f"⚠️ Error communicating with AI service: {str(e)}"
        else:
            # Success - record it for circuit breaker
            self._record_success()
        finally:
            # Only close if we created a temporary client
            if should_close:
                await client.aclose()
