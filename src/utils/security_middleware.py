"""Security middleware for production deployment.

This module provides comprehensive security headers and CORS configuration
for the MammoChat application in production environments.
"""

from typing import List
from fastapi import Request


class SecurityMiddleware:
    """Security middleware for adding security headers and CORS configuration."""

    def __init__(self):
        """Initialize security middleware with default configurations."""
        self.allowed_origins = [
            "https://mammochat.com",
            "https://www.mammochat.com",
            "http://localhost:8080",  # Development
            "http://127.0.0.1:8080",  # Development
        ]

    async def add_security_headers(self, request: Request, call_next):
        """Add security headers to HTTP responses.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware function in the chain

        Returns:
            HTTP response with security headers added
        """
        response = await call_next(request)

        # Security headers for production deployment
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' ws://localhost:8080 wss://localhost:8080"
        )

        return response

    async def add_cors_headers(self, request: Request, call_next):
        """Add CORS headers for cross-origin requests.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware function in the chain

        Returns:
            HTTP response with CORS headers added if origin is allowed
        """
        response = await call_next(request)

        # Get the origin from the request
        origin = request.headers.get("origin", "")

        # Only add CORS headers if the origin is in our allowed list
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response

    def get_middleware_functions(self):
        """Get the middleware functions for FastAPI app integration.

        Returns:
            List of middleware functions to be added to the FastAPI app
        """
        return [
            self.add_security_headers,
            self.add_cors_headers
        ]


# Global instance for easy access
security_middleware = SecurityMiddleware()