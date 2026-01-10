#!/bin/bash
#
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

set -euo pipefail

# Script to setup Python virtual environment for crossword generator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "🔧 Setting up Python virtual environment..."
echo "Project root: $PROJECT_ROOT"
echo "Virtual environment: $VENV_DIR"
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"

# Check minimum Python version (3.8+)
MIN_VERSION="3.8"
CURRENT_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

if [ "$(printf '%s\n' "$MIN_VERSION" "$CURRENT_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then
    echo "❌ Error: Python $MIN_VERSION or higher is required (found $CURRENT_VERSION)"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual environment already exists at $VENV_DIR"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        echo "ℹ️  Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📥 Installing dependencies from requirements.txt..."
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
    echo "✓ Dependencies installed"
else
    echo "⚠️  No requirements.txt found, skipping dependency installation"
fi

# Install package in editable mode
echo ""
echo "📦 Installing crossword-generator in editable mode..."
if [ -f "$PROJECT_ROOT/setup.py" ]; then
    pip install -e "$PROJECT_ROOT"
    echo "✓ Package installed in editable mode"
else
    echo "⚠️  No setup.py found, skipping package installation"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""
echo "To run the crossword generator:"
echo "  cd src"
echo "  python crossword_generator.py --topic 'Animals' --size 5"
echo ""
