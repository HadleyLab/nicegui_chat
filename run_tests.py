#!/usr/bin/env python3
"""
Test Runner Script for MammoChat™

This script provides convenient commands for running tests in different modes
for lean and agile development.

Usage:
    python run_tests.py fast      # Run fast unit tests only
    python run_tests.py all       # Run all tests with coverage
    python run_tests.py integration  # Run integration tests with real APIs
    python run_tests.py ci        # Run CI-style tests with coverage
    python run_tests.py models    # Run model tests only
    python run_tests.py services  # Run service tests only
    python run_tests.py bugs      # Run bug-specific tests
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=False, cwd=Path(__file__).parent)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error running command: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "fast":
        # Run fast unit tests only (no coverage, no integration)
        success = run_command(
            [
                "pytest",
                "-x",
                "--tb=short",
                "tests/test_models.py",
                "tests/test_utils.py",
                "tests/test_bugs.py",
            ],
            "Running fast unit tests",
        )

    elif command == "all":
        # Run all tests with coverage
        success = run_command(
            [
                "pytest",
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-fail-under=70",
            ],
            "Running all tests with coverage",
        )

    elif command == "integration":
        # Run integration tests only
        success = run_command(
            ["pytest", "-m", "integration", "--tb=short"],
            "Running integration tests with real APIs",
        )

    elif command == "ci":
        # Run CI-style tests
        success = run_command(
            [
                "pytest",
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=xml",
                "--cov-fail-under=70",
                "--junitxml=junit.xml",
            ],
            "Running CI-style tests",
        )

    elif command == "models":
        # Run model tests only
        success = run_command(
            ["pytest", "tests/test_models.py", "-v"], "Running model tests"
        )

    elif command == "services":
        # Run service tests only
        success = run_command(
            ["pytest", "tests/test_services.py", "-v"], "Running service tests"
        )

    elif command == "bugs":
        # Run bug-specific tests
        success = run_command(
            ["pytest", "tests/test_bugs.py", "-v"], "Running bug-specific tests"
        )

    elif command == "coverage":
        # Show coverage report
        success = run_command(
            ["pytest", "--cov=src", "--cov-report=html"], "Generating coverage report"
        )
        if success:
            print("\n📊 Coverage report generated in htmlcov/index.html")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        return

    if success:
        print(f"\n✅ {command} tests completed successfully!")
    else:
        print(f"\n❌ {command} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
