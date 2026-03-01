#!/bin/bash
# Setup script for Company Monitor Agent

set -e

echo "Setting up Company Monitor Agent..."
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env created - please edit with your credentials"
else
    echo "✓ .env already exists"
fi

# Run tests
echo ""
echo "Running tests..."
python3 test_setup.py

echo ""
echo "Setup complete!"
echo ""
echo "To use the agent:"
echo "  1. Activate the environment: source venv/bin/activate"
echo "  2. Edit config/companies.yaml to add your companies"
echo "  3. Edit .env with your API keys and email credentials"
echo "  4. Run: python scheduler.py --run-once"
echo ""
