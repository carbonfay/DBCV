#!/bin/bash

# Test script for OpenWeatherMap UV Index integration
# This script sets up a minimal environment and runs tests

set -e  # Exit on any error

echo "=== OpenWeatherMap UV Index Integration Test Script ==="
echo

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the backend directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel

# Install required packages
echo "Installing required packages..."
python3 -m pip install 'httpx>=0.27.0' 'respx>=0.20.0' 'pytest>=8.0.0' 'pytest-asyncio>=0.24.0'

# Set PYTHONPATH
export PYTHONPATH="$(pwd)"

echo
echo "=== Running Standalone Unit Tests ==="
python3 app/integrations/openweathermap/run_test_uv_unit.py

echo
echo "=== Standalone Tests Completed Successfully ==="
echo

# Check if API key is provided
if [ -n "$OPENWEATHERMAP_API_KEY" ] || [ -n "$OPENWEATHERMAP_KEY" ]; then
    echo "=== Running Real API Test (API key found) ==="
    export OPENWEATHERMAP_API_KEY="${OPENWEATHERMAP_API_KEY:-$OPENWEATHERMAP_KEY}"
    python3 app/integrations/openweathermap/test_get_uv_index.py
    echo "=== Real API Test Completed ==="
else
    echo "=== Skipping Real API Test (no OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_KEY env var) ==="
    echo "To test with real API, set OPENWEATHERMAP_API_KEY environment variable:"
    echo "export OPENWEATHERMAP_API_KEY=your_api_key_here"
    echo "Then run: python3 app/integrations/openweathermap/test_get_uv_index.py"
fi

echo
echo "=== All Tests Completed Successfully! ==="
echo
echo "Integration files:"
echo "- app/integrations/openweathermap/get_uv_index.py (main integration)"
echo "- app/integrations/openweathermap/__init__.py (registration)"
echo "- app/tests/integrations/test_openweathermap_uv.py (pytest tests)"
echo "- app/integrations/openweathermap/test_get_uv_index.py (manual test)"
echo "- app/integrations/openweathermap/run_test_uv_unit.py (standalone runner)"
echo
echo "To run pytest tests (requires full project dependencies):"
echo "pip install -r requirements.txt -r requirements-dev.txt"
echo "pytest app/tests/integrations/test_openweathermap_uv.py -v"