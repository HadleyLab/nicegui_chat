#!/usr/bin/env python3
"""
Simple regression test runner that avoids pytest dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_regression_suite import create_regression_test_suite


async def run_simple_regression_tests():
    """Run regression tests without pytest dependencies."""
    print("Running simple regression tests...")

    suite = create_regression_test_suite()
    results = await suite.run_all_tests(performance_monitoring=False)

    # Print results
    passed = sum(1 for r in results.values() if r.success)
    total = len(results)

    print("\nRegression Test Results:")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.1f}%")

    # Show details
    for name, result in results.items():
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"  {name}: {status} ({result.execution_time_ms:.2f}ms)")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_simple_regression_tests())
    sys.exit(0 if success else 1)
