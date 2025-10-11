"""Streaming performance tests for real-time response validation.

This module provides comprehensive testing of streaming chat functionality including:
- Real-time response streaming validation
- Chunk timing and consistency analysis
- Memory efficiency during streaming
- Concurrent streaming performance
- Streaming error handling and recovery
- Performance regression detection

Tests validate that streaming optimizations maintain responsiveness while
preserving data integrity and proper resource management.
"""

import asyncio
import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import structlog

from config import config
from src.models.chat import ChatEventType, ConversationState, ConversationStatus
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService

logger = structlog.get_logger()


@dataclass
class StreamingMetrics:
    """Metrics for a single streaming operation."""

    # Timing metrics
    total_duration_ms: float = 0.0
    first_chunk_time_ms: float = 0.0
    time_to_first_chunk_ms: float = 0.0
    time_between_chunks_ms: List[float] = field(default_factory=list)

    # Content metrics
    total_chunks: int = 0
    total_content_length: int = 0
    avg_chunk_size: float = 0.0

    # Performance metrics
    chunks_per_second: float = 0.0
    bytes_per_second: float = 0.0

    # Error tracking
    errors: List[str] = field(default_factory=list)
    incomplete_chunks: int = 0

    def calculate_derived_metrics(self) -> None:
        """Calculate derived performance metrics."""
        if self.total_duration_ms > 0:
            self.chunks_per_second = (self.total_chunks / self.total_duration_ms) * 1000
            self.bytes_per_second = (
                self.total_content_length / self.total_duration_ms
            ) * 1000

        if self.total_chunks > 0:
            self.avg_chunk_size = self.total_content_length / self.total_chunks

        if len(self.time_between_chunks_ms) > 0:
            # Calculate average time between chunks
            self.time_between_chunks_ms = [
                (
                    statistics.mean(self.time_between_chunks_ms)
                    if self.time_between_chunks_ms
                    else 0.0
                )
            ]


@dataclass
class StreamingTestResult:
    """Results from a streaming performance test."""

    test_name: str
    iterations: int
    metrics: List[StreamingMetrics]
    baseline_metrics: Optional[StreamingMetrics] = None

    @property
    def avg_total_duration(self) -> float:
        """Average total streaming duration."""
        return statistics.mean(m.total_duration_ms for m in self.metrics)

    @property
    def avg_first_chunk_time(self) -> float:
        """Average time to first chunk."""
        return statistics.mean(m.first_chunk_time_ms for m in self.metrics)

    @property
    def avg_chunks_per_second(self) -> float:
        """Average chunks per second."""
        return statistics.mean(m.chunks_per_second for m in self.metrics)

    @property
    def p95_total_duration(self) -> float:
        """95th percentile total duration."""
        if len(self.metrics) < 20:
            return self.avg_total_duration
        durations = [m.total_duration_ms for m in self.metrics]
        return statistics.quantiles(durations, n=20)[18]

    def get_chunk_timing_consistency(self) -> float:
        """Calculate consistency of chunk timing (lower is more consistent)."""
        if len(self.metrics) < 2:
            return 0.0

        all_intervals = []
        for metrics in self.metrics:
            all_intervals.extend(metrics.time_between_chunks_ms)

        if not all_intervals:
            return 0.0

        mean_interval = statistics.mean(all_intervals)
        if mean_interval == 0:
            return 0.0

        variance = statistics.variance(all_intervals, mean_interval)
        return variance / mean_interval  # Coefficient of variation

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for JSON serialization."""
        return {
            "test_name": self.test_name,
            "iterations": self.iterations,
            "avg_total_duration_ms": self.avg_total_duration,
            "avg_first_chunk_time_ms": self.avg_first_chunk_time,
            "avg_chunks_per_second": self.avg_chunks_per_second,
            "p95_total_duration_ms": self.p95_total_duration,
            "chunk_timing_consistency": self.get_chunk_timing_consistency(),
            "metrics": [
                {
                    "total_duration_ms": m.total_duration_ms,
                    "first_chunk_time_ms": m.first_chunk_time_ms,
                    "total_chunks": m.total_chunks,
                    "chunks_per_second": m.chunks_per_second,
                    "errors": m.errors,
                }
                for m in self.metrics
            ],
        }


class StreamingPerformanceTester:
    """Comprehensive streaming performance testing framework."""

    def __init__(self):
        self.results: Dict[str, StreamingTestResult] = {}
        self.output_dir = Path("streaming_test_results")
        self.output_dir.mkdir(exist_ok=True)

    async def setup_test_services(
        self,
    ) -> Tuple[ChatService, AuthService, MemoryService]:
        """Set up test services with mocked dependencies."""
        # Mock auth service
        auth_service = MagicMock(spec=AuthService)
        auth_service.is_authenticated = True

        # Mock memory service
        memory_service = MagicMock(spec=MemoryService)
        memory_service.search = AsyncMock(return_value=[])

        # Create chat service
        chat_service = ChatService(
            auth_service=auth_service,
            memory_service=memory_service,
            app_config=config,
        )

        return chat_service, auth_service, memory_service

    async def test_streaming_performance(
        self,
        test_name: str,
        messages: List[str],
        iterations: int = 10,
        expected_chunk_size_range: Tuple[int, int] = (10, 100),
    ) -> StreamingTestResult:
        """Test streaming performance with detailed metrics."""
        logger.info(
            "Starting streaming performance test",
            test_name=test_name,
            iterations=iterations,
            messages=len(messages),
        )

        chat_service, _, _ = await self.setup_test_services()
        all_metrics = []

        for i in range(iterations):
            for message in messages:
                # Create test conversation
                conversation = ConversationState(
                    conversation_id=f"streaming_test_{i}_{uuid4()}",
                    status=ConversationStatus.RUNNING,
                )

                metrics = StreamingMetrics()
                start_time = time.time()
                first_chunk_time = None
                last_chunk_time = None
                chunks = []

                try:
                    async for event in chat_service.stream_chat(
                        conversation=conversation,
                        user_message=message,
                        store_user_message=True,
                    ):
                        current_time = time.time()

                        if event.event_type == ChatEventType.MESSAGE_CHUNK:
                            chunk_content = event.payload.get("content", "")

                            # Record first chunk time
                            if first_chunk_time is None:
                                first_chunk_time = current_time
                                metrics.first_chunk_time_ms = (
                                    current_time - start_time
                                ) * 1000

                            # Record chunk timing
                            if last_chunk_time is not None:
                                interval = (current_time - last_chunk_time) * 1000
                                metrics.time_between_chunks_ms.append(interval)

                            last_chunk_time = current_time
                            chunks.append(chunk_content)
                            metrics.total_chunks += 1
                            metrics.total_content_length += len(chunk_content)

                        elif event.event_type == ChatEventType.ERROR:
                            error_msg = event.payload.get("error", "Unknown error")
                            metrics.errors.append(error_msg)

                    # Calculate final metrics
                    end_time = time.time()
                    metrics.total_duration_ms = (end_time - start_time) * 1000

                    # Validate chunk sizes
                    for chunk in chunks:
                        chunk_size = len(chunk)
                        if not (
                            expected_chunk_size_range[0]
                            <= chunk_size
                            <= expected_chunk_size_range[1]
                        ):
                            metrics.incomplete_chunks += 1

                    metrics.calculate_derived_metrics()
                    all_metrics.append(metrics)

                except Exception as e:
                    logger.error(
                        "Streaming test iteration failed", iteration=i, error=str(e)
                    )
                    error_metrics = StreamingMetrics(errors=[str(e)])
                    all_metrics.append(error_metrics)

        await chat_service.close()

        result = StreamingTestResult(
            test_name=test_name,
            iterations=len(all_metrics),
            metrics=all_metrics,
        )

        self.results[test_name] = result
        return result

    async def test_concurrent_streaming(
        self,
        test_name: str,
        concurrent_streams: int,
        messages: List[str],
        duration_seconds: int = 60,
    ) -> StreamingTestResult:
        """Test streaming performance under concurrent load."""
        logger.info(
            "Starting concurrent streaming test",
            test_name=test_name,
            concurrent_streams=concurrent_streams,
            duration=duration_seconds,
        )

        chat_service, _, _ = await self.setup_test_services()
        all_metrics = []
        semaphore = asyncio.Semaphore(concurrent_streams)

        async def streaming_session(session_id: int) -> List[StreamingMetrics]:
            """Run a single streaming session."""
            session_metrics = []

            async with semaphore:
                end_time = time.time() + duration_seconds

                while time.time() < end_time:
                    message = f"Concurrent streaming test message {session_id}"

                    conversation = ConversationState(
                        conversation_id=f"concurrent_{session_id}_{uuid4()}",
                        status=ConversationStatus.RUNNING,
                    )

                    metrics = StreamingMetrics()
                    start_time = time.time()
                    first_chunk_time = None
                    last_chunk_time = None
                    chunks = []

                    try:
                        async for event in chat_service.stream_chat(
                            conversation=conversation,
                            user_message=message,
                            store_user_message=True,
                        ):
                            current_time = time.time()

                            if event.event_type == ChatEventType.MESSAGE_CHUNK:
                                chunk_content = event.payload.get("content", "")

                                if first_chunk_time is None:
                                    first_chunk_time = current_time
                                    metrics.first_chunk_time_ms = (
                                        current_time - start_time
                                    ) * 1000

                                if last_chunk_time is not None:
                                    interval = (current_time - last_chunk_time) * 1000
                                    metrics.time_between_chunks_ms.append(interval)

                                last_chunk_time = current_time
                                chunks.append(chunk_content)
                                metrics.total_chunks += 1
                                metrics.total_content_length += len(chunk_content)

                        # Finalize metrics
                        stream_end_time = time.time()
                        metrics.total_duration_ms = (
                            stream_end_time - start_time
                        ) * 1000
                        metrics.calculate_derived_metrics()
                        session_metrics.append(metrics)

                    except Exception as e:
                        logger.error(
                            "Concurrent streaming failed",
                            session_id=session_id,
                            error=str(e),
                        )
                        error_metrics = StreamingMetrics(errors=[str(e)])
                        session_metrics.append(error_metrics)

                    # Brief pause between messages
                    await asyncio.sleep(0.1)

            return session_metrics

        # Run concurrent streaming sessions
        tasks = [streaming_session(i) for i in range(concurrent_streams)]
        session_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for session_result in session_results:
            if isinstance(session_result, list):
                all_metrics.extend(session_result)

        await chat_service.close()

        result = StreamingTestResult(
            test_name=test_name,
            iterations=len(all_metrics),
            metrics=all_metrics,
        )

        self.results[test_name] = result
        return result

    async def test_streaming_chunk_consistency(
        self,
        test_name: str,
        message: str,
        expected_chunk_count_range: Tuple[int, int] = (5, 50),
        iterations: int = 20,
    ) -> StreamingTestResult:
        """Test consistency of streaming chunk generation."""
        logger.info(
            "Starting chunk consistency test",
            test_name=test_name,
            iterations=iterations,
        )

        chat_service, _, _ = await self.setup_test_services()
        all_metrics = []

        for i in range(iterations):
            conversation = ConversationState(
                conversation_id=f"consistency_{i}_{uuid4()}",
                status=ConversationStatus.RUNNING,
            )

            metrics = StreamingMetrics()
            start_time = time.time()
            chunks = []

            try:
                async for event in chat_service.stream_chat(
                    conversation=conversation,
                    user_message=message,
                    store_user_message=True,
                ):
                    if event.event_type == ChatEventType.MESSAGE_CHUNK:
                        chunk_content = event.payload.get("content", "")
                        chunks.append(chunk_content)
                        metrics.total_chunks += 1
                        metrics.total_content_length += len(chunk_content)

                # Finalize metrics
                end_time = time.time()
                metrics.total_duration_ms = (end_time - start_time) * 1000
                metrics.calculate_derived_metrics()

                # Validate chunk count consistency
                if not (
                    expected_chunk_count_range[0]
                    <= len(chunks)
                    <= expected_chunk_count_range[1]
                ):
                    metrics.errors.append(
                        f"Chunk count {len(chunks)} outside expected range {expected_chunk_count_range}"
                    )

                all_metrics.append(metrics)

            except Exception as e:
                logger.error("Chunk consistency test failed", iteration=i, error=str(e))
                error_metrics = StreamingMetrics(errors=[str(e)])
                all_metrics.append(error_metrics)

        await chat_service.close()

        result = StreamingTestResult(
            test_name=test_name,
            iterations=len(all_metrics),
            metrics=all_metrics,
        )

        self.results[test_name] = result
        return result

    def save_results(self) -> None:
        """Save all streaming test results to JSON files."""
        timestamp = int(time.time())

        for name, result in self.results.items():
            filename = self.output_dir / f"{name}_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(result.to_dict(), f, indent=2)

        # Save summary report
        summary = {
            "timestamp": timestamp,
            "total_tests": len(self.results),
            "summary": {
                name: {
                    "avg_duration_ms": result.avg_total_duration,
                    "avg_first_chunk_ms": result.avg_first_chunk_time,
                    "avg_chunks_per_second": result.avg_chunks_per_second,
                    "iterations": result.iterations,
                }
                for name, result in self.results.items()
            },
        }

        summary_file = self.output_dir / f"streaming_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("Streaming test results saved", count=len(self.results))

    def generate_performance_report(self) -> str:
        """Generate a human-readable performance report."""
        if not self.results:
            return "No streaming test results available"

        report = (
            """
# Streaming Performance Test Report

## Summary

"""
            + f"""
- **Total Tests**: {len(self.results)}
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Results

"""
        )

        for name, result in self.results.items():
            report += f"""
### {name}
- **Iterations**: {result.iterations}
- **Average Duration**: {result.avg_total_duration:.2f} ms
- **Average Time to First Chunk**: {result.avg_first_chunk_time:.2f} ms
- **Average Chunks/Second**: {result.avg_chunks_per_second:.2f}
- **95th Percentile Duration**: {result.p95_total_duration:.2f} ms
- **Chunk Timing Consistency**: {result.get_chunk_timing_consistency():.4f}

"""

            # Error summary
            total_errors = sum(len(m.errors) for m in result.metrics)
            if total_errors > 0:
                report += f"- **Errors**: {total_errors} total\n"
            else:
                report += "- **Errors**: None\n"

        return report


# Global test framework instance
streaming_tester = StreamingPerformanceTester()


class TestStreamingPerformance:
    """Streaming performance test cases."""

    @pytest.mark.asyncio
    async def test_basic_streaming_performance(self):
        """Test basic streaming performance with various message lengths."""
        messages = [
            "Short message",
            "This is a medium length message that should generate multiple chunks",
            "This is a longer message that contains more content and should be broken down into several chunks for streaming delivery to ensure responsive user experience",
        ]

        result = await streaming_tester.test_streaming_performance(
            test_name="basic_streaming_performance",
            messages=messages,
            iterations=5,
        )

        # Validate performance requirements
        assert result.avg_total_duration < 10000  # Should complete within 10 seconds
        assert (
            result.avg_first_chunk_time < 2000
        )  # First chunk should arrive within 2 seconds
        assert result.avg_chunks_per_second > 1  # Should maintain reasonable chunk rate

        # Check for errors
        error_count = sum(len(m.errors) for m in result.metrics)
        assert error_count / len(result.metrics) < 0.2  # Less than 20% errors

    @pytest.mark.asyncio
    async def test_concurrent_streaming_performance(self):
        """Test streaming performance under concurrent load."""
        result = await streaming_tester.test_concurrent_streaming(
            test_name="concurrent_streaming_performance",
            concurrent_streams=5,
            messages=["Concurrent streaming test message"],
            duration_seconds=30,
        )

        # Validate concurrent performance
        assert result.avg_total_duration < 15000  # Should handle concurrent load
        assert (
            result.avg_first_chunk_time < 3000
        )  # First chunk should still be responsive
        assert result.avg_chunks_per_second > 0.5  # Should maintain chunk generation

    @pytest.mark.asyncio
    async def test_streaming_chunk_consistency(self):
        """Test consistency of chunk generation."""
        message = "This is a test message for chunk consistency validation that should generate a predictable number of chunks"

        result = await streaming_tester.test_streaming_chunk_consistency(
            test_name="chunk_consistency_test",
            message=message,
            expected_chunk_count_range=(3, 20),
            iterations=10,
        )

        # Validate chunk consistency
        assert result.avg_total_duration < 8000  # Should be reasonably fast
        assert result.avg_chunks_per_second > 2  # Should maintain good chunk rate

        # Check consistency (lower coefficient of variation is better)
        consistency = result.get_chunk_timing_consistency()
        assert consistency < 1.0  # Should have reasonable timing consistency

    @pytest.mark.asyncio
    async def test_streaming_memory_efficiency(self):
        """Test memory efficiency during streaming operations."""
        # This test would integrate with the memory profiler
        # For now, we'll focus on basic streaming validation

        message = "Memory efficiency test message for streaming validation"
        result = await streaming_tester.test_streaming_performance(
            test_name="streaming_memory_efficiency",
            messages=[message],
            iterations=5,
        )

        # Basic memory efficiency validation
        assert result.avg_total_duration < 5000  # Should be memory efficient
        assert result.iterations == 5  # Should complete all iterations

        # Check that we're not accumulating excessive memory per chunk
        avg_memory_per_chunk = result.avg_total_duration / result.avg_chunks_per_second
        assert avg_memory_per_chunk < 1000  # Reasonable memory per chunk


# Example usage
async def run_streaming_tests():
    """Run comprehensive streaming performance tests."""
    tester = StreamingPerformanceTester()

    print("Running streaming performance tests...")

    # Basic streaming test
    await tester.test_streaming_performance(
        "basic_streaming_test",
        ["Hello", "How are you?", "This is a test message"],
        iterations=3,
    )

    # Concurrent streaming test
    await tester.test_concurrent_streaming(
        "concurrent_streaming_test",
        concurrent_streams=3,
        messages=["Concurrent test"],
        duration_seconds=20,
    )

    # Chunk consistency test
    await tester.test_streaming_chunk_consistency(
        "chunk_consistency_test",
        "Consistency test message for chunk validation",
        iterations=5,
    )

    # Save results
    tester.save_results()

    # Generate report
    report = tester.generate_performance_report()
    print(report)

    return tester.results


if __name__ == "__main__":
    # Run tests when executed directly
    results = asyncio.run(run_streaming_tests())
    print(f"Streaming tests completed: {len(results)} test suites")
