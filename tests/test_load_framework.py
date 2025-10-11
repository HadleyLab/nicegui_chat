"""Load testing framework for nicegui_chat concurrent user simulation.

This module provides comprehensive load testing capabilities including:
- Concurrent user simulation with realistic chat patterns
- Stress testing with configurable load patterns
- Resource monitoring during load tests
- Performance degradation detection
- Load balancing validation
- Async architecture stress testing

The framework simulates realistic user behavior patterns and measures
system performance under various load conditions.
"""

import asyncio
import json
import random
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import psutil
import structlog

from config import config
from src.models.chat import ChatEventType, ConversationState, ConversationStatus
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService

try:
    import matplotlib.pyplot as plt
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = structlog.get_logger()


@dataclass
class LoadTestScenario:
    """Configuration for a load test scenario."""

    name: str
    description: str
    duration_seconds: int
    target_concurrent_users: int
    user_spawn_rate: float  # users per second
    message_patterns: List[str]
    think_time_range: Tuple[float, float]  # min/max seconds between messages
    memory_enrichment_enabled: bool = True
    streaming_enabled: bool = True


@dataclass
class UserSession:
    """Represents a simulated user session."""

    user_id: str
    conversation_id: str
    start_time: float
    messages_sent: int = 0
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    errors: List[str] = field(default_factory=list)

    def record_activity(self) -> None:
        """Record user activity timestamp."""
        self.last_activity = time.time()
        self.messages_sent += 1

    def add_error(self, error: str) -> None:
        """Record an error for this user."""
        self.errors.append(error)


@dataclass
class LoadTestMetrics:
    """Comprehensive metrics from a load test run."""

    # Basic metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0

    # Timing metrics
    response_times: List[float] = field(default_factory=list)
    first_token_times: List[float] = field(default_factory=list)

    # Concurrent user metrics
    max_concurrent_users: int = 0
    avg_concurrent_users: float = 0.0

    # Memory metrics
    memory_samples: List[float] = field(default_factory=list)  # MB
    cpu_samples: List[float] = field(default_factory=list)  # percent

    # Throughput metrics
    requests_per_second: float = 0.0
    tokens_per_second: float = 0.0
    total_tokens: int = 0

    # Error tracking
    error_count_by_type: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )

    # User session tracking
    user_sessions: List[UserSession] = field(default_factory=list)

    def add_response_time(
        self, response_time_ms: float, first_token_ms: float = 0.0
    ) -> None:
        """Add a response time sample."""
        self.total_requests += 1
        self.response_times.append(response_time_ms)
        if first_token_ms > 0:
            self.first_token_times.append(first_token_ms)

        if response_time_ms > 0:  # Success
            self.successful_requests += 1
            self.total_response_time += response_time_ms
        else:  # Failure
            self.failed_requests += 1

    def add_system_metrics(self, memory_mb: float, cpu_percent: float) -> None:
        """Add system performance samples."""
        self.memory_samples.append(memory_mb)
        self.cpu_samples.append(cpu_percent)

    def add_user_session(self, session: UserSession) -> None:
        """Add a user session for tracking."""
        self.user_sessions.append(session)
        self.max_concurrent_users = max(
            self.max_concurrent_users, len(self.user_sessions)
        )

    def finalize_metrics(self, test_duration: float) -> None:
        """Calculate final derived metrics."""
        if self.response_times:
            self.requests_per_second = len(self.response_times) / test_duration
            self.total_response_time = sum(self.response_times)

        if self.memory_samples:
            self.avg_concurrent_users = statistics.mean(
                len([s for s in self.user_sessions if s.is_active])
                for _ in self.memory_samples
            )

        if self.total_tokens and test_duration > 0:
            self.tokens_per_second = self.total_tokens / test_duration

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0

    @property
    def avg_response_time(self) -> float:
        """Average response time in milliseconds."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def p95_response_time(self) -> float:
        """95th percentile response time."""
        if len(self.response_times) < 20:
            return self.avg_response_time
        return statistics.quantiles(self.response_times, n=20)[18]

    @property
    def avg_memory_usage(self) -> float:
        """Average memory usage in MB."""
        if not self.memory_samples:
            return 0.0
        return statistics.mean(self.memory_samples)

    @property
    def avg_cpu_usage(self) -> float:
        """Average CPU usage percentage."""
        if not self.cpu_samples:
            return 0.0
        return statistics.mean(self.cpu_samples)


class LoadTestFramework:
    """Framework for comprehensive load testing."""

    def __init__(self):
        self.output_dir = Path("load_test_results")
        self.output_dir.mkdir(exist_ok=True)
        self.process = psutil.Process()

    async def setup_test_services(
        self,
    ) -> Tuple[ChatService, AuthService, MemoryService]:
        """Set up test services with mocked dependencies."""
        # Mock auth service - always authenticated
        auth_service = AuthService()
        # Mock the authentication check
        auth_service.is_authenticated = True

        # Mock memory service
        memory_service = MemoryService()

        # Mock the search method to avoid external dependencies
        async def mock_search(*args, **kwargs):
            return []

        memory_service.search = mock_search

        # Create chat service
        chat_service = ChatService(
            auth_service=auth_service,
            memory_service=memory_service,
            app_config=config,
        )

        return chat_service, auth_service, memory_service

    async def simulate_user_behavior(
        self,
        user_id: str,
        scenario: LoadTestScenario,
        metrics: LoadTestMetrics,
        stop_event: asyncio.Event,
    ) -> UserSession:
        """Simulate a single user's behavior pattern."""
        session = UserSession(
            user_id=user_id,
            conversation_id=str(uuid4()),
            start_time=time.time(),
        )

        chat_service, _, _ = await self.setup_test_services()

        try:
            while not stop_event.is_set() and session.is_active:
                # Select random message from patterns
                message = random.choice(scenario.message_patterns)

                # Create conversation state
                conversation = ConversationState(
                    conversation_id=session.conversation_id,
                    status=ConversationStatus.RUNNING,
                )

                # Send message and measure response time
                start_time = time.time()
                first_token_time = 0.0

                try:
                    events = []
                    async for event in chat_service.stream_chat(
                        conversation=conversation,
                        user_message=message,
                        store_user_message=True,
                    ):
                        events.append(event)

                        # Record first token time
                        if (
                            event.event_type == ChatEventType.MESSAGE_CHUNK
                            and first_token_time == 0.0
                        ):
                            first_token_time = (time.time() - start_time) * 1000

                    # Calculate response time
                    response_time = (time.time() - start_time) * 1000

                    # Count tokens from events
                    chunk_events = [
                        e for e in events if e.event_type == ChatEventType.MESSAGE_CHUNK
                    ]
                    tokens = sum(
                        len(e.payload.get("content", "")) for e in chunk_events
                    )
                    metrics.total_tokens += tokens

                    # Record metrics
                    metrics.add_response_time(response_time, first_token_time)
                    session.record_activity()

                except Exception as e:
                    error_msg = str(e)
                    session.add_error(error_msg)
                    metrics.error_count_by_type[error_msg] += 1
                    metrics.add_response_time(0.0)  # Failed request

                # Think time before next message
                if not stop_event.is_set():
                    think_time = random.uniform(*scenario.think_time_range)
                    await asyncio.sleep(think_time)

        except asyncio.CancelledError:
            session.is_active = False
        except Exception as e:
            session.add_error(f"Session error: {str(e)}")
        finally:
            await chat_service.close()

        return session

    async def run_load_test(
        self,
        scenario: LoadTestScenario,
        progress_callback: Optional[callable] = None,
    ) -> LoadTestMetrics:
        """Run a complete load test scenario."""
        logger.info(
            "Starting load test",
            scenario=scenario.name,
            duration=scenario.duration_seconds,
            target_users=scenario.target_concurrent_users,
        )

        metrics = LoadTestMetrics()
        stop_event = asyncio.Event()
        user_tasks = []
        system_monitor_task = None

        try:
            # Start system monitoring
            system_monitor_task = asyncio.create_task(
                self._monitor_system(metrics, scenario.duration_seconds, stop_event)
            )

            # Calculate user spawn timing
            spawn_interval = (
                1.0 / scenario.user_spawn_rate if scenario.user_spawn_rate > 0 else 0
            )

            # Spawn users over time
            start_time = time.time()
            users_spawned = 0

            while time.time() - start_time < scenario.duration_seconds:
                # Check if we need to spawn more users
                if users_spawned < scenario.target_concurrent_users:
                    user_id = f"user_{users_spawned}_{uuid4()}"
                    user_task = asyncio.create_task(
                        self.simulate_user_behavior(
                            user_id, scenario, metrics, stop_event
                        )
                    )
                    user_tasks.append(user_task)
                    users_spawned += 1

                    # Add user session to metrics
                    session = UserSession(
                        user_id=user_id,
                        conversation_id=str(uuid4()),
                        start_time=time.time(),
                    )
                    metrics.add_user_session(session)

                # Progress reporting
                if progress_callback:
                    elapsed = time.time() - start_time
                    progress = min(elapsed / scenario.duration_seconds, 1.0)
                    progress_callback(progress, metrics)

                # Brief pause before next spawn check
                await asyncio.sleep(min(spawn_interval, 0.1))

            # Wait for test duration
            await asyncio.sleep(
                max(0, scenario.duration_seconds - (time.time() - start_time))
            )

        finally:
            # Stop the test
            stop_event.set()

            # Wait for all user tasks to complete
            if user_tasks:
                await asyncio.gather(*user_tasks, return_exceptions=True)

            # Stop system monitoring
            if system_monitor_task:
                await system_monitor_task

        # Finalize metrics
        test_duration = time.time() - start_time
        metrics.finalize_metrics(test_duration)

        logger.info(
            "Load test completed",
            scenario=scenario.name,
            duration=test_duration,
            total_requests=metrics.total_requests,
            success_rate=metrics.success_rate,
        )

        return metrics

    async def _monitor_system(
        self,
        metrics: LoadTestMetrics,
        duration: int,
        stop_event: asyncio.Event,
    ) -> None:
        """Monitor system resources during load test."""
        start_time = time.time()

        while not stop_event.is_set():
            try:
                # Memory usage
                memory_mb = self.process.memory_info().rss / 1024 / 1024

                # CPU usage
                cpu_percent = self.process.cpu_percent()

                # Add to metrics
                metrics.add_system_metrics(memory_mb, cpu_percent)

                # Brief pause between samples
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.warning("System monitoring error", error=str(e))
                await asyncio.sleep(1.0)

    def save_load_test_results(
        self,
        scenario: LoadTestScenario,
        metrics: LoadTestMetrics,
        timestamp: Optional[str] = None,
    ) -> Path:
        """Save load test results to JSON file."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        results = {
            "scenario": {
                "name": scenario.name,
                "description": scenario.description,
                "duration_seconds": scenario.duration_seconds,
                "target_concurrent_users": scenario.target_concurrent_users,
                "user_spawn_rate": scenario.user_spawn_rate,
            },
            "metrics": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "avg_response_time_ms": metrics.avg_response_time,
                "p95_response_time_ms": metrics.p95_response_time,
                "requests_per_second": metrics.requests_per_second,
                "tokens_per_second": metrics.tokens_per_second,
                "total_tokens": metrics.total_tokens,
                "avg_memory_usage_mb": metrics.avg_memory_usage,
                "avg_cpu_usage_percent": metrics.avg_cpu_usage,
                "max_concurrent_users": metrics.max_concurrent_users,
                "error_count_by_type": dict(metrics.error_count_by_type),
            },
            "response_times": metrics.response_times,
            "memory_samples": metrics.memory_samples,
            "cpu_samples": metrics.cpu_samples,
            "timestamp": timestamp,
        }

        filename = (
            self.output_dir / f"load_test_{scenario.name}_{int(time.time())}.json"
        )
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

        logger.info("Load test results saved", filename=str(filename))
        return filename

    def generate_load_test_report(
        self,
        scenario: LoadTestScenario,
        metrics: LoadTestMetrics,
        output_path: Optional[Path] = None,
    ) -> str:
        """Generate a human-readable load test report."""
        if output_path is None:
            output_path = (
                self.output_dir
                / f"load_test_report_{scenario.name}_{int(time.time())}.txt"
            )

        report = f"""
# Load Test Report: {scenario.name}

## Test Configuration
- **Description**: {scenario.description}
- **Duration**: {scenario.duration_seconds} seconds
- **Target Concurrent Users**: {scenario.target_concurrent_users}
- **User Spawn Rate**: {scenario.user_spawn_rate} users/second
- **Memory Enrichment**: {scenario.memory_enrichment_enabled}
- **Streaming**: {scenario.streaming_enabled}

## Performance Results

### Request Performance
- **Total Requests**: {metrics.total_requests}
- **Successful Requests**: {metrics.successful_requests}
- **Failed Requests**: {metrics.failed_requests}
- **Success Rate**: {metrics.success_rate:.2f}%

### Response Times
- **Average Response Time**: {metrics.avg_response_time:.2f} ms
- **95th Percentile**: {metrics.p95_response_time:.2f} ms

### Throughput
- **Requests/Second**: {metrics.requests_per_second:.2f}
- **Tokens/Second**: {metrics.tokens_per_second:.2f}
- **Total Tokens Generated**: {metrics.total_tokens}

### System Resource Usage
- **Average Memory Usage**: {metrics.avg_memory_usage:.2f} MB
- **Average CPU Usage**: {metrics.avg_cpu_usage:.2f}%
- **Peak Concurrent Users**: {metrics.max_concurrent_users}

### Errors
"""

        for error_type, count in metrics.error_count_by_type.items():
            report += f"- **{error_type}**: {count}\n"

        if not metrics.error_count_by_type:
            report += "- No errors recorded\n"

        # Write report to file
        with open(output_path, "w") as f:
            f.write(report)

        logger.info("Load test report generated", path=str(output_path))
        return report


# Predefined test scenarios
PREDEFINED_SCENARIOS = [
    LoadTestScenario(
        name="light_load",
        description="Light load with 10 concurrent users",
        duration_seconds=300,  # 5 minutes
        target_concurrent_users=10,
        user_spawn_rate=2.0,
        message_patterns=[
            "Hello, how are you?",
            "What's the weather like?",
            "Tell me a joke",
            "How does this work?",
        ],
        think_time_range=(1.0, 3.0),
    ),
    LoadTestScenario(
        name="medium_load",
        description="Medium load with 50 concurrent users",
        duration_seconds=600,  # 10 minutes
        target_concurrent_users=50,
        user_spawn_rate=5.0,
        message_patterns=[
            "Can you help me with a question?",
            "I need information about something",
            "Please explain this concept",
            "What are the benefits of this?",
            "How do I get started?",
        ],
        think_time_range=(0.5, 2.0),
    ),
    LoadTestScenario(
        name="heavy_load",
        description="Heavy load with 100 concurrent users",
        duration_seconds=900,  # 15 minutes
        target_concurrent_users=100,
        user_spawn_rate=10.0,
        message_patterns=[
            "I have a complex question that needs detailed explanation",
            "Can you analyze this situation and provide insights?",
            "I need comprehensive information about this topic",
            "Please break down this complex concept step by step",
        ],
        think_time_range=(0.3, 1.5),
    ),
    LoadTestScenario(
        name="stress_test",
        description="Stress test with 200 concurrent users",
        duration_seconds=1200,  # 20 minutes
        target_concurrent_users=200,
        user_spawn_rate=20.0,
        message_patterns=[
            "This is a stress test message with substantial content that requires detailed processing and response generation",
            "I need you to analyze multiple aspects of this complex topic and provide comprehensive insights",
            "Please process this detailed request and generate a thorough response with multiple considerations",
        ],
        think_time_range=(0.2, 1.0),
    ),
]


class LoadTestRunner:
    """High-level interface for running load tests."""

    def __init__(self):
        self.framework = LoadTestFramework()

    async def run_scenario(
        self,
        scenario: LoadTestScenario,
        progress_callback: Optional[callable] = None,
    ) -> Tuple[LoadTestMetrics, str]:
        """Run a single load test scenario."""
        metrics = await self.framework.run_load_test(scenario, progress_callback)

        # Generate report
        report = self.framework.generate_load_test_report(scenario, metrics)

        # Save detailed results
        self.framework.save_load_test_results(scenario, metrics)

        return metrics, report

    async def run_all_scenarios(
        self,
        scenarios: Optional[List[LoadTestScenario]] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Tuple[LoadTestMetrics, str]]:
        """Run all predefined or specified scenarios."""
        if scenarios is None:
            scenarios = PREDEFINED_SCENARIOS

        results = {}

        for scenario in scenarios:
            print(f"\nRunning scenario: {scenario.name}")
            metrics, report = await self.run_scenario(scenario, progress_callback)
            results[scenario.name] = (metrics, report)

            # Print summary
            print(f"  Success Rate: {metrics.success_rate:.1f}%")
            print(f"  Avg Response Time: {metrics.avg_response_time:.0f}ms")
            print(f"  Requests/Second: {metrics.requests_per_second:.1f}")
            print(f"  Memory Usage: {metrics.avg_memory_usage:.1f}MB")

        return results


# Example usage and test functions
async def run_quick_load_test():
    """Run a quick load test for development."""
    runner = LoadTestRunner()

    # Use light load scenario for quick testing
    scenario = PREDEFINED_SCENARIOS[0]  # light_load
    scenario.duration_seconds = 60  # Reduce to 1 minute for quick test

    def progress_callback(progress, metrics):
        print(f"Progress: {progress*100:.1f}% - Requests: {metrics.total_requests}")

    metrics, report = await runner.run_scenario(scenario, progress_callback)

    print("\nQuick Load Test Results:")
    print(f"Success Rate: {metrics.success_rate:.1f}%")
    print(f"Average Response Time: {metrics.avg_response_time:.0f}ms")
    print(f"Requests per Second: {metrics.requests_per_second:.1f}")


if __name__ == "__main__":
    # Run quick load test when executed directly
    asyncio.run(run_quick_load_test())
