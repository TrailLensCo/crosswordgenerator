#!/bin/bash
#
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

set -uo pipefail

# Script to generate Newfoundland 21x21 crossword puzzle with logging and analysis

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"
CONFIG_FILE="$PROJECT_ROOT/config/sample_configs/newfoundland-21x21.yaml"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Newfoundland 21x21 Crossword Generator with Analysis      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration: $CONFIG_FILE"
echo "Working directory: $SRC_DIR"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Check if src directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo "❌ Error: Source directory not found: $SRC_DIR"
    exit 1
fi

# Activate virtual environment if it exists
VENV_DIR="$PROJECT_ROOT/.venv"
if [ -d "$VENV_DIR" ]; then
    echo "🔧 Activating virtual environment..."
    # shellcheck disable=SC1091
    if source "$VENV_DIR/bin/activate"; then
        echo "   ✓ Virtual environment activated"
    else
        echo "   ⚠️  Warning: Failed to activate virtual environment"
        echo "   Continuing with system Python..."
    fi
    echo ""
else
    echo "ℹ️  Virtual environment not found at $VENV_DIR"
    echo "   Using system Python. Run './scripts/setup-env.sh' to create venv."
    echo ""
fi

# Check if API key is available
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set in environment"
    echo "   The generator will check for API key in other locations:"
    echo "   - .claude-apikey.txt in repository root"
    echo "   - ~/.claude/credentials.json"
    echo "   - ~/.anthropic/api_key"
    echo ""
fi

# Change to src directory
if ! cd "$SRC_DIR"; then
    echo "❌ Error: Failed to change to directory: $SRC_DIR"
    exit 1
fi

# Run the generator with logging and analysis
echo "🚀 Starting puzzle generation..."
echo "   Log level: INFO"
echo "   Console output: Enabled"
echo "   AI analysis: Enabled"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Run with --analyze-log to automatically generate AI report
# Use --require-ai to force AI usage and avoid fallback to base word list
python3 crossword_generator.py \
    --config "$CONFIG_FILE" \
    --analyze-log \
    --require-ai \
    --verbose

EXIT_CODE=$?

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Generation complete!"
    echo ""
    echo "Output files are in: $PROJECT_ROOT/output/newfoundland-21x21/"
    echo ""
    echo "Generated files:"
    echo "  • Puzzle grid (blank): newfoundland_culture__21x21_puzzle.svg"
    echo "  • Clues list: newfoundland_culture__21x21_clues.svg"
    echo "  • Solution grid: newfoundland_culture__21x21_solution.svg"
    echo "  • Complete HTML: newfoundland_culture__21x21_complete.html"
    echo "  • Log file: crossword_generator_*.log"
    echo "  • AI Analysis Report: generation_report_*.md"
    echo ""
    echo "📊 View the AI analysis report for detailed insights and recommendations."
else
    echo "❌ Generation failed with exit code $EXIT_CODE"
    echo ""
    echo "Check the log file in $PROJECT_ROOT/output/newfoundland-21x21/ for details."
    exit $EXIT_CODE
fi
