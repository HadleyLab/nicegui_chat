"""Rate limiting configuration for API endpoints.

This module provides simple in-memory rate limiting functionality to prevent abuse
and ensure fair usage of the MammoChat API endpoints.
"""

import time
from collections import defaultdict
from fastapi import Request


class InMemoryRateLimiter:
    """Simple in-memory rate limiter using basic data structures."""

    def __init__(self):
        """Initialize the rate limiter with default limits."""
        self.requests = defaultdict(list)
        self.global_limits = {"day": 200, "hour": 50}
        self.health_endpoint_limit = {"minute": 10}

    def _cleanup_old_requests(self, client_id: str, window_seconds: int):
        """Remove requests outside the current time window."""
        current_time = time.time()
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < window_seconds
        ]

    def _is_rate_limited(self, client_id: str, limit: int, window_seconds: int) -> bool:
        """Check if client exceeds rate limit for given window."""
        self._cleanup_old_requests(client_id, window_seconds)
        return len(self.requests[client_id]) >= limit

    def check_rate_limit(self, request: Request, limit_type: str = "global") -> tuple[bool, str]:
        """Check if request should be rate limited.

        Args:
            request: The incoming HTTP request
            limit_type: Type of limit to check ("global", "health")

        Returns:
            Tuple of (is_limited, client_id)
        """
        client_id = self._get_client_id(request)

        if limit_type == "health":
            # 10 requests per minute for health endpoint
            if self._is_rate_limited(client_id, self.health_endpoint_limit["minute"], 60):
                return True, client_id
        else:
            # Global limits: 200 per day, 50 per hour
            current_time = time.time()

            # Check daily limit (86400 seconds)
            if self._is_rate_limited(client_id, self.global_limits["day"], 86400):
                return True, client_id

            # Check hourly limit (3600 seconds)
            if self._is_rate_limited(client_id, self.global_limits["hour"], 3600):
                return True, client_id

        # Record this request
        self.requests[client_id].append(time.time())
        return False, client_id

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use X-Forwarded-For header if available, otherwise use direct IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Get direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def get_exception_handler(self):
        """Get the rate limit exceeded exception handler.

        Returns:
            Exception handler function for rate limit exceeded errors
        """
        async def rate_limit_handler(request: Request, exc: Exception):
            return {
                "error": "Rate limit exceeded",
                "detail": "Too many requests"
            }, 429

        return rate_limit_handler


class RateLimitingConfig:
    """Configuration for rate limiting across different endpoints."""

    def __init__(self):
        """Initialize rate limiting configuration with default limits."""
        self.limiter = InMemoryRateLimiter()

    def get_limiter(self):
        """Get the configured rate limiter instance.

        Returns:
            Configured InMemoryRateLimiter instance for use with FastAPI
        """
        return self.limiter

    def get_exception_handler(self):
        """Get the rate limit exceeded exception handler.

        Returns:
            Exception handler function for rate limit exceeded errors
        """
        return self.limiter.get_exception_handler()


# Global instance for easy access
rate_limiting_config = RateLimitingConfig()