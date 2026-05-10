#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "      ClassMap Server Launcher"
echo "========================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Error: Python 3 is not installed or not found."
    echo "Please install Python 3 from python.org to continue."
    echo "Press any key to exit..."
    read -n 1 -s
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Initializing virtual environment (first run only)..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements quietly
echo "🔄 Checking and installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Attempt to stop any existing ghost process running on port 5555
echo "🧹 Cleaning up port 5555..."
lsof -t -i :5555 | xargs -I {} kill -9 {} 2>/dev/null || true

# Run the application
echo "🚀 Launching Application..."
python3 run.py
