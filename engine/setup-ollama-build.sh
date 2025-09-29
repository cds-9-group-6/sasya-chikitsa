#!/bin/bash

# Setup script for Sasya Chikitsa Ollama builds
# Makes all scripts executable and validates environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 Setting up Sasya Chikitsa Ollama build environment..."

# Make scripts executable
chmod +x "$SCRIPT_DIR/build-ollama-models.sh"
chmod +x "$SCRIPT_DIR/container-runtime-utils.sh"

echo "✅ Made scripts executable"

# Check for required files
required_files=(
    "Dockerfile.ollama-models"
    "Modelfile.llama3.1"
    "Modelfile.llava"
    "build-ollama-models.sh"
    "container-runtime-utils.sh"
)

echo "🔍 Checking required files..."
for file in "${required_files[@]}"; do
    if [[ -f "$SCRIPT_DIR/$file" ]]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING"
        exit 1
    fi
done

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Quick Start:"
echo "  • View help: ./engine/build-ollama-models.sh --help"
echo "  • Dry run: ./engine/build-ollama-models.sh --dry-run"
echo "  • Build all: ./engine/build-ollama-models.sh --version v1.0"
echo "  • Build specific: ./engine/build-ollama-models.sh --platform arm64 --models llama31"
echo ""
echo "🐳 Make sure Docker/Podman is running before building!"
