"""AI service for chat interactions."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import structlog

from src.config import config

logger = structlog.get_logger()


class AIService:
    """Service for AI chat interactions."""

    def __init__(self):
        """Initialize AI service."""
        self.api_key = config.deepseek_api_key
        self.model = config.deepseek_model
        self.base_url = config.deepseek_base_url

    async def stream_chat(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat responses using direct API.

        Args:
            message: User's message
            history: Previous conversation history

        Yields:
            Response text chunks
        """
        if not self.api_key:
            yield "⚠️ AI service not configured. Please set DEEPSEEK_API_KEY in your .env file."
            return

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
                            except Exception:
                                continue

        except httpx.HTTPStatusError as e:
            logger.error("ai_service_http_error", status_code=e.response.status_code)
            yield f"⚠️ Error communicating with AI service (Status {e.response.status_code})"
        except Exception as e:
            logger.error("ai_service_error", error=str(e))
            yield f"⚠️ Unexpected error: {str(e)}"
