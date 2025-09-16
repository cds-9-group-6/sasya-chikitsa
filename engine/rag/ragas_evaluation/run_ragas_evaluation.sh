#!/bin/bash

# RAGAS Evaluation Environment Setup and Execution Script
# Usage: ./run_ragas_evaluation.sh

set -e  # Exit on any error

# Default directories
LOG_DIR="./evaluation_logs"
METRICS_DIR="$LOG_DIR/metrics"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Ensure log directories exist
mkdir -p "$METRICS_DIR"

echo "🔍 Checking RAGAS Evaluation Environment..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  No virtual environment detected!"
    echo "   It is recommended to use a virtual environment for RAGAS evaluation."
    echo ""
    echo "💡 To create and activate a virtual environment:"
    echo "   python3 -m venv ragas_env"
    echo "   source ragas_env/bin/activate  # On Windows: ragas_env\\Scripts\\activate"
    echo ""
    exit 1
else
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
fi

# Check dependencies
echo ""
echo "🔍 Checking dependencies..."
if ! python3 -m pip check &> /dev/null; then
    echo "❌ Some dependencies are missing or outdated."
    echo "   Run the following command to install them:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "✅ All dependencies are satisfied!"
echo ""

# Run evaluations
echo "🚀 Running RAGAS evaluations..."
echo ""

# Run retrieval evaluation
echo "🔍 Running retrieval evaluation..."
python3 retrieval_evaluation.py --log-dir "$METRICS_DIR" --timestamp "$TIMESTAMP"

# Run generation evaluation
echo "🔍 Running generation evaluation..."
python3 generation_evaluation.py --log-dir "$METRICS_DIR" --timestamp "$TIMESTAMP"

# Run system evaluation
echo "🔍 Running system evaluation..."
python3 system_evaluation.py --log-dir "$METRICS_DIR" --timestamp "$TIMESTAMP"

echo ""
echo "🎉 All evaluations completed! Logs and metrics are saved in: $LOG_DIR"