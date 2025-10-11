#!/usr/bin/env python3
"""
Comprehensive Performance Validation Runner for nicegui_chat

This script orchestrates the complete performance validation suite including:
- Performance benchmarking
- Load testing
- Memory profiling
- Streaming validation
- Regression testing
- Docker performance validation
- Async integration testing

Usage:
    python run_performance_validation.py [options]

Options:
    --quick         Run quick validation (5-10 minutes)
    --full          Run full validation suite (30-60 minutes)
    --baseline      Create baseline performance data
    --compare       Compare against baseline
    --docker        Include Docker performance tests
    --memory        Run memory profiling
    --streaming     Run streaming performance tests
    --regression    Run regression tests
    --all           Run all validation tests
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

import structlog

# Configure logging
logger = structlog.get_logger()


class PerformanceValidationRunner:
    """Main orchestrator for performance validation."""

    def __init__(self):
        self.results_dir = Path("validation_results")
        self.results_dir.mkdir(exist_ok=True)
        self.start_time = time.time()

    async def run_quick_validation(self) -> Dict[str, Any]:
        """Run quick validation suite (5-10 minutes)."""
        logger.info("Starting quick validation suite")

        results = {
            "validation_type": "quick",
            "start_time": self.start_time,
            "tests_run": [],
            "summary": {},
        }

        try:
            # Run basic performance benchmarks
            logger.info("Running basic performance benchmarks")
            from tests.test_performance_benchmarks import PerformanceBenchmarkSuite

            suite = PerformanceBenchmarkSuite()

            # Quick chat benchmark
            await suite.benchmark_chat_response(
                name="quick_chat_benchmark",
                messages=["Hello", "Test message"],
                iterations=3,
            )

            results["tests_run"].append("performance_benchmarks")
            results["performance_results"] = {
                name: result.to_dict() for name, result in suite.results.items()
            }

            # Run basic regression tests
            logger.info("Running basic regression tests")
            from tests.test_regression_suite import create_regression_test_suite

            suite = create_regression_test_suite()
            regression_results = await suite.run_all_tests(performance_monitoring=False)

            results["tests_run"].append("regression_tests")
            results["regression_results"] = {
                name: result.to_dict() for name, result in regression_results.items()
            }

            # Calculate summary
            total_tests = len(suite.results)
            passed_tests = sum(1 for r in suite.results.values() if r.success)
            results["summary"] = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (
                    passed_tests / total_tests * 100 if total_tests > 0 else 0
                ),
                "duration": time.time() - self.start_time,
            }

        except Exception as e:
            logger.error("Quick validation failed", error=str(e))
            results["error"] = str(e)

        return results

    async def run_full_validation(self) -> Dict[str, Any]:
        """Run full validation suite (30-60 minutes)."""
        logger.info("Starting full validation suite")

        results = {
            "validation_type": "full",
            "start_time": self.start_time,
            "tests_run": [],
            "summary": {},
        }

        try:
            # Run comprehensive performance benchmarks
            logger.info("Running comprehensive performance benchmarks")
            from tests.test_performance_benchmarks import PerformanceBenchmarkSuite

            suite = PerformanceBenchmarkSuite()

            # Multiple benchmark scenarios
            await suite.benchmark_chat_response(
                name="full_chat_benchmark",
                messages=[
                    "Hello",
                    "How are you?",
                    "This is a longer test message for comprehensive validation",
                ],
                iterations=10,
            )

            await suite.benchmark_memory_operations(
                name="full_memory_benchmark",
                operations=100,
            )

            await suite.benchmark_concurrent_load(
                name="full_concurrent_benchmark",
                concurrent_users=10,
                messages_per_user=5,
            )

            results["tests_run"].append("performance_benchmarks")
            results["performance_results"] = {
                name: result.to_dict() for name, result in suite.results.items()
            }

            # Run load testing
            logger.info("Running load testing")
            from tests.test_load_framework import (
                PREDEFINED_SCENARIOS,
                LoadTestFramework,
            )

            framework = LoadTestFramework()
            scenario = PREDEFINED_SCENARIOS[0]  # Use light load for full validation
            scenario.duration_seconds = 300  # 5 minutes

            load_results = await framework.run_load_test(scenario)
            results["tests_run"].append("load_testing")
            results["load_results"] = {
                "scenario": scenario.name,
                "metrics": {
                    "total_requests": load_results.total_requests,
                    "success_rate": load_results.success_rate,
                    "avg_response_time": load_results.avg_response_time,
                    "requests_per_second": load_results.requests_per_second,
                },
            }

            # Run memory profiling
            logger.info("Running memory profiling")
            from src.utils.memory_profiler import MemoryProfiler

            profiler = MemoryProfiler(sampling_interval=2.0, max_snapshots=150)
            await profiler.start_profiling()
            await asyncio.sleep(60)  # Profile for 1 minute
            await profiler.stop_profiling()

            memory_report = profiler.get_memory_report()
            leak_analysis = profiler.detect_memory_leaks()

            results["tests_run"].append("memory_profiling")
            results["memory_results"] = {
                "report": memory_report,
                "leak_analysis": {
                    "has_leak": leak_analysis.has_leak,
                    "growth_rate_mb_per_hour": leak_analysis.growth_rate_mb_per_hour,
                    "confidence_score": leak_analysis.confidence_score,
                },
            }

            # Run streaming performance tests
            logger.info("Running streaming performance tests")
            from tests.test_streaming_performance import StreamingPerformanceTester

            tester = StreamingPerformanceTester()

            await tester.test_streaming_performance(
                test_name="full_streaming_test",
                messages=["Streaming performance test message"],
                iterations=5,
            )

            results["tests_run"].append("streaming_performance")
            results["streaming_results"] = {
                name: result.to_dict() for name, result in tester.results.items()
            }

            # Run regression tests
            logger.info("Running regression tests")
            from tests.test_regression_suite import create_regression_test_suite

            suite = create_regression_test_suite()
            regression_results = await suite.run_all_tests(performance_monitoring=True)

            results["tests_run"].append("regression_tests")
            results["regression_results"] = {
                name: result.to_dict() for name, result in regression_results.items()
            }

            # Run async integration tests
            logger.info("Running async integration tests")
            from tests.test_async_integration import AsyncIntegrationTester

            tester = AsyncIntegrationTester()
            async_results = await tester.run_comprehensive_async_integration_test()

            results["tests_run"].append("async_integration")
            results["async_results"] = {
                name: result.to_dict() for name, result in async_results.items()
            }

            # Calculate comprehensive summary
            total_tests = sum(
                len(suite.results) if hasattr(suite, "results") else 0
                for suite in [suite]  # Only regression tests for now
            )
            passed_tests = sum(
                sum(1 for r in test_results.values() if r.get("success", False))
                for test_results in [regression_results, async_results]
                if isinstance(test_results, dict)
            )

            results["summary"] = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (
                    passed_tests / total_tests * 100 if total_tests > 0 else 0
                ),
                "duration": time.time() - self.start_time,
                "tests_executed": results["tests_run"],
            }

        except Exception as e:
            logger.error("Full validation failed", error=str(e))
            results["error"] = str(e)

        return results

    async def run_docker_validation(self) -> Dict[str, Any]:
        """Run Docker-specific performance validation."""
        logger.info("Starting Docker validation")

        results = {
            "validation_type": "docker",
            "start_time": time.time(),
            "tests_run": [],
        }

        try:
            from tests.test_docker_performance import DockerPerformanceTester

            tester = DockerPerformanceTester()

            # Validate Docker environment
            env_validation = await tester.validate_docker_environment()
            results["docker_environment"] = env_validation

            if not env_validation.get("docker_available"):
                results["error"] = "Docker not available"
                return results

            # Build test container
            if not await tester.build_test_containers():
                results["error"] = "Failed to build test container"
                return results

            # Run Docker performance test
            from tests.test_docker_performance import DOCKER_TEST_SCENARIOS

            scenario = DOCKER_TEST_SCENARIOS[0]  # Basic scenario
            docker_results = await tester.run_container_performance_test(scenario)

            results["tests_run"].append("docker_performance")
            results["docker_results"] = docker_results

            # Generate report
            report = tester.generate_docker_performance_report(docker_results)
            results["docker_report"] = report

            results["summary"] = {
                "duration": time.time() - results["start_time"],
                "docker_available": True,
                "tests_executed": results["tests_run"],
            }

        except Exception as e:
            logger.error("Docker validation failed", error=str(e))
            results["error"] = str(e)

        return results

    def save_results(self, results: Dict[str, Any]) -> Path:
        """Save validation results to file."""
        timestamp = int(time.time())
        filename = self.results_dir / f"validation_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Validation results saved", filename=str(filename))
        return filename

    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary report."""
        if "error" in results:
            return f"Validation failed: {results['error']}"

        summary = results.get("summary", {})
        report = f"""
# Performance Validation Summary

## Validation Overview
- **Type**: {results.get('validation_type', 'Unknown')}
- **Duration**: {summary.get('duration', 0):.2f} seconds
- **Start Time**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results.get('start_time', 0)))}

## Test Results

"""

        if "performance_results" in results:
            report += "### Performance Benchmarks\n"
            for name, result in results["performance_results"].items():
                avg_response = result.get("avg_response_time_ms", 0)
                avg_memory = result.get("avg_memory_usage_mb", 0)
                report += f"- **{name}**: {avg_response:.0f}ms, {avg_memory:.1f}MB\n"

        if "load_results" in results:
            report += "\n### Load Testing\n"
            load = results["load_results"]
            report += f"- **Success Rate**: {load.get('success_rate', 0):.1f}%\n"
            report += (
                f"- **Avg Response Time**: {load.get('avg_response_time', 0):.0f}ms\n"
            )
            report += (
                f"- **Requests/Second**: {load.get('requests_per_second', 0):.2f}\n"
            )

        if "memory_results" in results:
            report += "\n### Memory Profiling\n"
            memory = results["memory_results"]
            leak = memory.get("leak_analysis", {})
            report += f"- **Memory Growth**: {leak.get('growth_rate_mb_per_hour', 0):.2f} MB/hour\n"
            report += f"- **Leak Detected**: {leak.get('has_leak', False)}\n"

        if "regression_results" in results:
            report += "\n### Regression Tests\n"
            regression = results["regression_results"]
            passed = sum(1 for r in regression.values() if r.get("success", False))
            total = len(regression)
            report += (
                f"- **Tests Passed**: {passed}/{total} ({passed/total*100:.1f}%)\n"
            )

        if "docker_results" in results:
            report += "\n### Docker Performance\n"
            docker = results["docker_results"]
            perf_summary = docker.get("performance_summary", {})
            report += f"- **Avg CPU Usage**: {perf_summary.get('cpu_usage_avg_percent', 0):.1f}%\n"
            report += f"- **Avg Memory Usage**: {perf_summary.get('memory_usage_avg_mb', 0):.1f} MB\n"

        # Overall assessment
        report += "\n## Assessment\n"
        success_rate = summary.get("success_rate", 0)

        if success_rate >= 90:
            report += (
                "✅ **EXCELLENT**: All validation tests passed with high success rate\n"
            )
        elif success_rate >= 75:
            report += "✅ **GOOD**: Most validation tests passed\n"
        elif success_rate >= 50:
            report += "⚠️ **FAIR**: Some tests failed, review required\n"
        else:
            report += "❌ **POOR**: MAny tests failed, significant issues detected\n"

        return report


async def main():
    """Main validation runner."""
    parser = argparse.ArgumentParser(description="Run performance validation suite")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick validation (5-10 minutes)"
    )
    parser.add_argument(
        "--full", action="store_true", help="Run full validation suite (30-60 minutes)"
    )
    parser.add_argument(
        "--docker", action="store_true", help="Include Docker performance tests"
    )
    parser.add_argument(
        "--baseline", action="store_true", help="Create baseline performance data"
    )
    parser.add_argument("--compare", type=str, help="Compare against baseline file")
    parser.add_argument("--output", type=str, help="Output file for results")

    args = parser.parse_args()

    # Determine validation type
    if args.quick:
        validation_type = "quick"
    elif args.full:
        validation_type = "full"
    else:
        # Default to quick if no type specified
        validation_type = "quick"

    runner = PerformanceValidationRunner()

    try:
        if validation_type == "quick":
            results = await runner.run_quick_validation()
        elif validation_type == "full":
            results = await runner.run_full_validation()
        else:
            results = {"error": f"Unknown validation type: {validation_type}"}

        # Add Docker validation if requested
        if args.docker and "error" not in results:
            docker_results = await runner.run_docker_validation()
            results["docker_validation"] = docker_results

        # Save results
        output_file = runner.save_results(results)

        # Generate and display summary
        summary = runner.generate_summary_report(results)
        print(summary)

        # Save summary to file
        summary_file = output_file.with_suffix(".txt")
        with open(summary_file, "w") as f:
            f.write(summary)

        print(f"\nDetailed results saved to: {output_file}")
        print(f"Summary report saved to: {summary_file}")

        # Compare against baseline if requested
        if args.compare and "error" not in results:
            try:
                from src.utils.performance_comparison import PerformanceComparator

                comparator = PerformanceComparator()
                comparison_report = comparator.compare_benchmark_runs(
                    Path(args.compare),
                    output_file,
                )

                print("\n" + "=" * 50)
                print("COMPARISON AGAINST BASELINE")
                print("=" * 50)
                print(comparison_report.generate_summary())

            except Exception as e:
                print(f"Failed to compare against baseline: {e}")

        # Exit with appropriate code
        if "error" in results or (
            results.get("summary", {}).get("success_rate", 100) < 50
        ):
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Validation runner failed", error=str(e))
        print(f"Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run validation suite
    asyncio.run(main())
