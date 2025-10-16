"""Timeout Reproduction and Load Testing Script.

This script reproduces common timeout scenarios and tests the application's
behavior under various stress conditions to identify bottlenecks.

Usage:
    python -m src.utils.timeout_reproducer --scenario api_stress
    python -m src.utils.timeout_reproducer --scenario memory_pressure
    python -m src.utils.timeout_reproducer --scenario concurrent_requests
"""

import asyncio
import json
import random
import statistics
import time
from pathlib import Path
from typing import Any

import httpx  # type: ignore
import psutil  # type: ignore[import-untyped]
import structlog  # type: ignore

logger = structlog.get_logger()


class TimeoutReproducer:
    """Reproduces timeout scenarios for debugging."""

    def __init__(self) -> None:
        self.results: list[dict] = []

    async def api_stress_test(
        self, num_requests: int = 50, concurrent: int = 10
    ) -> dict:
        """Stress test API endpoints to reproduce timeout issues."""
        logger.info(
            "starting_api_stress_test", requests=num_requests, concurrent=concurrent
        )

        start_time = time.time()

        # Simulate API calls with varying response times
        async def mock_api_call(request_id: int) -> float:
            # Simulate realistic API response times with some outliers
            base_delay = 0.5 + random.random() * 2.0  # 0.5-2.5 seconds

            # Add some slow requests to simulate real-world conditions
            if random.random() < 0.1:  # 10% slow requests
                base_delay += random.random() * 10  # Add up to 10 seconds

            # Add timeout simulation
            if random.random() < 0.05:  # 5% timeouts
                await asyncio.sleep(base_delay)
                raise TimeoutError(f"Request {request_id} timed out")

            await asyncio.sleep(base_delay)
            return base_delay

        # Run concurrent requests
        semaphore = asyncio.Semaphore(concurrent)

        async def limited_request(request_id: int) -> float | None:
            async with semaphore:
                try:
                    return await mock_api_call(request_id)
                except TimeoutError as e:
                    logger.warning(
                        "request_timeout", request_id=request_id, error=str(e)
                    )
                    return None

        tasks = [limited_request(i) for i in range(num_requests)]
        response_times = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None values
        valid_times = [t for t in response_times if isinstance(t, (int, float))]

        total_time = time.time() - start_time

        result = {
            "scenario": "api_stress_test",
            "total_requests": num_requests,
            "successful_requests": len(valid_times),
            "failed_requests": num_requests - len(valid_times),
            "total_time": total_time,
            "requests_per_second": (
                len(valid_times) / total_time if total_time > 0 else 0
            ),
            "avg_response_time": statistics.mean(valid_times) if valid_times else 0,
            "median_response_time": (
                statistics.median(valid_times) if valid_times else 0
            ),
            "min_response_time": min(valid_times) if valid_times else 0,
            "max_response_time": max(valid_times) if valid_times else 0,
            "response_times": valid_times[:100],  # Store first 100 for analysis
        }

        self.results.append(result)
        logger.info("api_stress_test_completed", **result)
        return result

    async def memory_pressure_test(self, duration_seconds: int = 60) -> dict:
        """Test application behavior under memory pressure."""
        logger.info("starting_memory_pressure_test", duration=duration_seconds)

        # Track memory usage over time
        memory_samples = []
        start_time = time.time()

        async def memory_monitor() -> None:
            while time.time() - start_time < duration_seconds:
                try:
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    memory_samples.append(
                        {
                            "timestamp": time.time() - start_time,
                            "rss_mb": memory_info.rss / (1024 * 1024),
                            "vms_mb": memory_info.vms / (1024 * 1024),
                        }
                    )
                    await asyncio.sleep(1.0)
                except Exception as e:
                    logger.error("memory_monitor_error", error=str(e))

        # Simulate memory-intensive operations
        async def memory_stresser() -> None:
            large_objects = []

            while time.time() - start_time < duration_seconds:
                # Create large objects to consume memory
                large_objects.append("x" * (1024 * 1024))  # 1MB strings

                # Occasionally clear some objects to simulate GC pressure
                if len(large_objects) > 100 and random.random() < 0.1:
                    large_objects = large_objects[50:]  # Keep half

                await asyncio.sleep(0.1)

        # Run both tasks concurrently
        await asyncio.gather(memory_monitor(), memory_stresser())

        # Analyze memory usage
        if memory_samples:
            rss_values = [s["rss_mb"] for s in memory_samples]
            result = {
                "scenario": "memory_pressure_test",
                "duration": duration_seconds,
                "samples_collected": len(memory_samples),
                "peak_memory_mb": max(rss_values),
                "avg_memory_mb": statistics.mean(rss_values),
                "memory_growth_rate": self._calculate_growth_rate(memory_samples),
                "memory_samples": memory_samples[:100],  # Store first 100 samples
            }
        else:
            result = {
                "scenario": "memory_pressure_test",
                "duration": duration_seconds,
                "error": "No memory samples collected",
            }

        self.results.append(result)
        logger.info("memory_pressure_test_completed", **result)
        return result

    def _calculate_growth_rate(self, samples: list[dict]) -> float:
        """Calculate memory growth rate in MB/second."""
        if len(samples) < 2:
            return 0.0

        first_sample = samples[0]
        last_sample = samples[-1]

        time_diff = last_sample["timestamp"] - first_sample["timestamp"]
        if time_diff <= 0:
            return 0.0

        memory_diff = last_sample["rss_mb"] - first_sample["rss_mb"]
        return float(memory_diff / time_diff)

    async def concurrent_requests_test(
        self, num_users: int = 20, messages_per_user: int = 5
    ) -> dict:
        """Test concurrent user requests to reproduce race conditions."""
        logger.info(
            "starting_concurrent_requests_test",
            users=num_users,
            messages_per_user=messages_per_user,
        )

        start_time = time.time()

        # Simulate multiple users sending messages concurrently
        async def simulate_user(user_id: int) -> list[float]:
            response_times = []

            for _msg_id in range(messages_per_user):
                request_start = time.time()

                # Simulate message processing time
                processing_time = 0.1 + random.random() * 0.5  # 0.1-0.6 seconds

                # Simulate occasional slow responses
                if random.random() < 0.05:  # 5% slow responses
                    processing_time += random.random() * 5  # Add up to 5 seconds

                await asyncio.sleep(processing_time)
                response_times.append(time.time() - request_start)

            return response_times

        # Run all users concurrently
        tasks = [simulate_user(user_id) for user_id in range(num_users)]
        all_response_times = await asyncio.gather(*tasks)

        # Flatten results
        flat_times = [t for user_times in all_response_times for t in user_times]

        total_time = time.time() - start_time

        result = {
            "scenario": "concurrent_requests_test",
            "total_users": num_users,
            "total_requests": num_users * messages_per_user,
            "total_time": total_time,
            "requests_per_second": (
                len(flat_times) / total_time if total_time > 0 else 0
            ),
            "avg_response_time": statistics.mean(flat_times) if flat_times else 0,
            "median_response_time": statistics.median(flat_times) if flat_times else 0,
            "min_response_time": min(flat_times) if flat_times else 0,
            "max_response_time": max(flat_times) if flat_times else 0,
            "response_times": flat_times[:200],  # Store first 200 for analysis
        }

        self.results.append(result)
        logger.info("concurrent_requests_test_completed", **result)
        return result

    async def network_latency_test(
        self, target_url: str = "https://api.deepseek.com"
    ) -> dict:
        """Test network latency and connectivity issues."""
        logger.info("starting_network_latency_test", target_url=target_url)

        response_times = []
        errors = []

        # Test multiple requests to identify patterns
        for i in range(20):
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(target_url, timeout=30.0)
                    response.raise_for_status()

                response_time = (time.time() - start_time) * 1000  # Convert to ms
                response_times.append(response_time)

                logger.debug(
                    "network_request_success", request_id=i, response_time=response_time
                )

            except Exception as e:
                errors.append(str(e))
                logger.warning("network_request_failed", request_id=i, error=str(e))

            # Small delay between requests
            await asyncio.sleep(0.5)

        result = {
            "scenario": "network_latency_test",
            "target_url": target_url,
            "total_requests": 20,
            "successful_requests": len(response_times),
            "failed_requests": len(errors),
            "avg_response_time_ms": (
                statistics.mean(response_times) if response_times else 0
            ),
            "median_response_time_ms": (
                statistics.median(response_times) if response_times else 0
            ),
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "errors": errors[:10],  # Store first 10 errors
        }

        self.results.append(result)
        logger.info("network_latency_test_completed", **result)
        return result

    async def run_scenario(self, scenario: str, **kwargs: Any) -> dict:
        """Run a specific timeout reproduction scenario."""
        logger.info("running_timeout_scenario", scenario=scenario, kwargs=kwargs)

        if scenario == "api_stress":
            return await self.api_stress_test(**kwargs)
        elif scenario == "memory_pressure":
            return await self.memory_pressure_test(**kwargs)
        elif scenario == "concurrent_requests":
            return await self.concurrent_requests_test(**kwargs)
        elif scenario == "network_latency":
            return await self.network_latency_test(**kwargs)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

    def save_results(self, filename: str | None = None) -> str:
        """Save test results to JSON file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"timeout_reproduction_{timestamp}.json"

        with Path(filename).open("w") as f:
            json.dump(
                {
                    "results": self.results,
                    "generated_at": time.time(),
                    "total_scenarios": len(self.results),
                },
                f,
                indent=2,
            )

        logger.info("results_saved", filename=filename)
        return filename

    def print_summary(self) -> None:
        """Print a summary of all test results."""
        print("\n" + "=" * 80)
        print("⏱️  TIMEOUT REPRODUCTION TEST RESULTS")
        print("=" * 80)

        for result in self.results:
            print(f"\n📋 Scenario: {result['scenario']}")

            if result["scenario"] == "api_stress_test":
                print(f"  Total Requests: {result['total_requests']}")
                print(f"  Successful: {result['successful_requests']}")
                print(f"  Failed: {result['failed_requests']}")
                print(f"  Requests/sec: {result['requests_per_second']:.2f}")
                print(f"  Avg Response Time: {result['avg_response_time']:.3f}s")
                print(f"  Max Response Time: {result['max_response_time']:.3f}s")

            elif result["scenario"] == "memory_pressure_test":
                print(f"  Duration: {result['duration']}s")
                print(f"  Peak Memory: {result['peak_memory_mb']:.1f} MB")
                print(f"  Avg Memory: {result['avg_memory_mb']:.1f} MB")
                print(f"  Growth Rate: {result['memory_growth_rate']:.2f} MB/s")

            elif result["scenario"] == "concurrent_requests_test":
                print(f"  Total Users: {result['total_users']}")
                print(f"  Total Requests: {result['total_requests']}")
                print(f"  Requests/sec: {result['requests_per_second']:.2f}")
                print(f"  Avg Response Time: {result['avg_response_time']:.3f}s")
                print(f"  Max Response Time: {result['max_response_time']:.3f}s")

            elif result["scenario"] == "network_latency_test":
                print(f"  Target: {result['target_url']}")
                print(
                    f"  Successful: {result['successful_requests']}/"
                    f"{result['total_requests']}"
                )
                print(f"  Avg Response Time: {result['avg_response_time_ms']:.1f}ms")
                print(f"  Max Response Time: {result['max_response_time_ms']:.1f}ms")

        print(f"\n📊 Total scenarios run: {len(self.results)}")
        print("=" * 80)


async def main() -> None:
    """Main function to run timeout reproduction tests."""
    reproducer = TimeoutReproducer()

    print("🔬 Starting timeout reproduction tests...")
    print("This will run multiple scenarios to identify potential timeout causes.\n")

    # Run different test scenarios
    scenarios = [
        ("api_stress", {"num_requests": 100, "concurrent": 20}),
        ("memory_pressure", {"duration_seconds": 30}),
        ("concurrent_requests", {"num_users": 15, "messages_per_user": 3}),
        ("network_latency", {"target_url": "https://httpbin.org/delay/1"}),
    ]

    for scenario_name, kwargs in scenarios:
        try:
            print(f"🧪 Running {scenario_name} test...")
            await reproducer.run_scenario(scenario_name, **kwargs)  # type: ignore[arg-type]
            print(f"✅ {scenario_name} test completed\n")
            await asyncio.sleep(2)  # Brief pause between tests
        except Exception as e:
            print(f"❌ {scenario_name} test failed: {e}\n")

    # Print summary
    reproducer.print_summary()

    # Save results
    filename = reproducer.save_results()
    print(f"\n💾 Detailed results saved to: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
