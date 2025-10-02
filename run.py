#!/usr/bin/env python3
"""Quick start script for NiceGUI Chat."""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from main import main  # noqa: E402

if __name__ == "__main__":
    print("🚀 Starting NiceGUI Chat...")
    print("📍 Open your browser at: http://localhost:8080")
    print("Press Ctrl+C to stop the server\n")
    main()
