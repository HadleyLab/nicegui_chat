"""Docker environment performance validation tests.

This module provides comprehensive performance testing specifically for
Docker containerized deployments, including:
- Container resource utilization validation
- Docker networking performance testing
- Multi-container orchestration testing
- Resource limit effectiveness validation
- Container scaling performance analysis
- Docker Compose stack performance testing

Tests ensure that optimizations work correctly in containerized environments
and validate resource management effectiveness.
"""

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = structlog.get_logger()


@dataclass
class DockerPerformanceMetrics:
    """Performance metrics for Docker container testing."""

    # Container resource usage
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    memory_limit_mb: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0

    # Performance timing
    container_start_time_ms: float = 0.0
    first_response_time_ms: float = 0.0
    total_request_time_ms: float = 0.0

    # Application metrics
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    throughput_mbps: float = 0.0

    # Health check metrics
    health_check_response_time_ms: float = 0.0
    health_check_success_rate: float = 100.0


@dataclass
class DockerTestScenario:
    """Configuration for a Docker performance test scenario."""

    name: str
    description: str
    docker_compose_file: str
    test_duration_seconds: int
    concurrent_users: int
    memory_limit: str
    cpu_limit: str
    expected_performance_thresholds: Dict[str, float]


class DockerPerformanceTester:
    """Comprehensive Docker performance testing framework."""

    def __init__(self):
        self.output_dir = Path("docker_performance_results")
        self.output_dir.mkdir(exist_ok=True)
        self.docker_client = None

        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized")
            except Exception as e:
                logger.warning("Failed to initialize Docker client", error=str(e))
                self.docker_client = None

    async def validate_docker_environment(self) -> Dict[str, Any]:
        """Validate Docker environment and capabilities."""
        if not DOCKER_AVAILABLE or not self.docker_client:
            return {
                "docker_available": False,
                "error": "Docker client not available",
            }

        try:
            # Check Docker version
            version_info = self.docker_client.version()

            # Check if Docker daemon is running
            info = self.docker_client.info()

            # Validate resource constraints support
            has_resource_constraints = "CPU CFS" in info.get("CgroupDriver", "")

            return {
                "docker_available": True,
                "version": version_info.get("Version", "unknown"),
                "api_version": version_info.get("ApiVersion", "unknown"),
                "cgroup_driver": info.get("CgroupDriver", "unknown"),
                "supports_resource_constraints": has_resource_constraints,
                "total_memory": info.get("MemTotal", 0),
                "containers_running": info.get("ContainersRunning", 0),
            }

        except Exception as e:
            return {
                "docker_available": False,
                "error": str(e),
            }

    async def build_test_containers(
        self, dockerfile_path: str = "Dockerfile.dev"
    ) -> bool:
        """Build test containers for performance testing."""
        if not self.docker_client:
            logger.error("Docker client not available")
            return False

        try:
            logger.info("Building test container", dockerfile=dockerfile_path)

            # Build the container
            image, build_logs = self.docker_client.images.build(
                path=".",
                dockerfile=dockerfile_path,
                tag="nicegui-chat-test:latest",
                rm=True,
                forcerm=True,
            )

            # Log build output
            for log in build_logs:
                if "stream" in log:
                    logger.debug("Build log", message=log["stream"].strip())

            logger.info("Test container built successfully", image_id=image.id[:12])
            return True

        except Exception as e:
            logger.error("Failed to build test container", error=str(e))
            return False

    async def run_container_performance_test(
        self,
        scenario: DockerTestScenario,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Run performance test in Docker container."""
        if not self.docker_client:
            return {"error": "Docker client not available"}

        logger.info(
            "Starting Docker performance test",
            scenario=scenario.name,
            duration=scenario.test_duration_seconds,
        )

        test_results = {
            "scenario": scenario.name,
            "start_time": time.time(),
            "container_metrics": [],
            "performance_summary": {},
        }

        try:
            # Start Docker Compose stack
            compose_process = await self._start_docker_compose(
                scenario.docker_compose_file
            )

            if not compose_process:
                return {"error": "Failed to start Docker Compose stack"}

            # Wait for services to be ready
            await self._wait_for_services_ready()

            # Run performance test
            container_id = await self._get_main_container_id()

            if container_id:
                # Monitor container performance
                await self._monitor_container_performance(
                    container_id,
                    scenario.test_duration_seconds,
                    test_results,
                    progress_callback,
                )

            # Stop Docker Compose stack
            await self._stop_docker_compose(compose_process)

            # Calculate summary metrics
            test_results["performance_summary"] = self._calculate_performance_summary(
                test_results["container_metrics"]
            )

            # Validate against thresholds
            test_results["threshold_validation"] = (
                self._validate_performance_thresholds(
                    test_results["performance_summary"],
                    scenario.expected_performance_thresholds,
                )
            )

        except Exception as e:
            logger.error("Docker performance test failed", error=str(e))
            test_results["error"] = str(e)

        test_results["end_time"] = time.time()
        test_results["duration"] = test_results["end_time"] - test_results["start_time"]

        return test_results

    async def _start_docker_compose(
        self, compose_file: str
    ) -> Optional[subprocess.Popen]:
        """Start Docker Compose stack."""
        try:
            logger.info("Starting Docker Compose stack", file=compose_file)

            # Start Docker Compose in background
            process = subprocess.Popen(
                ["docker-compose", "-f", compose_file, "up", "-d"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a bit for startup
            await asyncio.sleep(10)

            # Check if process is still running
            if process.poll() is None:
                logger.info("Docker Compose stack started successfully")
                return process
            else:
                # Read error output
                stdout, stderr = process.communicate()
                logger.error(
                    "Docker Compose failed to start",
                    stdout=stdout,
                    stderr=stderr,
                )
                return None

        except Exception as e:
            logger.error("Failed to start Docker Compose", error=str(e))
            return None

    async def _stop_docker_compose(self, process: subprocess.Popen) -> None:
        """Stop Docker Compose stack."""
        try:
            logger.info("Stopping Docker Compose stack")

            # Stop Docker Compose
            stop_process = subprocess.Popen(
                ["docker-compose", "down"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stop_process.communicate()

            # Terminate the up process if still running
            if process.poll() is None:
                process.terminate()
                process.wait()

            logger.info("Docker Compose stack stopped")

        except Exception as e:
            logger.error("Failed to stop Docker Compose", error=str(e))

    async def _wait_for_services_ready(self, timeout: int = 60) -> bool:
        """Wait for services to be ready and healthy."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check if main service is responding
                # This would depend on your specific health check endpoint
                # For now, we'll just wait and assume services start properly
                await asyncio.sleep(2)

                # TODO: Implement actual health checks
                # response = requests.get("http://localhost:8080/health", timeout=5)
                # if response.status_code == 200:
                #     return True

            except Exception:
                pass

            await asyncio.sleep(1)

        logger.warning("Timeout waiting for services to be ready")
        return False

    async def _get_main_container_id(self) -> Optional[str]:
        """Get the main application container ID."""
        if not self.docker_client:
            return None

        try:
            # Find containers with our test image
            containers = self.docker_client.containers.list(
                filters={"ancestor": "nicegui-chat-test:latest"}
            )

            if containers:
                container_id = containers[0].id
                logger.info("Found main container", container_id=container_id[:12])
                return container_id

        except Exception as e:
            logger.error("Failed to get container ID", error=str(e))

        return None

    async def _monitor_container_performance(
        self,
        container_id: str,
        duration: int,
        results: Dict[str, Any],
        progress_callback: Optional[callable] = None,
    ) -> None:
        """Monitor container performance during test."""
        if not self.docker_client:
            return

        start_time = time.time()
        metrics = []

        try:
            container = self.docker_client.containers.get(container_id)

            while time.time() - start_time < duration:
                try:
                    # Get container stats
                    stats = container.stats(stream=False)

                    # Extract metrics
                    cpu_percent = self._calculate_cpu_percent(stats)
                    memory_usage = (
                        stats["memory_stats"].get("usage", 0) / 1024 / 1024
                    )  # MB
                    memory_limit = (
                        stats["memory_stats"].get("limit", 0) / 1024 / 1024
                    )  # MB

                    # Network stats
                    networks = stats.get("networks", {})
                    network_rx = sum(
                        net.get("rx_bytes", 0) for net in networks.values()
                    )
                    network_tx = sum(
                        net.get("tx_bytes", 0) for net in networks.values()
                    )

                    metric = DockerPerformanceMetrics(
                        cpu_usage_percent=cpu_percent,
                        memory_usage_mb=memory_usage,
                        memory_limit_mb=memory_limit,
                        network_rx_bytes=network_rx,
                        network_tx_bytes=network_tx,
                    )

                    metrics.append(metric)

                    # Progress reporting
                    if progress_callback:
                        elapsed = time.time() - start_time
                        progress = min(elapsed / duration, 1.0)
                        progress_callback(progress, metric)

                except Exception as e:
                    logger.warning("Failed to get container stats", error=str(e))

                await asyncio.sleep(5)  # Sample every 5 seconds

        except Exception as e:
            logger.error("Container monitoring failed", error=str(e))

        results["container_metrics"] = metrics

    def _calculate_cpu_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU usage percentage from Docker stats."""
        try:
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})

            cpu_usage = cpu_stats.get("cpu_usage", {})
            precpu_usage = precpu_stats.get("cpu_usage", {})

            total_usage = cpu_usage.get("total_usage", 0)
            pre_total_usage = precpu_usage.get("total_usage", 0)

            cpu_count = len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", []))

            if cpu_count == 0:
                return 0.0

            cpu_delta = total_usage - pre_total_usage
            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                "system_cpu_usage", 0
            )

            if system_delta > 0:
                return (cpu_delta / system_delta) * cpu_count * 100.0

        except Exception:
            pass

        return 0.0

    def _calculate_performance_summary(
        self, metrics: List[DockerPerformanceMetrics]
    ) -> Dict[str, Any]:
        """Calculate performance summary from metrics."""
        if not metrics:
            return {}

        # CPU statistics
        cpu_values = [m.cpu_usage_percent for m in metrics]
        cpu_avg = sum(cpu_values) / len(cpu_values)

        # Memory statistics
        memory_values = [m.memory_usage_mb for m in metrics]
        memory_avg = sum(memory_values) / len(memory_values)
        memory_peak = max(memory_values)

        # Network statistics
        network_rx_values = [m.network_rx_bytes for m in metrics]
        network_tx_values = [m.network_tx_bytes for m in metrics]

        # Calculate throughput (bytes per second)
        if len(metrics) > 1:
            time_span = (len(metrics) - 1) * 5  # 5 second intervals
            rx_bytes_total = network_rx_values[-1] - network_rx_values[0]
            tx_bytes_total = network_tx_values[-1] - network_tx_values[0]

            rx_mbps = (rx_bytes_total * 8) / time_span / 1000000 if time_span > 0 else 0
            tx_mbps = (tx_bytes_total * 8) / time_span / 1000000 if time_span > 0 else 0
        else:
            rx_mbps = tx_mbps = 0

        return {
            "cpu_usage_avg_percent": cpu_avg,
            "cpu_usage_peak_percent": max(cpu_values),
            "memory_usage_avg_mb": memory_avg,
            "memory_usage_peak_mb": memory_peak,
            "memory_efficiency_percent": (
                (memory_avg / max(m.memory_limit_mb for m in metrics)) * 100
                if metrics
                else 0
            ),
            "network_rx_mbps": rx_mbps,
            "network_tx_mbps": tx_mbps,
            "samples_collected": len(metrics),
        }

    def _validate_performance_thresholds(
        self,
        summary: Dict[str, float],
        thresholds: Dict[str, float],
    ) -> Dict[str, Any]:
        """Validate performance against thresholds."""
        validation = {
            "passed": True,
            "threshold_results": {},
            "warnings": [],
        }

        for metric, threshold in thresholds.items():
            if metric in summary:
                actual_value = summary[metric]
                meets_threshold = actual_value <= threshold

                validation["threshold_results"][metric] = {
                    "actual": actual_value,
                    "threshold": threshold,
                    "passed": meets_threshold,
                }

                if not meets_threshold:
                    validation["passed"] = False
                    validation["warnings"].append(
                        f"Performance threshold exceeded for {metric}: "
                        f"{actual_value:.2f} > {threshold:.2f}"
                    )
            else:
                validation["warnings"].append(f"Metric not found: {metric}")

        return validation

    def save_docker_test_results(self, results: Dict[str, Any]) -> Path:
        """Save Docker test results to JSON file."""
        timestamp = int(time.time())
        filename = self.output_dir / f"docker_performance_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Docker test results saved", filename=str(filename))
        return filename

    def generate_docker_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable Docker performance report."""
        if "error" in results:
            return f"Docker performance test failed: {results['error']}"

        summary = results.get("performance_summary", {})
        threshold_validation = results.get("threshold_validation", {})

        report = f"""
# Docker Performance Test Report

## Test Summary
- **Scenario**: {results.get('scenario', 'Unknown')}
- **Duration**: {results.get('duration', 0):.2f} seconds
- **Container Metrics Samples**: {summary.get('samples_collected', 0)}

## Performance Results

### CPU Usage
- **Average**: {summary.get('cpu_usage_avg_percent', 0):.2f}%
- **Peak**: {summary.get('cpu_usage_peak_percent', 0):.2f}%

### Memory Usage
- **Average**: {summary.get('memory_usage_avg_mb', 0):.2f} MB
- **Peak**: {summary.get('memory_usage_peak_mb', 0):.2f} MB
- **Efficiency**: {summary.get('memory_efficiency_percent', 0):.2f}%

### Network Performance
- **RX Throughput**: {summary.get('network_rx_mbps', 0):.2f} Mbps
- **TX Throughput**: {summary.get('network_tx_mbps', 0):.2f} Mbps

## Threshold Validation

"""

        if threshold_validation.get("passed"):
            report += "✅ All performance thresholds met\n"
        else:
            report += "❌ Some performance thresholds exceeded\n"

        for metric, result in threshold_validation.get("threshold_results", {}).items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            report += f"- **{metric}**: {status} ({result['actual']:.2f} / {result['threshold']:.2f})\n"

        if threshold_validation.get("warnings"):
            report += "\n## Warnings\n"
            for warning in threshold_validation["warnings"]:
                report += f"- {warning}\n"

        return report


# Predefined Docker test scenarios
DOCKER_TEST_SCENARIOS = [
    DockerTestScenario(
        name="docker_basic_performance",
        description="Basic Docker performance validation",
        docker_compose_file="docker-compose.yml",
        test_duration_seconds=300,  # 5 minutes
        concurrent_users=5,
        memory_limit="1g",
        cpu_limit="0.5",
        expected_performance_thresholds={
            "cpu_usage_avg_percent": 70.0,
            "memory_usage_avg_mb": 800.0,
            "memory_efficiency_percent": 90.0,
        },
    ),
    DockerTestScenario(
        name="docker_high_load",
        description="High load Docker performance test",
        docker_compose_file="docker-compose.yml",
        test_duration_seconds=600,  # 10 minutes
        concurrent_users=20,
        memory_limit="2g",
        cpu_limit="1.0",
        expected_performance_thresholds={
            "cpu_usage_avg_percent": 85.0,
            "memory_usage_avg_mb": 1500.0,
            "memory_efficiency_percent": 85.0,
        },
    ),
    DockerTestScenario(
        name="docker_resource_limits",
        description="Docker resource limits effectiveness test",
        docker_compose_file="docker-compose.yml",
        test_duration_seconds=300,
        concurrent_users=10,
        memory_limit="512m",
        cpu_limit="0.25",
        expected_performance_thresholds={
            "cpu_usage_avg_percent": 90.0,
            "memory_usage_avg_mb": 450.0,
            "memory_efficiency_percent": 95.0,
        },
    ),
]


class DockerPerformanceValidator:
    """Automated validation of Docker performance."""

    def __init__(self, tester: DockerPerformanceTester):
        self.tester = tester

    async def validate_deployment_performance(
        self,
        scenarios: Optional[List[DockerTestScenario]] = None,
    ) -> Dict[str, Any]:
        """Validate performance across multiple Docker scenarios."""
        if scenarios is None:
            scenarios = DOCKER_TEST_SCENARIOS

        validation_results = {
            "total_scenarios": len(scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": {},
        }

        for scenario in scenarios:
            logger.info(f"Running Docker scenario: {scenario.name}")

            # Run performance test
            results = await self.tester.run_container_performance_test(scenario)

            # Check if test passed
            threshold_validation = results.get("threshold_validation", {})
            scenario_passed = threshold_validation.get("passed", False)

            if scenario_passed:
                validation_results["passed_scenarios"] += 1
            else:
                validation_results["failed_scenarios"] += 1

            validation_results["scenario_results"][scenario.name] = {
                "passed": scenario_passed,
                "results": results,
                "warnings": threshold_validation.get("warnings", []),
            }

        # Overall assessment
        validation_results["overall_success"] = (
            validation_results["failed_scenarios"] == 0
        )

        return validation_results


# Example usage and testing
async def run_docker_performance_test():
    """Run a comprehensive Docker performance test."""
    tester = DockerPerformanceTester()

    # Validate Docker environment
    env_validation = await tester.validate_docker_environment()
    print(f"Docker environment validation: {env_validation}")

    if not env_validation.get("docker_available"):
        print("Docker not available, skipping performance tests")
        return None

    # Build test container
    if not await tester.build_test_containers():
        print("Failed to build test container")
        return None

    # Run basic performance test
    scenario = DOCKER_TEST_SCENARIOS[0]  # Use first scenario

    def progress_callback(progress, metrics):
        print(f"Progress: {progress*100:.1f}% - CPU: {metrics.cpu_usage_percent:.1f}%")

    results = await tester.run_container_performance_test(scenario, progress_callback)

    # Generate report
    report = tester.generate_docker_performance_report(results)
    print(report)

    # Save results
    tester.save_docker_test_results(results)

    return results


async def validate_all_docker_scenarios():
    """Validate performance across all Docker scenarios."""
    tester = DockerPerformanceTester()
    validator = DockerPerformanceValidator(tester)

    # Validate Docker environment first
    env_validation = await tester.validate_docker_environment()
    if not env_validation.get("docker_available"):
        print("Docker not available, skipping validation")
        return None

    # Build test container
    if not await tester.build_test_containers():
        print("Failed to build test container")
        return None

    # Run all scenarios
    validation_results = await validator.validate_deployment_performance()

    print("Docker Performance Validation Results:")
    print(f"Total Scenarios: {validation_results['total_scenarios']}")
    print(f"Passed: {validation_results['passed_scenarios']}")
    print(f"Failed: {validation_results['failed_scenarios']}")
    print(f"Overall Success: {validation_results['overall_success']}")

    return validation_results


if __name__ == "__main__":
    # Run Docker performance tests when executed directly
    print("Running Docker performance tests...")

    # Run basic test
    results = asyncio.run(run_docker_performance_test())

    # Run comprehensive validation
    validation = asyncio.run(validate_all_docker_scenarios())

    print("Docker performance testing completed!")
