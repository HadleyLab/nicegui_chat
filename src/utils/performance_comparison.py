"""Performance comparison utilities for before/after optimization analysis.

This module provides comprehensive tools for comparing performance metrics
before and after optimizations, including:
- Statistical significance testing
- Performance regression detection
- Improvement quantification
- Visual comparison generation
- Automated performance validation
- Trend analysis and reporting

The utilities help validate that optimizations provide meaningful improvements
while ensuring no performance regressions occur.
"""

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

try:
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

logger = structlog.get_logger()


@dataclass
class PerformanceComparison:
    """Results of a performance comparison analysis."""

    metric_name: str
    before_values: List[float]
    after_values: List[float]

    # Statistical measures
    before_mean: float = 0.0
    after_mean: float = 0.0
    before_std: float = 0.0
    after_std: float = 0.0

    # Improvement metrics
    improvement_percent: float = 0.0
    is_significant: bool = False
    confidence_level: float = 0.0

    # Regression detection
    is_regression: bool = False
    regression_severity: str = "none"  # none, minor, moderate, severe

    def calculate_statistics(self) -> None:
        """Calculate statistical measures."""
        if not self.before_values or not self.after_values:
            return

        self.before_mean = statistics.mean(self.before_values)
        self.after_mean = statistics.mean(self.after_values)
        self.before_std = (
            statistics.stdev(self.before_values) if len(self.before_values) > 1 else 0.0
        )
        self.after_std = (
            statistics.stdev(self.after_values) if len(self.after_values) > 1 else 0.0
        )

        # Calculate improvement percentage
        if self.before_mean > 0:
            self.improvement_percent = (
                (self.after_mean - self.before_mean) / self.before_mean
            ) * 100

        # Determine if improvement is significant using t-test approximation
        self.is_significant = self._calculate_significance()

        # Check for regression (worse performance)
        self.is_regression = self.after_mean > self.before_mean

        # Classify regression severity
        if self.is_regression:
            degradation_percent = abs(self.improvement_percent)
            if degradation_percent > 20:
                self.regression_severity = "severe"
            elif degradation_percent > 10:
                self.regression_severity = "moderate"
            elif degradation_percent > 5:
                self.regression_severity = "minor"
            else:
                self.regression_severity = "none"
        else:
            self.regression_severity = "none"

    def _calculate_significance(self, alpha: float = 0.05) -> bool:
        """Calculate if the difference is statistically significant."""
        if len(self.before_values) < 2 or len(self.after_values) < 2:
            return False

        # Simple t-test approximation for two samples
        n1, n2 = len(self.before_values), len(self.after_values)
        var1, var2 = self.before_std**2, self.after_std**2

        # Pooled standard error
        pooled_se = ((var1 / n1) + (var2 / n2)) ** 0.5

        if pooled_se == 0:
            return False

        # T-statistic
        t_stat = (self.after_mean - self.before_mean) / pooled_se

        # Degrees of freedom
        df = n1 + n2 - 2

        # Critical t-value (approximation)
        # For simplicity, using common values for 95% confidence
        critical_t = {10: 2.23, 20: 2.09, 30: 2.04, 50: 2.01, 100: 1.98}.get(df, 1.96)

        return abs(t_stat) > critical_t


@dataclass
class ComparisonReport:
    """Comprehensive performance comparison report."""

    baseline_name: str
    optimized_name: str
    timestamp: float = field(default_factory=time.time)

    # Overall assessment
    total_metrics: int = 0
    improved_metrics: int = 0
    regressed_metrics: int = 0
    unchanged_metrics: int = 0

    # Detailed comparisons
    comparisons: List[PerformanceComparison] = field(default_factory=list)

    # Summary statistics
    avg_improvement_percent: float = 0.0
    significant_improvements: int = 0
    severe_regressions: int = 0

    def generate_summary(self) -> str:
        """Generate a human-readable summary."""
        return f"""
# Performance Comparison Report

## Overview
- **Baseline**: {self.baseline_name}
- **Optimized**: {self.optimized_name}
- **Comparison Date**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}

## Results Summary
- **Total Metrics**: {self.total_metrics}
- **Improved**: {self.improved_metrics} ({self.improved_metrics/self.total_metrics*100:.1f}%)
- **Regressed**: {self.regressed_metrics} ({self.regressed_metrics/self.total_metrics*100:.1f}%)
- **Unchanged**: {self.unchanged_metrics} ({self.unchanged_metrics/self.total_metrics*100:.1f}%)

## Key Findings
- **Average Improvement**: {self.avg_improvement_percent:+.2f}%
- **Significant Improvements**: {self.significant_improvements}
- **Severe Regressions**: {self.severe_regressions}

## Assessment
{self._generate_assessment()}
"""

    def _generate_assessment(self) -> str:
        """Generate performance assessment."""
        if self.severe_regressions > 0:
            return "⚠️  WARNING: Severe performance regressions detected!"
        elif self.improved_metrics > self.regressed_metrics:
            return "✅ Overall performance improvement detected."
        elif self.regressed_metrics > self.improved_metrics:
            return "⚠️  Performance degradation detected."
        else:
            return "➖ No significant performance changes detected."


class PerformanceComparator:
    """Main class for comparing performance data."""

    def __init__(self):
        self.output_dir = Path("performance_comparison_results")
        self.output_dir.mkdir(exist_ok=True)

    def load_benchmark_results(
        self, baseline_file: Path, optimized_file: Path
    ) -> Tuple[Dict, Dict]:
        """Load benchmark results from JSON files."""
        # Load baseline results
        with open(baseline_file, "r") as f:
            baseline_data = json.load(f)

        # Load optimized results
        with open(optimized_file, "r") as f:
            optimized_data = json.load(f)

        return baseline_data, optimized_data

    def extract_metrics(self, data: Dict) -> Dict[str, List[float]]:
        """Extract performance metrics from benchmark data."""
        metrics = {}

        # Handle different data formats
        if "metrics" in data:
            # Format from performance benchmarks
            for metric in data["metrics"]:
                for key, value in metric.items():
                    if isinstance(value, (int, float)) and key.endswith(
                        ("_ms", "_mb", "_tps", "_percent")
                    ):
                        if key not in metrics:
                            metrics[key] = []
                        metrics[key].append(float(value))

        elif "summary" in data and "metrics" in data["summary"]:
            # Format from load testing
            summary_metrics = data["summary"]["metrics"]
            for key, value in summary_metrics.items():
                if isinstance(value, (int, float)):
                    metrics[key] = [float(value)]

        return metrics

    def compare_benchmark_runs(
        self,
        baseline_file: Path,
        optimized_file: Path,
        output_file: Optional[Path] = None,
    ) -> ComparisonReport:
        """Compare two benchmark runs and generate report."""
        logger.info(
            "Comparing benchmark runs",
            baseline=str(baseline_file),
            optimized=str(optimized_file),
        )

        # Load data
        baseline_data, optimized_data = self.load_benchmark_results(
            baseline_file, optimized_file
        )

        # Extract metrics
        baseline_metrics = self.extract_metrics(baseline_data)
        optimized_metrics = self.extract_metrics(optimized_data)

        # Find common metrics
        common_metrics = set(baseline_metrics.keys()) & set(optimized_metrics.keys())

        if not common_metrics:
            raise ValueError(
                "No common metrics found between baseline and optimized results"
            )

        # Create comparisons
        comparisons = []
        for metric_name in common_metrics:
            comparison = PerformanceComparison(
                metric_name=metric_name,
                before_values=baseline_metrics[metric_name],
                after_values=optimized_metrics[metric_name],
            )
            comparison.calculate_statistics()
            comparisons.append(comparison)

        # Generate report
        baseline_name = baseline_file.stem
        optimized_name = optimized_file.stem

        report = ComparisonReport(
            baseline_name=baseline_name,
            optimized_name=optimized_name,
            comparisons=comparisons,
        )

        # Calculate summary statistics
        report.total_metrics = len(comparisons)
        report.improved_metrics = sum(
            1 for c in comparisons if not c.is_regression and c.improvement_percent > 0
        )
        report.regressed_metrics = sum(1 for c in comparisons if c.is_regression)
        report.unchanged_metrics = (
            report.total_metrics - report.improved_metrics - report.regressed_metrics
        )

        # Calculate average improvement
        improvements = [
            c.improvement_percent for c in comparisons if not c.is_regression
        ]
        report.avg_improvement_percent = (
            statistics.mean(improvements) if improvements else 0.0
        )

        # Count significant improvements and severe regressions
        report.significant_improvements = sum(
            1 for c in comparisons if c.is_significant and not c.is_regression
        )
        report.severe_regressions = sum(
            1 for c in comparisons if c.regression_severity == "severe"
        )

        # Save report if requested
        if output_file:
            self.save_comparison_report(report, output_file)

        logger.info(
            "Comparison completed",
            total_metrics=report.total_metrics,
            improved=report.improved_metrics,
            regressed=report.regressed_metrics,
        )

        return report

    def save_comparison_report(self, report: ComparisonReport, filepath: Path) -> None:
        """Save comparison report to JSON file."""
        # Convert to serializable format
        data = {
            "baseline_name": report.baseline_name,
            "optimized_name": report.optimized_name,
            "timestamp": report.timestamp,
            "summary": {
                "total_metrics": report.total_metrics,
                "improved_metrics": report.improved_metrics,
                "regressed_metrics": report.regressed_metrics,
                "unchanged_metrics": report.unchanged_metrics,
                "avg_improvement_percent": report.avg_improvement_percent,
                "significant_improvements": report.significant_improvements,
                "severe_regressions": report.severe_regressions,
            },
            "comparisons": [
                {
                    "metric_name": c.metric_name,
                    "before_mean": c.before_mean,
                    "after_mean": c.after_mean,
                    "improvement_percent": c.improvement_percent,
                    "is_significant": c.is_significant,
                    "is_regression": c.is_regression,
                    "regression_severity": c.regression_severity,
                }
                for c in report.comparisons
            ],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Comparison report saved", filepath=str(filepath))

    def generate_visual_comparison(
        self, report: ComparisonReport, output_dir: Path
    ) -> None:
        """Generate visual comparison charts."""
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualization libraries not available, skipping charts")
            return

        output_dir.mkdir(exist_ok=True)

        # Set up the plotting style
        plt.style.use("seaborn-v0_8")
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(
            f"Performance Comparison: {report.baseline_name} vs {report.optimized_name}",
            fontsize=16,
        )

        # Flatten axes for easier indexing
        axes = axes.flatten()

        # 1. Improvement percentages bar chart
        self._plot_improvement_bars(report, axes[0])

        # 2. Before/after comparison scatter plot
        self._plot_before_after_scatter(report, axes[1])

        # 3. Response time distributions
        self._plot_response_time_distributions(report, axes[2])

        # 4. Memory usage comparison
        self._plot_memory_usage_comparison(report, axes[3])

        plt.tight_layout()
        plt.savefig(
            output_dir / "performance_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

        logger.info("Visual comparison generated", output_dir=str(output_dir))

    def _plot_improvement_bars(self, report: ComparisonReport, ax) -> None:
        """Plot improvement percentages as bars."""
        metrics = [c.metric_name for c in report.comparisons]
        improvements = [c.improvement_percent for c in report.comparisons]

        colors = [
            "green" if x < 0 else "red" if x > 0 else "gray" for x in improvements
        ]

        bars = ax.bar(range(len(metrics)), improvements, color=colors, alpha=0.7)
        ax.axhline(y=0, color="black", linestyle="-", alpha=0.3)
        ax.set_xlabel("Metrics")
        ax.set_ylabel("Improvement (%)")
        ax.set_title("Performance Improvement by Metric")
        ax.set_xticks(range(len(metrics)))
        ax.set_xticklabels(metrics, rotation=45, ha="right")

        # Add value labels on bars
        for bar, improvement in zip(bars, improvements):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{improvement:+.1f}%",
                ha="center",
                va="bottom" if height >= 0 else "top",
            )

    def _plot_before_after_scatter(self, report: ComparisonReport, ax) -> None:
        """Plot before vs after performance scatter plot."""
        before_vals = []
        after_vals = []
        colors = []
        labels = []

        for comp in report.comparisons:
            if comp.before_mean > 0 and comp.after_mean > 0:
                before_vals.append(comp.before_mean)
                after_vals.append(comp.after_mean)
                colors.append("green" if not comp.is_regression else "red")
                labels.append(comp.metric_name)

        if before_vals and after_vals:
            scatter = ax.scatter(before_vals, after_vals, c=colors, alpha=0.7, s=100)

            # Add diagonal line (no change)
            min_val = min(min(before_vals), min(after_vals))
            max_val = max(max(before_vals), max(after_vals))
            ax.plot(
                [min_val, max_val],
                [min_val, max_val],
                "k--",
                alpha=0.5,
                label="No Change",
            )

            ax.set_xlabel("Baseline Performance")
            ax.set_ylabel("Optimized Performance")
            ax.set_title("Before vs After Performance")
            ax.legend()

            # Add metric labels for significant changes
            for i, label in enumerate(labels):
                if (
                    abs(report.comparisons[i].improvement_percent) > 10
                ):  # Significant change
                    ax.annotate(
                        label,
                        (before_vals[i], after_vals[i]),
                        xytext=(5, 5),
                        textcoords="offset points",
                        fontsize=8,
                    )

    def _plot_response_time_distributions(self, report: ComparisonReport, ax) -> None:
        """Plot response time distribution comparison."""
        before_times = []
        after_times = []

        for comp in report.comparisons:
            if (
                "response_time" in comp.metric_name.lower()
                or "duration" in comp.metric_name.lower()
            ):
                before_times.extend(comp.before_values)
                after_times.extend(comp.after_values)

        if before_times and after_times:
            ax.hist(before_times, alpha=0.7, label="Baseline", bins=30, density=True)
            ax.hist(after_times, alpha=0.7, label="Optimized", bins=30, density=True)
            ax.set_xlabel("Response Time (ms)")
            ax.set_ylabel("Density")
            ax.set_title("Response Time Distribution")
            ax.legend()

    def _plot_memory_usage_comparison(self, report: ComparisonReport, ax) -> None:
        """Plot memory usage comparison."""
        memory_metrics = []

        for comp in report.comparisons:
            if "memory" in comp.metric_name.lower():
                memory_metrics.append(
                    (comp.metric_name, comp.before_mean, comp.after_mean)
                )

        if memory_metrics:
            metrics = [m[0] for m in memory_metrics]
            before_vals = [m[1] for m in memory_metrics]
            after_vals = [m[2] for m in memory_metrics]

            x = range(len(metrics))
            ax.bar([i - 0.2 for i in x], before_vals, 0.4, label="Baseline", alpha=0.7)
            ax.bar([i + 0.2 for i in x], after_vals, 0.4, label="Optimized", alpha=0.7)

            ax.set_xlabel("Memory Metrics")
            ax.set_ylabel("Memory Usage (MB)")
            ax.set_title("Memory Usage Comparison")
            ax.set_xticks(x)
            ax.set_xticklabels(metrics, rotation=45, ha="right")
            ax.legend()


class AutomatedPerformanceValidator:
    """Automated validation of performance improvements."""

    def __init__(self, comparator: PerformanceComparator):
        self.comparator = comparator

    def validate_optimization(
        self,
        baseline_file: Path,
        optimized_file: Path,
        requirements: Dict[str, float],
    ) -> Dict[str, Any]:
        """Validate that optimizations meet specified requirements."""
        report = self.comparator.compare_benchmark_runs(baseline_file, optimized_file)

        validation_results = {
            "optimization_valid": True,
            "met_requirements": [],
            "failed_requirements": [],
            "warnings": [],
        }

        # Check each requirement
        for metric_pattern, required_improvement in requirements.items():
            matching_comparisons = [
                c
                for c in report.comparisons
                if metric_pattern.lower() in c.metric_name.lower()
            ]

            if not matching_comparisons:
                validation_results["warnings"].append(
                    f"No metrics found matching: {metric_pattern}"
                )
                continue

            # Check if any matching metric meets the requirement
            requirement_met = False
            for comp in matching_comparisons:
                if (
                    not comp.is_regression
                    and comp.improvement_percent >= required_improvement
                ):
                    requirement_met = True
                    validation_results["met_requirements"].append(
                        {
                            "metric": comp.metric_name,
                            "improvement": comp.improvement_percent,
                            "required": required_improvement,
                        }
                    )
                    break

            if not requirement_met:
                validation_results["optimization_valid"] = False
                validation_results["failed_requirements"].append(
                    {
                        "metric_pattern": metric_pattern,
                        "required_improvement": required_improvement,
                        "best_improvement": max(
                            (
                                c.improvement_percent
                                for c in matching_comparisons
                                if not c.is_regression
                            ),
                            default=0.0,
                        ),
                    }
                )

        # Check for severe regressions
        severe_regressions = [
            c for c in report.comparisons if c.regression_severity == "severe"
        ]
        if severe_regressions:
            validation_results["optimization_valid"] = False
            validation_results["warnings"].append(
                f"Severe regressions detected in: {[c.metric_name for c in severe_regressions]}"
            )

        return validation_results


# Example usage and testing functions
def compare_benchmark_runs_example():
    """Example of comparing two benchmark runs."""
    comparator = PerformanceComparator()

    # Example file paths (would be actual benchmark result files)
    baseline_file = Path("benchmark_results/baseline_1234567890.json")
    optimized_file = Path("benchmark_results/optimized_1234567990.json")

    if baseline_file.exists() and optimized_file.exists():
        report = comparator.compare_benchmark_runs(baseline_file, optimized_file)

        print(report.generate_summary())

        # Generate visual comparison
        comparator.generate_visual_comparison(
            report, Path("performance_comparison_results")
        )

        return report
    else:
        print("Benchmark files not found, skipping comparison")
        return None


def validate_performance_requirements():
    """Example of validating performance requirements."""
    comparator = PerformanceComparator()
    validator = AutomatedPerformanceValidator(comparator)

    # Define performance requirements
    requirements = {
        "response_time": -15.0,  # 15% improvement required
        "memory": -10.0,  # 10% memory reduction required
        "throughput": 20.0,  # 20% throughput increase required
    }

    baseline_file = Path("benchmark_results/baseline_1234567890.json")
    optimized_file = Path("benchmark_results/optimized_1234567990.json")

    if baseline_file.exists() and optimized_file.exists():
        validation = validator.validate_optimization(
            baseline_file, optimized_file, requirements
        )

        print("Performance Validation Results:")
        print(f"Valid: {validation['optimization_valid']}")
        print(f"Met Requirements: {len(validation['met_requirements'])}")
        print(f"Failed Requirements: {len(validation['failed_requirements'])}")

        if validation["warnings"]:
            print("Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")

        return validation
    else:
        print("Benchmark files not found, skipping validation")
        return None


if __name__ == "__main__":
    # Run example comparisons when executed directly
    print("Running performance comparison examples...")

    report = compare_benchmark_runs_example()
    validation = validate_performance_requirements()

    print("Performance comparison examples completed!")
