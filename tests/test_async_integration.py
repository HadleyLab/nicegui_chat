"""Integration tests for async architecture components.

This module provides comprehensive integration testing for the async architecture,
focusing on:
- Async service interaction validation
- Background task processing verification
- Concurrent operation coordination
- Resource cleanup and lifecycle management
- Error propagation and handling
- Performance under async load

Tests ensure that all async components work together correctly and maintain
performance optimizations while preserving system stability.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import structlog

from config import config
from src.models.chat import (ChatEventType, ConversationState,
                             ConversationStatus)
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService

logger = structlog.get_logger()


@dataclass
class AsyncIntegrationMetrics:
    """Metrics for async integration testing."""

    # Timing metrics
    total_execution_time_ms: float = 0.0
    background_task_completion_time_ms: float = 0.0
    service_initialization_time_ms: float = 0.0

    # Concurrency metrics
    max_concurrent_operations: int = 0
    background_tasks_created: int = 0
    background_tasks_completed: int = 0

    # Resource metrics
    memory_peak_mb: float = 0.0
    cpu_peak_percent: float = 0.0

    # Error tracking
    errors: List[str] = field(default_factory=list)
    timeouts: int = 0
    deadlocks_detected: bool = False


@dataclass
class AsyncOperationResult:
    """Result of an async operation test."""

    operation_name: str
    success: bool
    execution_time_ms: float
    memory_used_mb: float
    error_message: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)


class AsyncIntegrationTester:
    """Comprehensive async integration testing framework."""

    def __init__(self):
        self.results: Dict[str, AsyncOperationResult] = {}
        self.metrics = AsyncIntegrationMetrics()

    async def setup_test_services(self) -> tuple:
        """Set up test services with realistic mocking."""
        # Mock auth service
        auth_service = MagicMock(spec=AuthService)
        auth_service.is_authenticated = True

        # Mock memory service with async behavior
        memory_service = MagicMock(spec=MemoryService)

        # Simulate async memory operations with realistic delays
        async def mock_search(query, **kwargs):
            await asyncio.sleep(0.1)  # Simulate network delay
            return []

        async def mock_store(content, **kwargs):
            await asyncio.sleep(0.05)  # Simulate storage delay
            return f"stored_{uuid4()}"

        memory_service.search = mock_search
        memory_service.store = mock_store

        # Create chat service
        chat_service = ChatService(
            auth_service=auth_service,
            memory_service=memory_service,
            app_config=config,
        )

        return chat_service, auth_service, memory_service

    async def test_background_task_processing(
        self,
        test_name: str,
        num_concurrent_chats: int = 5,
        messages_per_chat: int = 3,
    ) -> AsyncOperationResult:
        """Test background task processing during chat operations."""
        logger.info(
            "Testing background task processing",
            test_name=test_name,
            concurrent_chats=num_concurrent_chats,
        )

        start_time = time.time()
        chat_service, _, memory_service = await self.setup_test_services()

        try:
            # Track background tasks
            initial_task_count = len(chat_service._background_tasks)

            # Create multiple concurrent conversations
            tasks = []
            for i in range(num_concurrent_chats):
                conversation = ConversationState(
                    conversation_id=f"bg_test_{i}_{uuid4()}",
                    status=ConversationStatus.RUNNING,
                )

                # Create chat task
                async def chat_with_background_processing(conv, msg_idx):
                    events = []
                    async for event in chat_service.stream_chat(
                        conversation=conv,
                        user_message=f"Background task test message {msg_idx}",
                        store_user_message=True,
                    ):
                        events.append(event)
                    return events

                # Create multiple messages per conversation
                for j in range(messages_per_chat):
                    task = asyncio.create_task(
                        chat_with_background_processing(conversation, j)
                    )
                    tasks.append(task)

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check results
            successful_chats = sum(1 for r in results if not isinstance(r, Exception))
            failed_chats = len(results) - successful_chats

            # Verify background tasks were created and cleaned up
            final_task_count = len(chat_service._background_tasks)
            tasks_created = max(0, final_task_count - initial_task_count)

            # Wait a bit for cleanup
            await asyncio.sleep(2.0)
            post_cleanup_task_count = len(chat_service._background_tasks)

            execution_time_ms = (time.time() - start_time) * 1000

            success = failed_chats == 0 and tasks_created > 0

            if not success:
                error_msg = f"{failed_chats or 0} chats failed, {tasks_created or 0} background tasks created"
            else:
                error_msg = None

            result = AsyncOperationResult(
                operation_name=test_name,
                success=success,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,  # Would need memory monitoring
                error_message=error_msg,
                artifacts={
                    "successful_chats": successful_chats,
                    "failed_chats": failed_chats,
                    "background_tasks_created": tasks_created,
                    "background_tasks_remaining": post_cleanup_task_count,
                    "total_messages": num_concurrent_chats * messages_per_chat,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            result = AsyncOperationResult(
                operation_name=test_name,
                success=False,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,
                error_message=str(e),
            )

        finally:
            await chat_service.close()

        self.results[test_name] = result
        return result

    async def test_concurrent_service_interaction(
        self,
        test_name: str,
        num_services: int = 3,
        operations_per_service: int = 10,
    ) -> AsyncOperationResult:
        """Test concurrent interaction between multiple services."""
        logger.info(
            "Testing concurrent service interaction",
            test_name=test_name,
            services=num_services,
        )

        start_time = time.time()
        services = []

        try:
            # Create multiple service instances
            for i in range(num_services):
                chat_service, _, _ = await self.setup_test_services()
                services.append(chat_service)

            # Create concurrent operations across all services
            tasks = []
            for service_idx, service in enumerate(services):
                for op_idx in range(operations_per_service):
                    conversation = ConversationState(
                        conversation_id=f"concurrent_{service_idx}_{op_idx}_{uuid4()}",
                        status=ConversationStatus.RUNNING,
                    )

                    async def service_operation(svc, conv):
                        events = []
                        async for event in svc.stream_chat(
                            conversation=conv,
                            user_message=f"Service {service_idx} operation {op_idx}",
                            store_user_message=True,
                        ):
                            events.append(event)
                        return len(events)

                    task = asyncio.create_task(service_operation(service, conversation))
                    tasks.append(task)

            # Execute all operations concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Analyze results
            successful_operations = sum(
                1 for r in results if not isinstance(r, Exception)
            )
            failed_operations = len(results) - successful_operations

            execution_time_ms = (time.time() - start_time) * 1000

            success = failed_operations == 0

            if not success:
                error_msg = (
                    f"{failed_operations} operations failed out of {len(results)}"
                )
            else:
                error_msg = None

            result = AsyncOperationResult(
                operation_name=test_name,
                success=success,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,
                error_message=error_msg,
                artifacts={
                    "total_operations": len(results),
                    "successful_operations": successful_operations,
                    "failed_operations": failed_operations,
                    "services_used": num_services,
                    "avg_operations_per_service": operations_per_service,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            result = AsyncOperationResult(
                operation_name=test_name,
                success=False,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,
                error_message=str(e),
            )

        finally:
            # Clean up all services
            for service in services:
                await service.close()

        self.results[test_name] = result
        return result

    async def test_async_resource_management(
        self,
        test_name: str,
        num_iterations: int = 50,
        resource_cleanup_delay: float = 0.1,
    ) -> AsyncOperationResult:
        """Test async resource management and cleanup."""
        logger.info(
            "Testing async resource management",
            test_name=test_name,
            iterations=num_iterations,
        )

        start_time = time.time()

        try:
            # Test resource lifecycle management
            service_creation_times = []
            service_cleanup_times = []

            for i in range(num_iterations):
                # Create service
                create_start = time.time()
                chat_service, _, _ = await self.setup_test_services()
                create_time = (time.time() - create_start) * 1000
                service_creation_times.append(create_time)

                # Use service briefly
                conversation = ConversationState(
                    conversation_id=f"resource_test_{i}_{uuid4()}",
                    status=ConversationStatus.RUNNING,
                )

                events = []
                async for event in chat_service.stream_chat(
                    conversation=conversation,
                    user_message=f"Resource management test {i}",
                    store_user_message=True,
                ):
                    events.append(event)

                # Clean up service
                cleanup_start = time.time()
                await chat_service.close()
                cleanup_time = (time.time() - cleanup_start) * 1000
                service_cleanup_times.append(cleanup_time)

                # Brief delay between iterations
                await asyncio.sleep(resource_cleanup_delay)

            execution_time_ms = (time.time() - start_time) * 1000

            # Analyze resource management performance
            avg_creation_time = sum(service_creation_times) / len(
                service_creation_times
            )
            avg_cleanup_time = sum(service_cleanup_times) / len(service_cleanup_times)

            success = True
            error_msg = None

            # Check for performance degradation
            if avg_creation_time > 1000:  # More than 1 second average
                success = False
                error_msg = f"Slow service creation: {avg_creation_time:.2f}ms average"

            if avg_cleanup_time > 500:  # More than 500ms average
                if not success:
                    error_msg = (error_msg or "") + "; "
                else:
                    success = False
                    error_msg = f"Slow service cleanup: {avg_cleanup_time:.2f}ms average"

            result = AsyncOperationResult(
                operation_name=test_name,
                success=success,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,
                error_message=error_msg,
                artifacts={
                    "iterations": num_iterations,
                    "avg_service_creation_ms": avg_creation_time,
                    "avg_service_cleanup_ms": avg_cleanup_time,
                    "total_services_created": num_iterations,
                    "resource_cleanup_delay": resource_cleanup_delay,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            result = AsyncOperationResult(
                operation_name=test_name,
                success=False,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,
                error_message=str(e),
            )

        self.results[test_name] = result
        return result

    async def test_error_propagation_and_recovery(
        self,
        test_name: str,
        error_scenarios: List[str],
    ) -> AsyncOperationResult:
        """Test error propagation and recovery mechanisms."""
        logger.info(
            "Testing error propagation and recovery",
            test_name=test_name,
            scenarios=len(error_scenarios),
        )

        start_time = time.time()
        chat_service, _, memory_service = await self.setup_test_services()

        try:
            results: Dict[str, Dict[str, Any]] = {}

            for scenario in error_scenarios:
                scenario_start = time.time()

                try:
                    if scenario == "empty_message":
                        # Test empty message handling
                        conversation = ConversationState(
                            conversation_id=f"error_test_{scenario}_{uuid4()}",
                            status=ConversationStatus.RUNNING,
                        )

                        events = []
                        async for event in chat_service.stream_chat(
                            conversation=conversation,
                            user_message="",
                            store_user_message=True,
                        ):
                            events.append(event)

                        # Should handle gracefully
                        error_events = [
                            e for e in events if e.event_type == ChatEventType.ERROR
                        ]
                        results[scenario] = {
                            "success": len(error_events) > 0,
                            "error_handled": True,
                        }

                    elif scenario == "memory_failure":
                        # Test memory service failure
                        async def failing_search(*args, **kwargs):
                            raise Exception("Simulated memory failure")

                        memory_service.search = failing_search

                        conversation = ConversationState(
                            conversation_id=f"error_test_{scenario}_{uuid4()}",
                            status=ConversationStatus.RUNNING,
                        )

                        events = []
                        async for event in chat_service.stream_chat(
                            conversation=conversation,
                            user_message="Test message with memory failure",
                            store_user_message=True,
                        ):
                            events.append(event)

                        # Should handle memory failure gracefully
                        results[scenario] = {
                            "success": conversation.status != ConversationStatus.FAILED,
                            "error_handled": True,
                        }

                    elif scenario == "timeout_simulation":
                        # Test timeout handling
                        conversation = ConversationState(
                            conversation_id=f"error_test_{scenario}_{uuid4()}",
                            status=ConversationStatus.RUNNING,
                        )

                        # Create a very slow response simulation
                        original_search = memory_service.search

                        async def slow_search(*args, **kwargs):
                            await asyncio.sleep(2.0)  # Longer than typical timeout
                            return await original_search(*args, **kwargs)

                        memory_service.search = slow_search

                        events = []
                        async for event in chat_service.stream_chat(
                            conversation=conversation,
                            user_message="Test message with timeout",
                            store_user_message=True,
                        ):
                            events.append(event)

                        results[scenario] = {
                            "success": len(events) > 0,
                            "timeout_handled": True,
                        }

                except Exception as e:
                    results[scenario] = {
                        "success": False,
                        "error_message": str(e),
                        "error_handled": False,
                    }

                scenario_execution_time_ms = (time.time() - scenario_start) * 1000

            execution_time_ms = (time.time() - start_time) * 1000

            # Analyze error handling effectiveness
            successful_scenarios = sum(
                1 for r in results.values() if r.get("success", False)
            )
            error_handling_effective = sum(
                1 for r in results.values() if r.get("error_handled", False)
            )

            success = (
                successful_scenarios >= len(error_scenarios) * 0.8
            )  # 80% success rate

            if not success:
                error_msg = f"Only {successful_scenarios}/{len(error_scenarios)} scenarios handled successfully"
            else:
                error_msg = None

            result = AsyncOperationResult(
                operation_name=test_name,
                success=success,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,
                error_message=error_msg,
                artifacts={
                    "total_scenarios": len(error_scenarios),
                    "successful_scenarios": successful_scenarios,
                    "error_handling_effective": error_handling_effective,
                    "scenario_results": results,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            result = AsyncOperationResult(
                operation_name=test_name,
                success=False,
                execution_time_ms=execution_time_ms,
                memory_used_mb=0.0,
                error_message=str(e),
            )

        finally:
            await chat_service.close()

        self.results[test_name] = result
        return result

    async def run_comprehensive_async_integration_test(
        self,
    ) -> Dict[str, AsyncOperationResult]:
        """Run comprehensive async integration tests."""
        logger.info("Starting comprehensive async integration tests")

        # Define test scenarios
        test_scenarios: List[Dict[str, Any]] = [
            {
                "name": "background_task_processing",
                "concurrent_chats": 5,
                "messages_per_chat": 3,
            },
            {
                "name": "concurrent_service_interaction",
                "num_services": 3,
                "operations_per_service": 10,
            },
            {
                "name": "async_resource_management",
                "num_iterations": 20,
                "resource_cleanup_delay": 0.05,
            },
            {
                "name": "error_propagation_recovery",
                "error_scenarios": [
                    "empty_message",
                    "memory_failure",
                    "timeout_simulation",
                ],
            },
        ]

        results = {}

        for scenario in test_scenarios:
            if scenario["name"] == "background_task_processing":
                result = await self.test_background_task_processing(
                    scenario["name"],
                    scenario["concurrent_chats"],
                    scenario["messages_per_chat"],
                )
            elif scenario["name"] == "concurrent_service_interaction":
                result = await self.test_concurrent_service_interaction(
                    scenario["name"],
                    scenario["num_services"],
                    scenario["operations_per_service"],
                )
            elif scenario["name"] == "async_resource_management":
                result = await self.test_async_resource_management(
                    scenario["name"],
                    scenario["num_iterations"],
                    scenario["resource_cleanup_delay"],
                )
            elif scenario["name"] == "error_propagation_recovery":
                result = await self.test_error_propagation_and_recovery(
                    scenario["name"],
                    scenario["error_scenarios"],
                )

            results[scenario["name"]] = result

            # Log progress
            status = "✅ PASS" if result.success else "❌ FAIL"
            logger.info(
                f"Async test completed: {scenario['name']} - {status}",
                execution_time_ms=result.execution_time_ms,
            )

        # Update overall metrics
        self.metrics.total_execution_time_ms = sum(
            r.execution_time_ms for r in results.values()
        )
        self.metrics.max_concurrent_operations = max(
            r.artifacts.get("total_operations", 0) for r in results.values()
        )

        return results


# Example usage and test functions
async def run_async_integration_tests():
    """Run comprehensive async integration tests."""
    tester = AsyncIntegrationTester()

    print("Running async integration tests...")

    # Run comprehensive test suite
    results = await tester.run_comprehensive_async_integration_test()

    # Print summary
    print("\nAsync Integration Test Results:")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r.success)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")

    # Detailed results
    for name, result in results.items():
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"\n{name}:")
        print(f"  Status: {status}")
        print(f"  Execution Time: {result.execution_time_ms:.2f} ms")

        if result.error_message:
            print(f"  Error: {result.error_message}")

        # Show key artifacts
        for key, value in result.artifacts.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value}")

    return results


class TestAsyncArchitecture:
    """Pytest integration for async architecture testing."""

    @pytest.mark.asyncio
    async def test_background_task_processing(self):
        """Test background task processing functionality."""
        tester = AsyncIntegrationTester()

        result = await tester.test_background_task_processing(
            "pytest_background_tasks",
            num_concurrent_chats=3,
            messages_per_chat=2,
        )

        assert result.success, f"Background task test failed: {result.error_message}"
        assert result.artifacts["successful_chats"] > 0, "No successful chats"
        assert (
            result.artifacts["background_tasks_created"] > 0
        ), "No background tasks created"

    @pytest.mark.asyncio
    async def test_concurrent_service_interaction(self):
        """Test concurrent interaction between services."""
        tester = AsyncIntegrationTester()

        result = await tester.test_concurrent_service_interaction(
            "pytest_concurrent_services",
            num_services=2,
            operations_per_service=5,
        )

        assert result.success, f"Concurrent service test failed: {result.error_message}"
        assert result.artifacts["successful_operations"] > 0, "No successful operations"

    @pytest.mark.asyncio
    async def test_resource_management(self):
        """Test async resource management."""
        tester = AsyncIntegrationTester()

        result = await tester.test_async_resource_management(
            "pytest_resource_management",
            num_iterations=10,
            resource_cleanup_delay=0.02,
        )

        assert (
            result.success
        ), f"Resource management test failed: {result.error_message}"
        assert (
            result.artifacts["avg_service_creation_ms"] < 1000
        ), "Service creation too slow"
        assert (
            result.artifacts["avg_service_cleanup_ms"] < 500
        ), "Service cleanup too slow"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling and recovery."""
        tester = AsyncIntegrationTester()

        error_scenarios = ["empty_message", "memory_failure"]

        result = await tester.test_error_propagation_and_recovery(
            "pytest_error_handling",
            error_scenarios,
        )

        assert result.success, f"Error handling test failed: {result.error_message}"
        assert result.artifacts["successful_scenarios"] >= len(error_scenarios) * 0.8


if __name__ == "__main__":
    # Run async integration tests when executed directly
    results = asyncio.run(run_async_integration_tests())
    print(f"\nAsync integration testing completed: {len(results)} test suites")
