#!/bin/bash

# Download Ollama models locally for cross-platform Docker builds
# This avoids emulation issues when building AMD64 images on ARM64 Mac

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📥 Downloading Ollama Multi-Models for Cross-Platform Builds${NC}"
echo -e "${BLUE}Models: llama3.1:8b (text) + llava-llama3:8b (vision)${NC}"
echo ""

# Check if ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Error: Ollama is not installed${NC}"
    echo -e "${YELLOW}Please install Ollama from: https://ollama.ai${NC}"
    exit 1
fi

# Check if ollama is running
if ! curl -s -f http://localhost:11434/api/version > /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama is not running. Starting Ollama...${NC}"
    echo -e "${YELLOW}Please make sure Ollama app is running on your Mac${NC}"
    echo ""
    echo -e "${BLUE}Waiting for Ollama to start...${NC}"
    
    # Wait for Ollama to be available
    for i in {1..30}; do
        if curl -s -f http://localhost:11434/api/version > /dev/null; then
            echo -e "${GREEN}✅ Ollama is now running${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Ollama failed to start. Please start it manually.${NC}"
            exit 1
        fi
        sleep 2
        echo -n "."
    done
fi

# Get Ollama version
OLLAMA_VERSION=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}🔍 Ollama version: ${OLLAMA_VERSION}${NC}"
echo ""

# Models to download
MODELS=("llama3.1:8b" "llava-llama3:8b")

# Download each model
for model in "${MODELS[@]}"; do
    echo -e "${BLUE}📥 Downloading ${model}...${NC}"
    
    if ollama pull "$model"; then
        echo -e "${GREEN}✅ Successfully downloaded ${model}${NC}"
    else
        echo -e "${RED}❌ Failed to download ${model}${NC}"
        exit 1
    fi
    echo ""
done

# Find ollama models directory
OLLAMA_MODELS_DIR=""
if [[ -d "$HOME/.ollama/models" ]]; then
    OLLAMA_MODELS_DIR="$HOME/.ollama/models"
elif [[ -d "/usr/share/ollama/.ollama/models" ]]; then
    OLLAMA_MODELS_DIR="/usr/share/ollama/.ollama/models"
else
    echo -e "${YELLOW}🔍 Searching for Ollama models directory...${NC}"
    OLLAMA_MODELS_DIR=$(find /Users -name "models" -path "*/.ollama/models" -type d 2>/dev/null | head -1)
    
    if [[ -z "$OLLAMA_MODELS_DIR" ]]; then
        echo -e "${RED}❌ Could not find Ollama models directory${NC}"
        echo -e "${YELLOW}Please check where Ollama stores models on your system${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}📁 Found Ollama models directory: ${OLLAMA_MODELS_DIR}${NC}"

# Create local model_files directory for Docker build
MODEL_FILES_DIR="$(dirname "$0")/model_files"
echo -e "${BLUE}📁 Creating build directory: ${MODEL_FILES_DIR}${NC}"

# Remove existing model_files if it exists
if [[ -d "$MODEL_FILES_DIR" ]]; then
    echo -e "${YELLOW}🗑️  Removing existing model_files directory...${NC}"
    rm -rf "$MODEL_FILES_DIR"
fi

# Copy models to build directory
echo -e "${BLUE}📦 Copying model files for Docker build...${NC}"
cp -r "$OLLAMA_MODELS_DIR" "$MODEL_FILES_DIR"

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Model files copied successfully${NC}"
    
    # Show directory contents and size
    echo ""
    echo -e "${BLUE}📊 Model files summary:${NC}"
    echo -e "${YELLOW}Directory size: $(du -sh "$MODEL_FILES_DIR" | cut -f1)${NC}"
    echo -e "${YELLOW}Files count: $(find "$MODEL_FILES_DIR" -type f | wc -l)${NC}"
    echo ""
    
    # Show main directories
    echo -e "${BLUE}📁 Directory structure:${NC}"
    ls -la "$MODEL_FILES_DIR"
    
    echo ""
    echo -e "${GREEN}🎉 Multi-model download and preparation completed!${NC}"
    echo ""
    echo -e "${BLUE}📋 Downloaded models:${NC}"
    echo -e "${BLUE}  📝 llama3.1:8b - Text AI for conversations and Q&A${NC}"
    echo -e "${BLUE}  👁️  llava-llama3:8b - Vision AI for image analysis${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo -e "${BLUE}  1. Run cross-platform build: ./engine/build-cross-platform.sh --version v1.0${NC}"
    echo -e "${BLUE}  2. The build will use pre-downloaded models (no emulation issues)${NC}"
    echo -e "${BLUE}  3. Clean up later: rm -rf ${MODEL_FILES_DIR}${NC}"
    echo ""
    echo -e "${YELLOW}💡 This approach avoids segmentation faults during cross-platform builds${NC}"
    
else
    echo -e "${RED}❌ Failed to copy model files${NC}"
    exit 1
fi
