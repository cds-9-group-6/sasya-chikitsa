#!/bin/bash

echo "🌿 Setting up LLaVA Plant Disease Detection"
echo "=========================================="

# Check if ollama is installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama found"
else
    echo "❌ Ollama not found. Installing..."
    echo "Please install Ollama from: https://ollama.ai"
    echo "Or run: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Pull LLaVA model
echo "📦 Downloading LLaVA model..."
ollama pull llava

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements_llava.txt

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Usage examples:"
echo "  # Analyze a leaf image"
echo "  python llava_disease_detector.py path/to/leaf.jpg"
echo ""
echo "  # Use custom prompt"
echo "  python llava_disease_detector.py leaf.jpg --prompt 'Is this tomato plant healthy?'"
echo ""
echo "  # Use transformers method (requires more memory)"
echo "  python llava_disease_detector.py leaf.jpg --method transformers"
