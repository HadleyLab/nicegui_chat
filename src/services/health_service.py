"""Health check service for monitoring application and external service status.

This module provides comprehensive health monitoring for the MammoChat application,
checking the status of core services, external API connectivity, and system health.
"""

import urllib.request
from typing import Dict, Tuple
from dataclasses import dataclass

from config import config
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService


@dataclass
class HealthCheck:
    """Represents the health status of a service component."""
    status: str  # "healthy" or "unhealthy"
    message: str


@dataclass
class HealthStatus:
    """Overall health status with individual service checks."""
    status: str  # "healthy" or "unhealthy"
    checks: Dict[str, HealthCheck]


class HealthService:
    """Service for performing comprehensive health checks."""

    def __init__(
        self,
        auth_service: AuthService,
        memory_service: MemoryService,
        chat_service: ChatService
    ):
        """Initialize the health service with required service dependencies.

        Args:
            auth_service: Authentication service instance
            memory_service: Memory service instance
            chat_service: Chat service instance
        """
        self.auth_service = auth_service
        self.memory_service = memory_service
        self.chat_service = chat_service

    async def check_application_health(self) -> HealthCheck:
        """Check if core application services are properly initialized.

        Returns:
            HealthCheck with application service status
        """
        try:
            if self.auth_service and self.memory_service and self.chat_service:
                return HealthCheck(
                    status="healthy",
                    message="Application started successfully"
                )
            else:
                return HealthCheck(
                    status="unhealthy",
                    message="Services not properly initialized"
                )
        except Exception as e:
            return HealthCheck(
                status="unhealthy",
                message=f"Application check failed: {str(e)}"
            )

    def check_deepseek_health(self) -> HealthCheck:
        """Check DeepSeek API connectivity and availability.

        Returns:
            HealthCheck with DeepSeek API status
        """
        try:
            if not config.deepseek_api_key:
                return HealthCheck(
                    status="unhealthy",
                    message="DeepSeek API key not configured"
                )

            # Simple connectivity test using HEAD request
            request = urllib.request.Request(
                f"{config.deepseek_base_url}/v1/models",
                headers={"Authorization": f"Bearer {config.deepseek_api_key}"},
                method="HEAD"
            )

            response = urllib.request.urlopen(request, timeout=10.0)

            if response.status == 200:
                return HealthCheck(
                    status="healthy",
                    message="DeepSeek API is accessible"
                )
            else:
                return HealthCheck(
                    status="unhealthy",
                    message=f"DeepSeek API returned status {response.status}"
                )
        except Exception as e:
            return HealthCheck(
                status="unhealthy",
                message=f"DeepSeek connectivity test failed: {str(e)}"
            )

    async def check_heysol_health(self) -> HealthCheck:
        """Check HeySol memory service availability.

        Returns:
            HealthCheck with HeySol memory service status
        """
        try:
            if not config.heysol_api_key:
                return HealthCheck(
                    status="unhealthy",
                    message="HeySol API key not configured"
                )

            # Test connectivity by calling list_spaces method
            await self.memory_service.list_spaces()
            return HealthCheck(
                status="healthy",
                message="HeySol memory service is accessible"
            )
        except Exception as e:
            return HealthCheck(
                status="unhealthy",
                message=f"HeySol memory service check failed: {str(e)}"
            )

    async def perform_health_check(self) -> Tuple[HealthStatus, int]:
        """Perform comprehensive health check of all services.

        Returns:
            Tuple of (HealthStatus, HTTP status code)
            - 200 if all services are healthy
            - 503 if any service is unhealthy
        """
        # Perform all health checks
        application_check = await self.check_application_health()
        deepseek_check = self.check_deepseek_health()
        heysol_check = await self.check_heysol_health()

        # Combine all checks
        checks = {
            "application": application_check,
            "deepseek": deepseek_check,
            "heysol": heysol_check
        }

        # Determine overall health status
        overall_healthy = all(check.status == "healthy" for check in checks.values())

        health_status = HealthStatus(
            status="healthy" if overall_healthy else "unhealthy",
            checks=checks
        )

        # Return appropriate HTTP status code
        http_status = 200 if overall_healthy else 503

        return health_status, http_status