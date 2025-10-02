#!/bin/bash
# Quick start script for NiceGUI Chat

echo "🚀 Starting NiceGUI Chat..."
echo "📍 Open your browser at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
python main.py
