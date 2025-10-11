"""Docker Environment Profiling and Performance Monitoring.

This module provides comprehensive profiling capabilities for diagnosing
Docker environment issues and timeout causes in containerized deployments.

Key Features:
- Resource usage monitoring (CPU, memory, disk I/O)
- Network connectivity and DNS resolution testing
- Environment variable validation and debugging
- Performance benchmarking and bottleneck identification
- Container health and resource constraint analysis

Usage:
    python -m src.utils.docker_profiler
"""

import asyncio
import json
import os
import platform
import socket
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
import structlog

logger = structlog.get_logger()


@dataclass
class ResourceMetrics:
    """Container resource usage metrics."""

    timestamp: float
    cpu_percent: float
    memory_used_mb: float
    memory_percent: float
    disk_read_mb: float
    disk_write_mb: float
    network_rx_mb: float
    network_tx_mb: float
    open_files: int
    process_count: int


@dataclass
class NetworkMetrics:
    """Network connectivity and performance metrics."""

    timestamp: float
    dns_resolution_ms: float
    api_connectivity_ms: Dict[str, float]
    connection_pool_status: Dict[str, Any]
    socket_stats: Dict[str, int]


@dataclass
class ProfilingReport:
    """Comprehensive profiling report."""

    container_info: Dict[str, Any]
    resource_history: List[ResourceMetrics] = field(default_factory=list)
    network_tests: List[NetworkMetrics] = field(default_factory=list)
    environment_issues: List[str] = field(default_factory=list)
    performance_warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class DockerProfiler:
    """Comprehensive Docker environment profiler."""

    def __init__(self):
        self.report = ProfilingReport(container_info=self._get_container_info())
        self.monitoring_active = False

    def _get_container_info(self) -> Dict[str, Any]:
        """Gather container and system information."""
        info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": os.cpu_count(),
            "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "containerized": self._detect_container(),
            "working_directory": os.getcwd(),
            "environment_variables": self._get_relevant_env_vars(),
        }

        # Try to get Docker-specific info
        try:
            info.update(self._get_docker_info())
        except Exception as e:
            logger.warning("failed_to_get_docker_info", error=str(e))

        return info

    def _detect_container(self) -> bool:
        """Detect if running in a container."""
        container_indicators = [
            Path("/.dockerenv"),
            (
                Path("/proc/1/cgroup").read_text().find("docker") >= 0
                if Path("/proc/1/cgroup").exists()
                else False
            ),
        ]
        return any(container_indicators)

    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Get environment variables relevant to the application."""
        relevant_vars = [
            "DEEPSEEK_API_KEY",
            "HEYSOL_API_KEY",
            "DEEPSEEK_BASE_URL",
            "HEYSOL_BASE_URL",
            "HOST",
            "PORT",
            "APP_CONFIG_PATH",
            "PYTHONPATH",
            "PATH",
        ]
        return {var: os.getenv(var, "NOT_SET") for var in relevant_vars}

    def _get_docker_info(self) -> Dict[str, Any]:
        """Get Docker-specific information."""
        docker_info = {}

        try:
            # Get container limits from cgroup
            if Path("/sys/fs/cgroup/memory.max").exists():
                with open("/sys/fs/cgroup/memory.max") as f:
                    docker_info["memory_limit"] = f.read().strip()

            if Path("/sys/fs/cgroup/cpu.max").exists():
                with open("/sys/fs/cgroup/cpu.max") as f:
                    docker_info["cpu_limit"] = f.read().strip()

            # Get container ID if available
            if Path("/proc/1/cgroup").exists():
                with open("/proc/1/cgroup") as f:
                    content = f.read()
                    if "docker" in content:
                        # Extract container ID from cgroup
                        for line in content.split("\n"):
                            if "docker" in line:
                                parts = line.split("/")
                                if len(parts) > 2:
                                    docker_info["container_id"] = parts[-1][:12]
        except Exception as e:
            logger.debug("docker_info_extraction_error", error=str(e))

        return docker_info

    async def monitor_resources(
        self, duration_seconds: int = 300, interval_seconds: float = 5.0
    ) -> List[ResourceMetrics]:
        """Monitor system resources over time."""
        logger.info(
            "starting_resource_monitoring",
            duration=duration_seconds,
            interval=interval_seconds,
        )

        metrics_history = []
        self.monitoring_active = True

        try:
            start_time = time.time()
            while (
                self.monitoring_active and (time.time() - start_time) < duration_seconds
            ):
                try:
                    metrics = await self._collect_resource_metrics()
                    metrics_history.append(metrics)
                    self.report.resource_history.append(metrics)

                    logger.debug("resource_metrics_collected", metrics=metrics.__dict__)
                    await asyncio.sleep(interval_seconds)

                except Exception as e:
                    logger.error("resource_collection_error", error=str(e))
                    await asyncio.sleep(interval_seconds)

        finally:
            self.monitoring_active = False

        logger.info("resource_monitoring_completed", samples=len(metrics_history))
        return metrics_history

    async def _collect_resource_metrics(self) -> ResourceMetrics:
        """Collect current resource usage metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1.0)
            memory = psutil.virtual_memory()

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0

            # Network I/O
            network_io = psutil.net_io_counters()
            network_rx_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0
            network_tx_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0

            # Process information
            process = psutil.Process()
            open_files = len(process.open_files())
            process_count = len(psutil.pids())

            return ResourceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_percent=memory.percent,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb,
                network_rx_mb=network_rx_mb,
                network_tx_mb=network_tx_mb,
                open_files=open_files,
                process_count=process_count,
            )

        except Exception as e:
            logger.error("metrics_collection_failed", error=str(e))
            # Return minimal metrics on error
            return ResourceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_used_mb=0.0,
                memory_percent=0.0,
                disk_read_mb=0.0,
                disk_write_mb=0.0,
                network_rx_mb=0.0,
                network_tx_mb=0.0,
                open_files=0,
                process_count=0,
            )

    async def test_network_connectivity(self) -> NetworkMetrics:
        """Test network connectivity and performance."""
        logger.info("testing_network_connectivity")

        network_metrics = NetworkMetrics(
            timestamp=time.time(),
            dns_resolution_ms=0.0,
            api_connectivity_ms={},
            connection_pool_status={},
            socket_stats={},
        )

        # Test DNS resolution
        start_time = time.time()
        try:
            socket.gethostbyname("api.deepseek.com")
            network_metrics.dns_resolution_ms = (time.time() - start_time) * 1000
        except Exception as e:
            logger.warning("dns_resolution_failed", error=str(e))
            network_metrics.dns_resolution_ms = -1.0

        # Test API endpoints
        api_endpoints = [
            ("deepseek", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")),
            ("heysol", os.getenv("HEYSOL_BASE_URL", "https://api.heysol.ai")),
        ]

        for name, base_url in api_endpoints:
            if base_url and base_url != "NOT_SET":
                start_time = time.time()
                try:
                    import httpx

                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(base_url + "/health", timeout=10.0)
                        response.raise_for_status()
                        network_metrics.api_connectivity_ms[name] = (
                            time.time() - start_time
                        ) * 1000
                except Exception as e:
                    logger.warning("api_connectivity_failed", api=name, error=str(e))
                    network_metrics.api_connectivity_ms[name] = -1.0

        # Get socket statistics
        try:
            network_metrics.socket_stats = self._get_socket_stats()
        except Exception as e:
            logger.debug("socket_stats_collection_failed", error=str(e))

        self.report.network_tests.append(network_metrics)
        return network_metrics

    def _get_socket_stats(self) -> Dict[str, int]:
        """Get socket connection statistics."""
        stats = {}
        try:
            # Count different socket states
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    for conn in proc.connections():
                        state = conn.status
                        stats[state] = stats.get(state, 0) + 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug("socket_stats_error", error=str(e))

        return stats

    def validate_environment(self) -> List[str]:
        """Validate environment variables and configuration."""
        issues = []

        # Check required API keys
        if not os.getenv("DEEPSEEK_API_KEY"):
            issues.append("DEEPSEEK_API_KEY is not set")

        if not os.getenv("HEYSOL_API_KEY"):
            issues.append("HEYSOL_API_KEY is not set")

        # Check API base URLs
        deepseek_url = os.getenv("DEEPSEEK_BASE_URL")
        if deepseek_url and not (
            deepseek_url.startswith("http://") or deepseek_url.startswith("https://")
        ):
            issues.append("DEEPSEEK_BASE_URL must start with http:// or https://")

        heysol_url = os.getenv("HEYSOL_BASE_URL")
        if heysol_url and not (
            heysol_url.startswith("http://") or heysol_url.startswith("https://")
        ):
            issues.append("HEYSOL_BASE_URL must start with http:// or https://")

        # Check file permissions
        config_paths = ["config/app.json", "config/scene.json", "config/system.md"]
        for config_path in config_paths:
            if Path(config_path).exists():
                if not os.access(config_path, os.R_OK):
                    issues.append(f"Cannot read config file: {config_path}")
            else:
                issues.append(f"Config file not found: {config_path}")

        # Check Python path and imports
        try:
            import importlib.util
            if not importlib.util.find_spec("heysol"):
                issues.append("Missing required dependency: heysol")
            if not importlib.util.find_spec("nicegui"):
                issues.append("Missing required dependency: nicegui")
            if not importlib.util.find_spec("pydantic"):
                issues.append("Missing required dependency: pydantic")
        except Exception as e:
            issues.append(f"Dependency check failed: {e}")

        self.report.environment_issues.extend(issues)
        return issues

    def analyze_performance_issues(self) -> List[str]:
        """Analyze collected metrics for performance issues."""
        warnings = []

        if not self.report.resource_history:
            return ["No resource metrics collected"]

        # Analyze resource usage patterns
        recent_metrics = self.report.resource_history[-10:]  # Last 10 samples

        # Check for high CPU usage
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        if avg_cpu > 80:
            warnings.append(f"High CPU usage detected: {avg_cpu:.1f}% average")

        # Check for high memory usage
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        if avg_memory > 85:
            warnings.append(f"High memory usage detected: {avg_memory:.1f}% average")

        # Check for memory leaks (increasing memory usage)
        if len(recent_metrics) >= 5:
            first_half = recent_metrics[: len(recent_metrics) // 2]
            second_half = recent_metrics[len(recent_metrics) // 2 :]

            first_avg = sum(m.memory_used_mb for m in first_half) / len(first_half)
            second_avg = sum(m.memory_used_mb for m in second_half) / len(second_half)

            if second_avg > first_avg * 1.2:  # 20% increase
                warnings.append("Potential memory leak detected")

        # Check for excessive file handles
        max_open_files = max(m.open_files for m in recent_metrics)
        if max_open_files > 1000:
            warnings.append(f"High number of open files: {max_open_files}")

        # Check network issues
        if self.report.network_tests:
            latest_network = self.report.network_tests[-1]

            if latest_network.dns_resolution_ms > 1000:
                warnings.append(
                    f"Slow DNS resolution: {latest_network.dns_resolution_ms:.0f}ms"
                )

            for api_name, response_time in latest_network.api_connectivity_ms.items():
                if response_time > 5000:
                    warnings.append(
                        f"Slow {api_name} API response: {response_time:.0f}ms"
                    )
                elif response_time == -1:
                    warnings.append(f"Failed to connect to {api_name} API")

        self.report.performance_warnings.extend(warnings)
        return warnings

    def generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []

        # Resource allocation recommendations
        if self.report.container_info.get("memory_limit"):
            try:
                memory_limit = int(self.report.container_info["memory_limit"])
                if memory_limit > 8 * 1024 * 1024 * 1024:  # 8GB
                    recommendations.append(
                        "Consider reducing memory limit from current allocation"
                    )
            except (ValueError, TypeError):
                pass

        # CPU recommendations
        cpu_count = self.report.container_info.get("cpu_count", 1)
        if cpu_count > 4:
            recommendations.append(
                "Consider setting explicit CPU limits in docker-compose.yml"
            )

        # Network recommendations
        if self.report.performance_warnings:
            slow_apis = [
                w for w in self.report.performance_warnings if "API response" in w
            ]
            if slow_apis:
                recommendations.append(
                    "Implement connection pooling and retry logic for API calls"
                )
                recommendations.append(
                    "Consider caching API responses for frequently accessed data"
                )

        # Environment recommendations
        if self.report.environment_issues:
            missing_keys = [
                i for i in self.report.environment_issues if "API_KEY is not set" in i
            ]
            if missing_keys:
                recommendations.append(
                    "Ensure all required API keys are set in environment variables"
                )

        # General optimizations
        recommendations.extend(
            [
                "Implement proper logging levels (avoid DEBUG in production)",
                "Add connection pooling for external API calls",
                "Consider implementing circuit breaker pattern for external services",
                "Monitor application metrics with proper alerting",
                "Implement graceful shutdown handling",
            ]
        )

        self.report.recommendations.extend(recommendations)
        return recommendations

    async def run_comprehensive_profile(
        self, duration_seconds: int = 300
    ) -> ProfilingReport:
        """Run comprehensive profiling analysis."""
        logger.info("starting_comprehensive_profiling", duration=duration_seconds)

        # Validate environment first
        self.validate_environment()

        # Start resource monitoring
        monitoring_task = asyncio.create_task(self.monitor_resources(duration_seconds))

        # Test network connectivity multiple times
        for i in range(3):
            await self.test_network_connectivity()
            await asyncio.sleep(
                duration_seconds / 4
            )  # Spread tests throughout monitoring

        # Wait for monitoring to complete
        await monitoring_task

        # Analyze results
        self.analyze_performance_issues()
        self.generate_recommendations()

        # Save report
        self.save_report()

        logger.info("comprehensive_profiling_completed")
        return self.report

    def save_report(self, filename: Optional[str] = None) -> str:
        """Save profiling report to JSON file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"docker_profile_report_{timestamp}.json"

        report_data = {
            "container_info": self.report.container_info,
            "resource_history": [m.__dict__ for m in self.report.resource_history],
            "network_tests": [n.__dict__ for n in self.report.network_tests],
            "environment_issues": self.report.environment_issues,
            "performance_warnings": self.report.performance_warnings,
            "recommendations": self.report.recommendations,
            "generated_at": time.time(),
        }

        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info("report_saved", filename=filename)
        return filename

    def print_summary(self) -> None:
        """Print a human-readable summary of the profiling results."""
        print("\n" + "=" * 80)
        print("🐳 DOCKER ENVIRONMENT PROFILING REPORT")
        print("=" * 80)

        print("\n📊 Container Information:")
        for key, value in self.report.container_info.items():
            print(f"  {key}: {value}")

        if self.report.environment_issues:
            print("\n⚠️  Environment Issues:")
            for issue in self.report.environment_issues:
                print(f"  ❌ {issue}")

        if self.report.performance_warnings:
            print("\n🚨 Performance Warnings:")
            for warning in self.report.performance_warnings:
                print(f"  ⚠️  {warning}")

        if self.report.recommendations:
            print("\n💡 Recommendations:")
            for rec in self.report.recommendations:
                print(f"  💡 {rec}")

        print(f"\n📈 Resource samples collected: {len(self.report.resource_history)}")
        print(f"🌐 Network tests performed: {len(self.report.network_tests)}")
        print("=" * 80)


async def main():
    """Main profiling function."""
    profiler = DockerProfiler()

    print("🔍 Starting Docker environment profiling...")
    print("This will monitor resources and test connectivity for 5 minutes.")
    print("Press Ctrl+C to stop early.\n")

    try:
        await profiler.run_comprehensive_profile(duration_seconds=300)
        profiler.print_summary()

        print(
            "\n✅ Profiling completed! Check the generated JSON report for detailed data."
        )
    except KeyboardInterrupt:
        print("\n⚠️  Profiling interrupted by user")
        profiler.print_summary()
    except Exception as e:
        logger.error("profiling_failed", error=str(e))
        print(f"❌ Profiling failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
