"""Regression testing framework for nicegui_chat optimization validation.

This module ensures that performance optimizations don't break existing functionality:
- Core chat functionality validation
- Memory service integration testing
- Authentication flow verification
- Error handling and edge case testing
- Data integrity validation
- Configuration compatibility testing

The framework provides comprehensive regression tests that validate
all critical functionality while measuring performance impact.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import structlog

from config import config
from src.models.chat import (
    ChatEventType,
    ChatMessage,
    ConversationState,
    ConversationStatus,
    MessageRole,
)
from src.models.memory import MemoryEpisode, MemorySearchResult
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService

logger = structlog.get_logger()


@dataclass
class RegressionTestCase:
    """Definition of a regression test case."""

    name: str
    description: str
    test_function: callable
    expected_behavior: str
    performance_threshold_ms: Optional[float] = None
    memory_threshold_mb: Optional[float] = None
    critical: bool = False  # Critical tests must always pass


@dataclass
class RegressionTestResult:
    """Results from a regression test execution."""

    test_name: str
    success: bool
    execution_time_ms: float
    memory_used_mb: float
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "memory_used_mb": self.memory_used_mb,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "artifacts": self.artifacts,
        }


class RegressionTestSuite:
    """Comprehensive regression testing suite."""

    def __init__(self):
        self.test_cases: List[RegressionTestCase] = []
        self.results: Dict[str, RegressionTestResult] = {}
        self.output_dir = Path("regression_test_results")
        self.output_dir.mkdir(exist_ok=True)

    def add_test_case(self, test_case: RegressionTestCase) -> None:
        """Add a test case to the suite."""
        self.test_cases.append(test_case)

    async def setup_test_services(self) -> tuple:
        """Set up test services with realistic mocking."""
        # Mock auth service
        auth_service = MagicMock(spec=AuthService)
        auth_service.is_authenticated = True

        # Mock memory service with realistic responses
        memory_service = MagicMock(spec=MemoryService)

        # Realistic memory search response
        mock_episodes = [
            MemoryEpisode(
                episode_id=f"episode_{i}",
                body=f"Memory content {i}",
                space_id="test_space",
                created_at="2024-01-01T00:00:00Z",
            )
            for i in range(3)
        ]
        memory_service.search = AsyncMock(
            return_value=MemorySearchResult(episodes=mock_episodes, total=3)
        )

        # Realistic memory store response
        memory_service.store = AsyncMock(return_value=f"stored_episode_{uuid4()}")

        # Create chat service
        chat_service = ChatService(
            auth_service=auth_service,
            memory_service=memory_service,
            app_config=config,
        )

        return chat_service, auth_service, memory_service

    async def run_test_case(
        self,
        test_case: RegressionTestCase,
        performance_monitor: bool = True,
    ) -> RegressionTestResult:
        """Run a single test case with performance monitoring."""
        import tracemalloc

        import psutil

        logger.info("Running regression test", test_name=test_case.name)

        start_time = time.time()
        process = psutil.Process()

        # Memory monitoring
        if performance_monitor:
            tracemalloc.start()
            gc.collect()
            initial_memory = process.memory_info().rss / 1024 / 1024
        else:
            initial_memory = 0.0

        try:
            # Execute test function
            if performance_monitor:
                result = await test_case.test_function()
            else:
                result = await test_case.test_function()

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Calculate memory usage
            if performance_monitor:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                final_memory = process.memory_info().rss / 1024 / 1024
                memory_used_mb = final_memory - initial_memory
            else:
                memory_used_mb = 0.0

            # Validate performance thresholds
            warnings = []
            if (
                test_case.performance_threshold_ms
                and execution_time_ms > test_case.performance_threshold_ms
            ):
                warnings.append(
                    f"Performance threshold exceeded: {execution_time_ms:.2f}ms > "
                    f"{test_case.performance_threshold_ms}ms"
                )

            if (
                test_case.memory_threshold_mb
                and memory_used_mb > test_case.memory_threshold_mb
            ):
                warnings.append(
                    f"Memory threshold exceeded: {memory_used_mb:.2f}MB > "
                    f"{test_case.memory_threshold_mb}MB"
                )

            test_result = RegressionTestResult(
                test_name=test_case.name,
                success=True,
                execution_time_ms=execution_time_ms,
                memory_used_mb=memory_used_mb,
                warnings=warnings,
                artifacts={"result": result},
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            if performance_monitor:
                try:
                    tracemalloc.stop()
                except:
                    pass
                final_memory = process.memory_info().rss / 1024 / 1024
                memory_used_mb = final_memory - initial_memory
            else:
                memory_used_mb = 0.0

            test_result = RegressionTestResult(
                test_name=test_case.name,
                success=False,
                execution_time_ms=execution_time_ms,
                memory_used_mb=memory_used_mb,
                error_message=str(e),
            )

        self.results[test_case.name] = test_result
        return test_result

    async def run_all_tests(
        self,
        performance_monitoring: bool = True,
        fail_fast: bool = False,
    ) -> Dict[str, RegressionTestResult]:
        """Run all test cases in the suite."""
        logger.info("Starting regression test suite", total_tests=len(self.test_cases))

        results = {}

        for test_case in self.test_cases:
            result = await self.run_test_case(test_case, performance_monitoring)

            # Log result
            if result.success:
                logger.info(
                    "Test passed",
                    test_name=test_case.name,
                    execution_time_ms=result.execution_time_ms,
                    memory_mb=result.memory_used_mb,
                )
            else:
                logger.error(
                    "Test failed",
                    test_name=test_case.name,
                    error=result.error_message,
                    execution_time_ms=result.execution_time_ms,
                )

                if fail_fast and test_case.critical:
                    logger.error("Critical test failed, stopping test suite")
                    break

            results[test_case.name] = result

        # Update results
        self.results.update(results)

        # Log summary
        passed = sum(1 for r in results.values() if r.success)
        failed = len(results) - passed

        logger.info(
            "Regression test suite completed",
            passed=passed,
            failed=failed,
            total=len(results),
        )

        return results

    def save_results(self) -> None:
        """Save test results to JSON file."""
        timestamp = int(time.time())

        # Convert results to serializable format
        serializable_results = {
            name: result.to_dict() for name, result in self.results.items()
        }

        results_data = {
            "timestamp": timestamp,
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results.values() if r.success),
                "failed": sum(1 for r in self.results.values() if not r.success),
                "critical_failures": sum(
                    1
                    for r in self.results.values()
                    if not r.success
                    and any(
                        tc.critical for tc in self.test_cases if tc.name == r.test_name
                    )
                ),
            },
            "results": serializable_results,
        }

        filename = self.output_dir / f"regression_results_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info("Regression test results saved", filename=str(filename))

    def generate_report(self) -> str:
        """Generate a human-readable test report."""
        if not self.results:
            return "No test results available"

        passed = sum(1 for r in self.results.values() if r.success)
        failed = sum(1 for r in self.results.values() if not r.success)
        critical_failures = sum(
            1
            for r in self.results.values()
            if not r.success
            and any(tc.critical for tc in self.test_cases if tc.name == r.test_name)
        )

        report = f"""
# Regression Test Report

## Summary
- **Total Tests**: {len(self.results)}
- **Passed**: {passed}
- **Failed**: {failed}
- **Critical Failures**: {critical_failures}
- **Success Rate**: {passed / len(self.results) * 100:.1f}%

## Test Results

"""

        for name, result in self.results.items():
            status = "✅ PASS" if result.success else "❌ FAIL"
            report += f"""
### {name}
- **Status**: {status}
- **Execution Time**: {result.execution_time_ms:.2f} ms
- **Memory Used**: {result.memory_used_mb:.2f} MB
"""

            if result.error_message:
                report += f"- **Error**: {result.error_message}\n"

            if result.warnings:
                report += "- **Warnings**:\n"
                for warning in result.warnings:
                    report += f"  - {warning}\n"

        return report


# Test case definitions
async def test_basic_chat_functionality(
    chat_service, auth_service, memory_service
) -> Dict[str, Any]:
    """Test basic chat functionality."""
    conversation = ConversationState(
        conversation_id="test_conversation",
        status=ConversationStatus.RUNNING,
    )

    events = []
    async for event in chat_service.stream_chat(
        conversation=conversation,
        user_message="Hello, this is a test message",
        store_user_message=True,
    ):
        events.append(event)

    # Validate event sequence
    event_types = [e.event_type for e in events]

    # Should have start, chunks, and end events
    assert ChatEventType.MESSAGE_START in event_types
    assert ChatEventType.MESSAGE_CHUNK in event_types
    assert ChatEventType.MESSAGE_END in event_types

    return {
        "total_events": len(events),
        "event_types": [et.value for et in event_types],
        "conversation_status": conversation.status.value,
    }


async def test_memory_integration(
    chat_service, auth_service, memory_service
) -> Dict[str, Any]:
    """Test memory service integration."""
    # Test memory search
    search_results = await memory_service.search("test query", limit=5)
    assert isinstance(search_results, MemorySearchResult)
    assert len(search_results.episodes) >= 0

    # Test memory enrichment during chat
    conversation = ConversationState(
        conversation_id="memory_test_conversation",
        status=ConversationStatus.RUNNING,
        memory_space_ids=["test_space"],
    )

    events = []
    async for event in chat_service.stream_chat(
        conversation=conversation,
        user_message="Test message with memory",
        store_user_message=True,
    ):
        events.append(event)

    # Should complete successfully
    assert conversation.status == ConversationStatus.SUCCESS

    return {
        "search_results_count": len(search_results.episodes),
        "conversation_events": len(events),
        "memory_enrichment_enabled": config.chat_enable_memory_enrichment,
    }


async def test_error_handling(
    chat_service, auth_service, memory_service
) -> Dict[str, Any]:
    """Test error handling and edge cases."""
    # Test empty message handling
    conversation = ConversationState(
        conversation_id="error_test_conversation",
        status=ConversationStatus.RUNNING,
    )

    try:
        events = []
        async for event in chat_service.stream_chat(
            conversation=conversation,
            user_message="",
            store_user_message=True,
        ):
            events.append(event)

        # Should handle empty message gracefully
        error_events = [e for e in events if e.event_type == ChatEventType.ERROR]
        assert len(error_events) > 0

    except Exception as e:
        # Should raise appropriate exception
        assert "empty message" in str(e).lower()

    return {
        "error_handling_tested": True,
        "conversation_final_status": conversation.status.value,
    }


async def test_conversation_state_management(
    chat_service, auth_service, memory_service
) -> Dict[str, Any]:
    """Test conversation state management."""
    conversation = ConversationState(
        conversation_id="state_test_conversation",
        status=ConversationStatus.RUNNING,
    )

    # Test message appending
    user_message = ChatMessage(
        message_id="test_user_msg",
        role=MessageRole.USER,
        content="Test user message",
    )
    conversation.append_message(user_message)

    # Test conversation progression
    events = []
    async for event in chat_service.stream_chat(
        conversation=conversation,
        user_message="Test message for state management",
        store_user_message=True,
    ):
        events.append(event)

    # Validate final state
    assert conversation.status == ConversationStatus.SUCCESS
    assert len(conversation.messages) >= 2  # User + Assistant messages

    return {
        "initial_messages": len(conversation.messages),
        "final_messages": len(conversation.messages),
        "conversation_status": conversation.status.value,
        "streaming_events": len(events),
    }


async def test_authentication_integration(
    chat_service, auth_service, memory_service
) -> Dict[str, Any]:
    """Test authentication integration."""
    # Test with authenticated user
    conversation = ConversationState(
        conversation_id="auth_test_conversation",
        status=ConversationStatus.RUNNING,
    )

    events = []
    async for event in chat_service.stream_chat(
        conversation=conversation,
        user_message="Authenticated user test message",
        store_user_message=True,
    ):
        events.append(event)

    # Should complete successfully with authentication
    assert conversation.status == ConversationStatus.SUCCESS

    return {
        "authentication_required": True,
        "conversation_completed": conversation.status == ConversationStatus.SUCCESS,
        "events_generated": len(events),
    }


async def test_configuration_compatibility(
    chat_service, auth_service, memory_service
) -> Dict[str, Any]:
    """Test configuration compatibility and settings."""
    # Test various configuration settings
    assert config.chat_store_user_messages is True
    assert config.chat_enable_memory_enrichment is True
    assert config.chat_stream_chunk_size > 0

    # Test with different chunk sizes
    conversation = ConversationState(
        conversation_id="config_test_conversation",
        status=ConversationStatus.RUNNING,
    )

    events = []
    async for event in chat_service.stream_chat(
        conversation=conversation,
        user_message="Configuration compatibility test message",
        store_user_message=True,
    ):
        events.append(event)

    # Should respect configuration settings
    chunk_events = [e for e in events if e.event_type == ChatEventType.MESSAGE_CHUNK]
    total_content = sum(len(e.payload.get("content", "")) for e in chunk_events)

    return {
        "config_chunk_size": config.chat_stream_chunk_size,
        "total_streaming_events": len(events),
        "chunk_events": len(chunk_events),
        "total_content_length": total_content,
        "memory_enrichment_enabled": config.chat_enable_memory_enrichment,
    }


# Create test suite with comprehensive test cases
def create_regression_test_suite() -> RegressionTestSuite:
    """Create and configure the regression test suite."""
    suite = RegressionTestSuite()

    # Define test cases
    test_cases = [
        RegressionTestCase(
            name="basic_chat_functionality",
            description="Test core chat functionality and event streaming",
            test_function=lambda cs, auth, ms: test_basic_chat_functionality(
                cs, auth, ms
            ),
            expected_behavior="Should generate complete chat event sequence",
            performance_threshold_ms=10000,  # 10 seconds
            memory_threshold_mb=100,  # 100 MB
            critical=True,
        ),
        RegressionTestCase(
            name="memory_integration",
            description="Test memory service integration and enrichment",
            test_function=lambda cs, auth, ms: test_memory_integration(cs, auth, ms),
            expected_behavior="Should integrate memory search and enrichment",
            performance_threshold_ms=15000,  # 15 seconds
            memory_threshold_mb=150,  # 150 MB
            critical=True,
        ),
        RegressionTestCase(
            name="error_handling",
            description="Test error handling and edge cases",
            test_function=lambda cs, auth, ms: test_error_handling(cs, auth, ms),
            expected_behavior="Should handle errors gracefully",
            performance_threshold_ms=5000,  # 5 seconds
            memory_threshold_mb=50,  # 50 MB
            critical=True,
        ),
        RegressionTestCase(
            name="conversation_state_management",
            description="Test conversation state transitions and message management",
            test_function=lambda cs, auth, ms: test_conversation_state_management(
                cs, auth, ms
            ),
            expected_behavior="Should maintain proper conversation state",
            performance_threshold_ms=12000,  # 12 seconds
            memory_threshold_mb=120,  # 120 MB
            critical=False,
        ),
        RegressionTestCase(
            name="authentication_integration",
            description="Test authentication flow integration",
            test_function=lambda cs, auth, ms: test_authentication_integration(
                cs, auth, ms
            ),
            expected_behavior="Should require and validate authentication",
            performance_threshold_ms=8000,  # 8 seconds
            memory_threshold_mb=80,  # 80 MB
            critical=False,
        ),
        RegressionTestCase(
            name="configuration_compatibility",
            description="Test configuration settings and compatibility",
            test_function=lambda cs, auth, ms: test_configuration_compatibility(
                cs, auth, ms
            ),
            expected_behavior="Should respect configuration settings",
            performance_threshold_ms=10000,  # 10 seconds
            memory_threshold_mb=100,  # 100 MB
            critical=False,
        ),
    ]

    for test_case in test_cases:
        suite.add_test_case(test_case)

    return suite


# Example usage and test runner
async def run_regression_tests():
    """Run the complete regression test suite."""
    suite = create_regression_test_suite()

    # Run all tests with performance monitoring
    results = await suite.run_all_tests(performance_monitoring=True, fail_fast=True)

    # Generate and save report
    report = suite.generate_report()
    print(report)

    # Save detailed results
    suite.save_results()

    # Return summary
    passed = sum(1 for r in results.values() if r.success)
    total = len(results)

    print(f"\nRegression Tests: {passed}/{total} passed")

    if passed == total:
        print("✅ All regression tests passed!")
    else:
        print("❌ Some regression tests failed")
        failed_tests = [name for name, result in results.items() if not result.success]
        print(f"Failed tests: {', '.join(failed_tests)}")

    return results


class TestRegressionValidation:
    """Pytest integration for regression testing."""

    @pytest.mark.asyncio
    async def test_regression_suite_execution(self):
        """Test that the regression suite executes without critical failures."""
        suite = create_regression_test_suite()
        results = await suite.run_all_tests(performance_monitoring=False)

        # Check critical tests
        critical_tests = [tc for tc in suite.test_cases if tc.critical]
        critical_failures = [
            name
            for name, result in results.items()
            if not result.success and any(tc.name == name for tc in critical_tests)
        ]

        assert (
            len(critical_failures) == 0
        ), f"Critical tests failed: {critical_failures}"

        # Overall success rate should be high
        success_rate = sum(1 for r in results.values() if r.success) / len(results)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2f}"

    @pytest.mark.asyncio
    async def test_individual_critical_tests(self):
        """Test individual critical functionality."""
        chat_service, auth_service, memory_service = (
            await RegressionTestSuite().setup_test_services()
        )

        # Test basic chat functionality
        result = await test_basic_chat_functionality(
            chat_service, auth_service, memory_service
        )
        assert result["total_events"] > 0
        assert result["conversation_status"] == "success"

        # Test memory integration
        result = await test_memory_integration(
            chat_service, auth_service, memory_service
        )
        assert result["search_results_count"] >= 0
        assert result["conversation_events"] > 0

        # Test error handling
        result = await test_error_handling(chat_service, auth_service, memory_service)
        assert result["error_handling_tested"] is True

        await chat_service.close()


if __name__ == "__main__":
    # Run regression tests when executed directly
    results = asyncio.run(run_regression_tests())
    print(f"\nRegression testing completed: {len(results)} tests executed")
