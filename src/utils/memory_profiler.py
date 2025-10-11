"""Memory profiling tools for nicegui_chat optimization validation.

This module provides comprehensive memory profiling capabilities including:
- Memory usage pattern analysis
- Memory leak detection
- Object allocation tracking
- Garbage collection monitoring
- Memory growth trend analysis
- Performance impact assessment

The profiler integrates with the existing async architecture and provides
detailed insights into memory behavior under various load conditions.
"""

import asyncio
import gc
import time
import tracemalloc
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil
import structlog

logger = structlog.get_logger()


@dataclass
class MemorySnapshot:
    """Snapshot of memory state at a specific point in time."""

    timestamp: float
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    objects_count: int
    gc_collections: Dict[str, int]
    top_allocations: List[Tuple[str, float]] = field(
        default_factory=list
    )  # (filename:line, size_mb)

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "rss_mb": self.rss_mb,
            "vms_mb": self.vms_mb,
            "objects_count": self.objects_count,
            "gc_collections": self.gc_collections,
            "top_allocations": self.top_allocations,
        }


@dataclass
class MemoryGrowthPoint:
    """Point representing memory growth over time."""

    timestamp: float
    memory_mb: float
    operation_count: int
    growth_rate_mb_per_sec: float = 0.0
    is_baseline: bool = False


@dataclass
class MemoryLeakAnalysis:
    """Results of memory leak analysis."""

    has_leak: bool
    growth_rate_mb_per_hour: float
    confidence_score: float  # 0-1, higher = more confident
    problematic_areas: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class MemoryProfiler:
    """Comprehensive memory profiler for async applications."""

    def __init__(
        self,
        sampling_interval: float = 1.0,
        max_snapshots: int = 1000,
        enable_tracemalloc: bool = True,
    ):
        self.sampling_interval = sampling_interval
        self.max_snapshots = max_snapshots
        self.enable_tracemalloc = enable_tracemalloc

        # Memory tracking
        self.snapshots: deque[MemorySnapshot] = deque(maxlen=max_snapshots)
        self.baseline_snapshot: Optional[MemorySnapshot] = None
        self.is_profiling = False
        self.profile_task: Optional[asyncio.Task] = None

        # Process reference
        self.process = psutil.Process()

        # Tracemalloc state
        self.tracemalloc_enabled = False

    async def start_profiling(self) -> None:
        """Start memory profiling."""
        if self.is_profiling:
            logger.warning("Memory profiling already running")
            return

        self.is_profiling = True

        # Enable tracemalloc if requested
        if self.enable_tracemalloc:
            tracemalloc.start()
            self.tracemalloc_enabled = True

        # Take baseline snapshot
        self.baseline_snapshot = await self._take_snapshot()
        logger.info(
            "Memory profiling started", baseline_mb=self.baseline_snapshot.rss_mb
        )

        # Start continuous profiling
        self.profile_task = asyncio.create_task(self._profile_loop())

    async def stop_profiling(self) -> None:
        """Stop memory profiling and return results."""
        if not self.is_profiling:
            return

        self.is_profiling = False

        if self.profile_task:
            self.profile_task.cancel()
            try:
                await self.profile_task
            except asyncio.CancelledError:
                pass

        # Stop tracemalloc
        if self.tracemalloc_enabled:
            tracemalloc.stop()
            self.tracemalloc_enabled = False

        logger.info("Memory profiling stopped", snapshots=len(self.snapshots))

    async def _take_snapshot(self) -> MemorySnapshot:
        """Take a comprehensive memory snapshot."""
        timestamp = time.time()

        # Get memory info
        memory_info = self.process.memory_info()
        rss_mb = memory_info.rss / 1024 / 1024
        vms_mb = memory_info.vms / 1024 / 1024

        # Count objects
        objects_count = len(gc.get_objects())

        # Get GC collection stats
        gc_collections = {}
        for i in range(3):  # GC generations 0, 1, 2
            gc_collections[f"gen{i}"] = gc.get_count()[i]

        # Get top allocations if tracemalloc is enabled
        top_allocations = []
        if self.tracemalloc_enabled:
            try:
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics("traceback")

                for stat in top_stats[:10]:  # Top 10 allocations
                    for line in stat.traceback.format()[:1]:  # First line only
                        if "site-packages" not in line and "stdlib" not in line:
                            top_allocations.append(
                                (line.strip(), stat.size / 1024 / 1024)
                            )
                            break
            except Exception as e:
                logger.warning("Failed to get allocation stats", error=str(e))

        return MemorySnapshot(
            timestamp=timestamp,
            rss_mb=rss_mb,
            vms_mb=vms_mb,
            objects_count=objects_count,
            gc_collections=gc_collections,
            top_allocations=top_allocations,
        )

    async def _profile_loop(self) -> None:
        """Main profiling loop."""
        while self.is_profiling:
            try:
                snapshot = await self._take_snapshot()
                self.snapshots.append(snapshot)

                # Brief pause between samples
                await asyncio.sleep(self.sampling_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in profiling loop", error=str(e))
                await asyncio.sleep(self.sampling_interval)

    def get_memory_growth_trend(self) -> List[MemoryGrowthPoint]:
        """Analyze memory growth trend over time."""
        if len(self.snapshots) < 2:
            return []

        growth_points = []

        for i, snapshot in enumerate(self.snapshots):
            # Calculate time since start
            elapsed_time = snapshot.timestamp - self.snapshots[0].timestamp

            # Calculate memory since baseline
            baseline_mb = (
                self.baseline_snapshot.rss_mb
                if self.baseline_snapshot
                else snapshot.rss_mb
            )
            memory_mb = snapshot.rss_mb - baseline_mb

            # Calculate growth rate (simplified)
            growth_rate = 0.0
            if i > 0:
                prev_snapshot = self.snapshots[i - 1]
                time_diff = snapshot.timestamp - prev_snapshot.timestamp
                memory_diff = snapshot.rss_mb - prev_snapshot.rss_mb
                if time_diff > 0:
                    growth_rate = memory_diff / time_diff * 3600  # MB per hour

            growth_points.append(
                MemoryGrowthPoint(
                    timestamp=snapshot.timestamp,
                    memory_mb=memory_mb,
                    operation_count=i,
                    growth_rate_mb_per_sec=growth_rate,
                )
            )

        return growth_points

    def detect_memory_leaks(
        self, threshold_mb_per_hour: float = 50.0
    ) -> MemoryLeakAnalysis:
        """Detect potential memory leaks based on growth patterns."""
        growth_points = self.get_memory_growth_trend()

        if len(growth_points) < 10:
            return MemoryLeakAnalysis(
                has_leak=False,
                growth_rate_mb_per_hour=0.0,
                confidence_score=0.0,
                recommendations=["Need more data points for leak analysis"],
            )

        # Calculate average growth rate
        growth_rates = [
            p.growth_rate_mb_per_sec for p in growth_points[-20:]
        ]  # Last 20 points
        avg_growth_rate = (
            sum(growth_rates) / len(growth_rates) * 3600
        )  # Convert to MB/hour

        # Simple leak detection: consistent growth above threshold
        has_leak = avg_growth_rate > threshold_mb_per_hour

        # Calculate confidence based on consistency
        if growth_rates:
            # Coefficient of variation (lower = more consistent growth)
            mean_rate = sum(growth_rates) / len(growth_rates)
            variance = sum((r - mean_rate) ** 2 for r in growth_rates) / len(
                growth_rates
            )
            std_dev = variance**0.5
            cv = std_dev / mean_rate if mean_rate > 0 else float("inf")

            # Lower coefficient of variation = higher confidence
            confidence_score = max(0.0, min(1.0, 1.0 - cv))
        else:
            confidence_score = 0.0

        # Identify problematic areas
        problematic_areas = []
        if self.snapshots:
            latest = self.snapshots[-1]
            if latest.objects_count > 100000:  # Arbitrary threshold
                problematic_areas.append("High object count")
            if latest.top_allocations:
                problematic_areas.extend(
                    [area for area, _ in latest.top_allocations[:3]]
                )

        # Generate recommendations
        recommendations = []
        if has_leak:
            recommendations.append(
                "Memory leak detected - investigate growing allocations"
            )
            if confidence_score > 0.7:
                recommendations.append(
                    "High confidence leak - immediate investigation recommended"
                )
        else:
            recommendations.append("No significant memory leak detected")

        if problematic_areas:
            recommendations.append(f"Focus on: {', '.join(problematic_areas)}")

        return MemoryLeakAnalysis(
            has_leak=has_leak,
            growth_rate_mb_per_hour=avg_growth_rate,
            confidence_score=confidence_score,
            problematic_areas=problematic_areas,
            recommendations=recommendations,
        )

    def get_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory report."""
        if not self.snapshots:
            return {"error": "No snapshots available"}

        latest = self.snapshots[-1]
        baseline = self.baseline_snapshot

        # Calculate memory delta
        memory_delta = 0.0
        if baseline:
            memory_delta = latest.rss_mb - baseline.rss_mb

        # Get growth trend
        growth_points = self.get_memory_growth_trend()
        leak_analysis = self.detect_memory_leaks()

        # Calculate statistics
        memory_values = [s.rss_mb for s in self.snapshots]
        object_counts = [s.objects_count for s in self.snapshots]

        report = {
            "summary": {
                "current_memory_mb": latest.rss_mb,
                "memory_delta_mb": memory_delta,
                "current_objects": latest.objects_count,
                "total_snapshots": len(self.snapshots),
                "profiling_duration_sec": latest.timestamp
                - self.snapshots[0].timestamp,
            },
            "statistics": {
                "memory_mb": {
                    "min": min(memory_values),
                    "max": max(memory_values),
                    "avg": sum(memory_values) / len(memory_values),
                    "latest": latest.rss_mb,
                },
                "objects": {
                    "min": min(object_counts),
                    "max": max(object_counts),
                    "avg": sum(object_counts) / len(object_counts),
                    "latest": latest.objects_count,
                },
            },
            "leak_analysis": {
                "has_leak": leak_analysis.has_leak,
                "growth_rate_mb_per_hour": leak_analysis.growth_rate_mb_per_hour,
                "confidence_score": leak_analysis.confidence_score,
                "problematic_areas": leak_analysis.problematic_areas,
                "recommendations": leak_analysis.recommendations,
            },
            "top_allocations": latest.top_allocations,
            "snapshots": [
                s.to_dict() for s in list(self.snapshots)[-10:]
            ],  # Last 10 snapshots
        }

        return report

    def save_memory_report(self, filepath: Optional[Path] = None) -> Path:
        """Save memory report to JSON file."""
        if filepath is None:
            timestamp = int(time.time())
            filepath = Path(f"memory_report_{timestamp}.json")

        report = self.get_memory_report()

        with open(filepath, "w") as f:
            import json

            json.dump(report, f, indent=2, default=str)

        logger.info("Memory report saved", filepath=str(filepath))
        return filepath

    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return stats."""
        gc.collect(0)  # Young generation
        gc.collect(1)  # Middle generation
        gc.collect(2)  # Old generation

        before_objects = len(gc.get_objects())
        gc.collect()
        after_objects = len(gc.get_objects())

        return {
            "objects_before": before_objects,
            "objects_after": after_objects,
            "objects_freed": before_objects - after_objects,
            "gc_stats": {f"gen{i}": gc.get_count()[i] for i in range(3)},
        }


class AsyncMemoryProfiler:
    """Memory profiler specifically designed for async operations."""

    def __init__(self, profiler: MemoryProfiler):
        self.profiler = profiler
        self.operation_snapshots: Dict[str, List[MemorySnapshot]] = defaultdict(list)

    async def profile_operation(
        self,
        operation_name: str,
        operation_func,
        *args,
        **kwargs,
    ) -> Tuple[Any, List[MemorySnapshot]]:
        """Profile a single async operation."""
        # Start profiling if not already running
        was_profiling = self.profiler.is_profiling
        if not was_profiling:
            await self.profiler.start_profiling()

        # Take pre-operation snapshot
        pre_snapshot = await self.profiler._take_snapshot()

        try:
            # Execute operation
            result = await operation_func(*args, **kwargs)

            # Take post-operation snapshot
            post_snapshot = await self.profiler._take_snapshot()

            # Store snapshots for this operation
            self.operation_snapshots[operation_name].extend(
                [pre_snapshot, post_snapshot]
            )

            return result, [pre_snapshot, post_snapshot]

        except Exception as e:
            # Take error snapshot
            error_snapshot = await self.profiler._take_snapshot()
            self.operation_snapshots[operation_name].append(error_snapshot)
            raise e
        finally:
            # Stop profiling if we started it
            if not was_profiling:
                await self.profiler.stop_profiling()

    def get_operation_memory_impact(self, operation_name: str) -> Dict[str, Any]:
        """Get memory impact analysis for a specific operation."""
        snapshots = self.operation_snapshots.get(operation_name, [])

        if len(snapshots) < 2:
            return {"error": "Insufficient data for operation analysis"}

        # Analyze memory changes across operation executions
        memory_deltas = []
        object_deltas = []

        for i in range(0, len(snapshots) - 1, 2):  # Process pairs
            if i + 1 < len(snapshots):
                pre = snapshots[i]
                post = snapshots[i + 1]

                memory_delta = post.rss_mb - pre.rss_mb
                object_delta = post.objects_count - pre.objects_count

                memory_deltas.append(memory_delta)
                object_deltas.append(object_delta)

        if not memory_deltas:
            return {"error": "No complete operation pairs found"}

        return {
            "operation_name": operation_name,
            "executions_analyzed": len(memory_deltas),
            "memory_impact_mb": {
                "min": min(memory_deltas),
                "max": max(memory_deltas),
                "avg": sum(memory_deltas) / len(memory_deltas),
                "total": sum(memory_deltas),
            },
            "object_impact": {
                "min": min(object_deltas),
                "max": max(object_deltas),
                "avg": sum(object_deltas) / len(object_deltas),
                "total": sum(object_deltas),
            },
        }


# Utility functions for common profiling tasks
async def profile_chat_operation(
    chat_service,
    conversation,
    message: str,
    profiler: MemoryProfiler,
) -> Tuple[Any, Dict[str, Any]]:
    """Profile a single chat operation."""
    async_profiler = AsyncMemoryProfiler(profiler)

    async def chat_operation():
        events = []
        async for event in chat_service.stream_chat(
            conversation=conversation,
            user_message=message,
            store_user_message=True,
        ):
            events.append(event)
        return events

    result, snapshots = await async_profiler.profile_operation(
        "chat_streaming",
        chat_operation,
    )

    return result, async_profiler.get_operation_memory_impact("chat_streaming")


async def profile_memory_operations(
    memory_service,
    queries: List[str],
    profiler: MemoryProfiler,
) -> Dict[str, Any]:
    """Profile memory search operations."""
    async_profiler = AsyncMemoryProfiler(profiler)

    results = {}

    for i, query in enumerate(queries):
        operation_name = f"memory_search_{i}"

        async def memory_operation():
            return await memory_service.search(query, limit=10)

        try:
            result, snapshots = await async_profiler.profile_operation(
                operation_name,
                memory_operation,
            )
            results[operation_name] = async_profiler.get_operation_memory_impact(
                operation_name
            )
        except Exception as e:
            results[operation_name] = {"error": str(e)}

    return results


# Example usage and testing
async def run_memory_profile_test():
    """Run a comprehensive memory profiling test."""
    profiler = MemoryProfiler(sampling_interval=0.5, max_snapshots=100)

    print("Starting memory profiling test...")

    # Start profiling
    await profiler.start_profiling()

    # Simulate some operations
    await asyncio.sleep(5.0)  # Let it run for 5 seconds

    # Stop profiling
    await profiler.stop_profiling()

    # Generate report
    report = profiler.get_memory_report()
    print(
        f"Memory profiling completed. Final memory: {report['summary']['current_memory_mb']:.2f} MB"
    )

    # Check for leaks
    leak_analysis = profiler.detect_memory_leaks()
    print(f"Memory leak detected: {leak_analysis.has_leak}")
    print(f"Growth rate: {leak_analysis.growth_rate_mb_per_hour:.2f} MB/hour")

    # Save report
    profiler.save_memory_report()

    return report


if __name__ == "__main__":
    # Run test when executed directly
    report = asyncio.run(run_memory_profile_test())
    print("Memory profiling test completed!")
