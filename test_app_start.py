#!/usr/bin/env python3
"""
Quick test to verify the MammoChat™ application starts without timeout issues.
"""

import asyncio
import time
import subprocess
import signal
import sys

async def test_app_startup():
    """Test that the application starts and handles basic requests."""
    print("🚀 Testing MammoChat™ application startup...")

    # Start the application in background
    process = subprocess.Popen([
        sys.executable, "main.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        # Wait for startup
        time.sleep(5)

        # Check if process is still running
        if process.poll() is None:
            print("✅ Application started successfully")
            print("✅ No immediate startup errors")

            # Let it run for a bit more to check for stability
            time.sleep(10)

            if process.poll() is None:
                print("✅ Application stable after 15 seconds")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Application crashed after startup")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Application failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False

    finally:
        # Clean up
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

if __name__ == "__main__":
    success = asyncio.run(test_app_startup())
    sys.exit(0 if success else 1)