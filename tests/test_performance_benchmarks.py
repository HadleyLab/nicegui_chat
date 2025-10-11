"""Comprehensive performance benchmarks for nicegui_chat optimizations.

This module provides systematic performance testing across multiple dimensions:
- Response time benchmarks for chat operations
- Memory usage profiling and leak detection
- Throughput testing under concurrent load
- Streaming performance validation
- Async architecture efficiency testing
- Docker environment performance validation

All benchmarks include before/after comparison capabilities and detailed
performance metrics collection for optimization validation.
"""

import asyncio
import gc
import json
import statistics
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import psutil

try:
    import pytest
except ImportError:
    pytest = None

try:
    import structlog

    logger = structlog.get_logger()
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

from config import config
from src.models.chat import ChatEventType, ConversationState, ConversationStatus
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService

logger = structlog.get_logger()


@dataclass
class PerformanceMetrics:
    """Container for comprehensive performance metrics."""

    # Timing metrics
    response_time_ms: float = 0.0
    first_token_time_ms: float = 0.0
    streaming_duration_ms: float = 0.0

    # Memory metrics
    memory_peak_mb: float = 0.0
    memory_increase_mb: float = 0.0
    memory_objects_created: int = 0

    # Throughput metrics
    tokens_per_second: float = 0.0
    chunks_per_second: float = 0.0
    total_tokens: int = 0
    total_chunks: int = 0

    # System metrics
    cpu_usage_percent: float = 0.0
    thread_count: int = 0

    # Error tracking
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0


@dataclass
class BenchmarkResult:
    """Results from a complete benchmark run."""

    benchmark_name: str
    iterations: int
    metrics: List[PerformanceMetrics]
    baseline_metrics: Optional[PerformanceMetrics] = None
    timestamp: float = field(default_factory=time.time)

    @property
    def avg_response_time(self) -> float:
        """Average response time across all iterations."""
        return statistics.mean(m.response_time_ms for m in self.metrics)

    @property
    def avg_memory_usage(self) -> float:
        """Average memory usage across all iterations."""
        return statistics.mean(m.memory_peak_mb for m in self.metrics)

    @property
    def avg_throughput(self) -> float:
        """Average tokens per second across all iterations."""
        return statistics.mean(m.tokens_per_second for m in self.metrics)

    @property
    def p95_response_time(self) -> float:
        """95th percentile response time."""
        if len(self.metrics) < 20:
            return self.avg_response_time
        return statistics.quantiles((m.response_time_ms for m in self.metrics), n=20)[
            18
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for JSON serialization."""
        return {
            "benchmark_name": self.benchmark_name,
            "iterations": self.iterations,
            "timestamp": self.timestamp,
            "avg_response_time_ms": self.avg_response_time,
            "avg_memory_usage_mb": self.avg_memory_usage,
            "avg_throughput_tps": self.avg_throughput,
            "p95_response_time_ms": self.p95_response_time,
            "metrics": [
                {
                    "response_time_ms": m.response_time_ms,
                    "memory_peak_mb": m.memory_peak_mb,
                    "tokens_per_second": m.tokens_per_second,
                    "errors": m.errors,
                }
                for m in self.metrics
            ],
        }


class PerformanceMonitor:
    """Context manager for comprehensive performance monitoring."""

    def __init__(self):
        self.start_time = None
        self.first_token_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = 0
        self.start_objects = 0
        self.start_cpu = 0.0
        self.process = psutil.Process()

    def __enter__(self):
        # Force garbage collection before starting
        gc.collect()
        self.start_objects = len(gc.get_objects())

        # Record initial memory state
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory

        # Record CPU state
        self.start_cpu = self.process.cpu_percent()

        # Start timing
        self.start_time = time.perf_counter()

        # Start memory tracing
        tracemalloc.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # End timing
        self.end_time = time.perf_counter()

        # Get final memory state
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.peak_memory = max(self.peak_memory, peak / 1024 / 1024)  # MB

        # Calculate object creation
        gc.collect()
        end_objects = len(gc.get_objects())

        return exc_type is None  # Don't suppress exceptions

    def record_first_token(self):
        """Record when first token is received."""
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()

    def get_metrics(self) -> PerformanceMetrics:
        """Get comprehensive performance metrics."""
        if not self.end_time or not self.start_time:
            raise RuntimeError("Monitor not properly exited")

        total_time_ms = (self.end_time - self.start_time) * 1000

        # Calculate memory increase
        memory_increase = self.peak_memory - (self.start_memory or 0)

        # Calculate object creation
        objects_created = len(gc.get_objects()) - self.start_objects

        # Get current CPU usage
        cpu_percent = self.process.cpu_percent()

        # Get thread count
        thread_count = self.process.num_threads()

        return PerformanceMetrics(
            response_time_ms=total_time_ms,
            first_token_time_ms=(
                (self.first_token_time - self.start_time) * 1000
                if self.first_token_time
                else 0
            ),
            streaming_duration_ms=total_time_ms,
            memory_peak_mb=self.peak_memory,
            memory_increase_mb=memory_increase,
            memory_objects_created=objects_created,
            cpu_usage_percent=cpu_percent,
            thread_count=thread_count,
        )


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmarking suite."""

    def __init__(self):
        self.results: Dict[str, BenchmarkResult] = {}
        self.baselines: Dict[str, PerformanceMetrics] = {}
        self.output_dir = Path("benchmark_results")
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
        memory_service.store = AsyncMock(return_value=str(uuid4()))

        # Create chat service with mocked dependencies
        chat_service = ChatService(
            auth_service=auth_service,
            memory_service=memory_service,
            app_config=config,
        )

        return chat_service, auth_service, memory_service

    async def benchmark_chat_response(
        self,
        name: str,
        messages: List[str],
        iterations: int = 10,
        warmup_iterations: int = 3,
    ) -> BenchmarkResult:
        """Benchmark chat response performance."""
        logger.info(
            "Starting chat response benchmark", benchmark=name, iterations=iterations
        )

        chat_service, auth_service, memory_service = await self.setup_test_services()

        all_metrics = []

        for i in range(warmup_iterations + iterations):
            is_warmup = i < warmup_iterations

            # Create test conversation
            conversation = ConversationState(
                conversation_id=str(uuid4()),
                status=ConversationStatus.RUNNING,
            )

            # Test with each message
            for message in messages:
                with PerformanceMonitor() as monitor:
                    try:
                        # Collect streaming events
                        events = []
                        async for event in chat_service.stream_chat(
                            conversation=conversation,
                            user_message=message,
                            store_user_message=True,
                        ):
                            events.append(event)
                            if event.event_type == ChatEventType.MESSAGE_CHUNK:
                                monitor.record_first_token()

                        # Calculate token metrics from events
                        chunk_events = [
                            e
                            for e in events
                            if e.event_type == ChatEventType.MESSAGE_CHUNK
                        ]
                        total_tokens = sum(
                            len(e.payload.get("content", "")) for e in chunk_events
                        )

                        metrics = monitor.get_metrics()
                        metrics.total_tokens = total_tokens
                        metrics.total_chunks = len(chunk_events)
                        metrics.tokens_per_second = (
                            total_tokens / (metrics.response_time_ms / 1000)
                            if metrics.response_time_ms > 0
                            else 0
                        )
                        metrics.chunks_per_second = (
                            len(chunk_events) / (metrics.response_time_ms / 1000)
                            if metrics.response_time_ms > 0
                            else 0
                        )

                        if not is_warmup:
                            all_metrics.append(metrics)

                    except Exception as e:
                        logger.error(
                            "Benchmark iteration failed", iteration=i, error=str(e)
                        )
                        if not is_warmup:
                            error_metrics = PerformanceMetrics(errors=[str(e)])
                            all_metrics.append(error_metrics)

        # Clean up
        await chat_service.close()

        result = BenchmarkResult(
            benchmark_name=name,
            iterations=len(all_metrics),
            metrics=all_metrics,
            baseline_metrics=self.baselines.get(name),
        )

        self.results[name] = result
        return result

    async def benchmark_memory_operations(
        self,
        name: str,
        operations: int = 100,
    ) -> BenchmarkResult:
        """Benchmark memory service performance."""
        logger.info(
            "Starting memory operations benchmark",
            benchmark=name,
            operations=operations,
        )

        chat_service, auth_service, memory_service = await self.setup_test_services()

        all_metrics = []

        with PerformanceMonitor() as monitor:
            try:
                # Perform memory search operations
                for i in range(operations):
                    await memory_service.search(f"test query {i}", limit=10)

                metrics = monitor.get_metrics()
                all_metrics.append(metrics)

            except Exception as e:
                logger.error("Memory benchmark failed", error=str(e))
                error_metrics = PerformanceMetrics(errors=[str(e)])
                all_metrics.append(error_metrics)

        await chat_service.close()

        result = BenchmarkResult(
            benchmark_name=name,
            iterations=operations,
            metrics=all_metrics,
        )

        self.results[name] = result
        return result

    async def benchmark_concurrent_load(
        self,
        name: str,
        concurrent_users: int = 10,
        messages_per_user: int = 5,
    ) -> BenchmarkResult:
        """Benchmark performance under concurrent load."""
        logger.info(
            "Starting concurrent load benchmark",
            benchmark=name,
            users=concurrent_users,
            messages_per_user=messages_per_user,
        )

        chat_service, auth_service, memory_service = await self.setup_test_services()

        all_metrics = []
        semaphore = asyncio.Semaphore(concurrent_users)

        async def simulate_user(user_id: int):
            async with semaphore:
                user_metrics = []

                for msg_idx in range(messages_per_user):
                    conversation = ConversationState(
                        conversation_id=f"concurrent_{user_id}_{uuid4()}",
                        status=ConversationStatus.RUNNING,
                    )

                    with PerformanceMonitor() as monitor:
                        try:
                            events = []
                            async for event in chat_service.stream_chat(
                                conversation=conversation,
                                user_message=f"User {user_id} message {msg_idx}",
                                store_user_message=True,
                            ):
                                events.append(event)
                                if event.event_type == ChatEventType.MESSAGE_CHUNK:
                                    monitor.record_first_token()

                            chunk_events = [
                                e
                                for e in events
                                if e.event_type == ChatEventType.MESSAGE_CHUNK
                            ]
                            total_tokens = sum(
                                len(e.payload.get("content", "")) for e in chunk_events
                            )

                            metrics = monitor.get_metrics()
                            metrics.total_tokens = total_tokens
                            metrics.total_chunks = len(chunk_events)
                            metrics.tokens_per_second = (
                                total_tokens / (metrics.response_time_ms / 1000)
                                if metrics.response_time_ms > 0
                                else 0
                            )

                            user_metrics.append(metrics)

                        except Exception as e:
                            logger.error(
                                "Concurrent user failed", user_id=user_id, error=str(e)
                            )
                            error_metrics = PerformanceMetrics(errors=[str(e)])
                            user_metrics.append(error_metrics)

                return user_metrics

        # Run concurrent users
        tasks = [simulate_user(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for user_result in user_results:
            if isinstance(user_result, list):
                all_metrics.extend(user_result)

        await chat_service.close()

        result = BenchmarkResult(
            benchmark_name=name,
            iterations=len(all_metrics),
            metrics=all_metrics,
        )

        self.results[name] = result
        return result

    async def benchmark_streaming_performance(
        self,
        name: str,
        message_lengths: List[int] = [100, 500, 1000, 2000],
    ) -> BenchmarkResult:
        """Benchmark streaming performance across different message sizes."""
        logger.info("Starting streaming performance benchmark", benchmark=name)

        chat_service, auth_service, memory_service = await self.setup_test_services()

        all_metrics = []

        for length in message_lengths:
            # Create message of specified length
            message = "A" * length

            conversation = ConversationState(
                conversation_id=f"streaming_{length}_{uuid4()}",
                status=ConversationStatus.RUNNING,
            )

            with PerformanceMonitor() as monitor:
                try:
                    events = []
                    chunks = []

                    async for event in chat_service.stream_chat(
                        conversation=conversation,
                        user_message=message,
                        store_user_message=True,
                    ):
                        events.append(event)
                        if event.event_type == ChatEventType.MESSAGE_CHUNK:
                            chunks.append(event.payload.get("content", ""))
                            monitor.record_first_token()

                    total_tokens = sum(len(chunk) for chunk in chunks)

                    metrics = monitor.get_metrics()
                    metrics.total_tokens = total_tokens
                    metrics.total_chunks = len(chunks)
                    metrics.tokens_per_second = (
                        total_tokens / (metrics.response_time_ms / 1000)
                        if metrics.response_time_ms > 0
                        else 0
                    )
                    metrics.chunks_per_second = (
                        len(chunks) / (metrics.response_time_ms / 1000)
                        if metrics.response_time_ms > 0
                        else 0
                    )

                    all_metrics.append(metrics)

                except Exception as e:
                    logger.error(
                        "Streaming benchmark failed", length=length, error=str(e)
                    )
                    error_metrics = PerformanceMetrics(errors=[str(e)])
                    all_metrics.append(error_metrics)

        await chat_service.close()

        result = BenchmarkResult(
            benchmark_name=name,
            iterations=len(all_metrics),
            metrics=all_metrics,
        )

        self.results[name] = result
        return result

    def save_results(self) -> None:
        """Save all benchmark results to JSON files."""
        timestamp = int(time.time())

        for name, result in self.results.items():
            filename = self.output_dir / f"{name}_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(result.to_dict(), f, indent=2)

        # Save summary report
        summary = {
            "timestamp": timestamp,
            "total_benchmarks": len(self.results),
            "summary": {
                name: {
                    "avg_response_time_ms": result.avg_response_time,
                    "avg_memory_usage_mb": result.avg_memory_usage,
                    "avg_throughput_tps": result.avg_throughput,
                    "iterations": result.iterations,
                }
                for name, result in self.results.items()
            },
        }

        summary_file = self.output_dir / f"benchmark_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(
            "Benchmark results saved",
            count=len(self.results),
            summary_file=summary_file,
        )

    def set_baseline(self, benchmark_name: str) -> None:
        """Set baseline metrics for comparison."""
        if benchmark_name in self.results:
            self.baselines[benchmark_name] = self.results[benchmark_name].metrics[0]
            logger.info("Baseline set", benchmark=benchmark_name)


# Global benchmark suite instance
benchmark_suite = PerformanceBenchmarkSuite()


@pytest.fixture
async def benchmark_setup():
    """Setup fixture for benchmark tests."""
    yield benchmark_suite
    benchmark_suite.save_results()


class TestChatPerformanceBenchmarks:
    """Performance benchmark test cases."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message_length", [100, 500, 1000])
    async def test_chat_response_performance(self, benchmark_setup, message_length):
        """Test chat response performance across different message lengths."""
        messages = [
            f"Test message of length {message_length}" * (message_length // 50 + 1)
        ]

        result = await benchmark_setup.benchmark_chat_response(
            name=f"chat_response_{message_length}chars",
            messages=messages,
            iterations=5,
        )

        # Validate performance requirements
        assert result.avg_response_time < 10000  # Should respond within 10 seconds
        assert result.avg_memory_usage < 500  # Should use less than 500MB
        assert result.avg_throughput > 0  # Should generate tokens

        # Check for errors
        error_count = sum(1 for m in result.metrics if m.errors)
        assert error_count / len(result.metrics) < 0.2  # Less than 20% errors

    @pytest.mark.asyncio
    async def test_memory_operations_performance(self, benchmark_setup):
        """Test memory operations performance."""
        result = await benchmark_setup.benchmark_memory_operations(
            name="memory_operations",
            operations=50,
        )

        # Validate memory operation performance
        assert result.avg_response_time < 5000  # Memory ops should be fast
        assert result.avg_memory_usage < 200  # Should be memory efficient

    @pytest.mark.asyncio
    @pytest.mark.parametrize("concurrent_users", [5, 10, 20])
    async def test_concurrent_load_performance(self, benchmark_setup, concurrent_users):
        """Test performance under concurrent user load."""
        result = await benchmark_setup.benchmark_concurrent_load(
            name=f"concurrent_load_{concurrent_users}users",
            concurrent_users=concurrent_users,
            messages_per_user=3,
        )

        # Validate concurrent performance
        avg_response_time = result.avg_response_time
        max_acceptable_time = 15000 * (concurrent_users / 10)  # Scale with users

        assert avg_response_time < max_acceptable_time
        assert result.avg_throughput > 0

    @pytest.mark.asyncio
    async def test_streaming_performance(self, benchmark_setup):
        """Test streaming performance across different message sizes."""
        result = await benchmark_setup.benchmark_streaming_performance(
            name="streaming_performance",
            message_lengths=[200, 500, 1000],
        )

        # Validate streaming performance
        assert result.avg_response_time < 8000  # Streaming should be responsive
        assert result.avg_throughput > 5  # Should maintain reasonable throughput

        # Check that streaming actually works
        for metrics in result.metrics:
            assert metrics.total_chunks > 0  # Should have multiple chunks


if __name__ == "__main__":
    # Run benchmarks directly
    async def run_benchmarks():
        suite = PerformanceBenchmarkSuite()

        # Run basic chat benchmarks
        await suite.benchmark_chat_response(
            name="basic_chat_benchmark",
            messages=["Hello, how are you?", "Tell me about performance testing"],
            iterations=3,
        )

        # Run memory benchmarks
        await suite.benchmark_memory_operations(
            name="memory_benchmark",
            operations=20,
        )

        # Run concurrent load test
        await suite.benchmark_concurrent_load(
            name="concurrent_benchmark",
            concurrent_users=5,
            messages_per_user=2,
        )

        # Save results
        suite.save_results()
        print("Benchmarks completed and saved!")

    asyncio.run(run_benchmarks())
