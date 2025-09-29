#!/bin/bash

# Cross-platform Ollama build script for OpenShift deployment
# Builds AMD64 images on ARM64 MacBook

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏗️  Cross-Platform Ollama Multi-Model Build for OpenShift${NC}"
echo -e "${BLUE}Building AMD64 image with llama3.1:8b + llava-llama3:8b on ARM64 MacBook${NC}"
echo ""

# Check if we're in the right directory
if [[ ! -f "engine/Dockerfile.ollamamodel" ]]; then
    echo -e "${RED}❌ Error: Must run from sasya-chikitsa root directory${NC}"
    exit 1
fi

# Default values
VERSION="v1.0"
REGISTRY=""
PUSH=false
PLATFORMS="linux/amd64"
TAG_PREFIX="ollama-multi-model"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --version <version>    Version tag (default: v1.0)"
            echo "  --registry <registry>  Registry to push to (e.g., quay.io/username)"
            echo "  --push                 Push to registry after build"
            echo "  --platforms <list>     Platforms to build (default: linux/amd64)"
            echo "  --help                 Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --version v1.0"
            echo "  $0 --version v1.0 --registry quay.io/myorg --push"
            echo "  $0 --platforms linux/amd64,linux/arm64"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Build configuration
IMAGE_NAME="${TAG_PREFIX}:${PLATFORMS//\//-}-${VERSION}"
if [[ -n "$REGISTRY" ]]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="localhost/${IMAGE_NAME}"
fi

echo -e "${YELLOW}Configuration:${NC}"
echo -e "${YELLOW}  Version: ${VERSION}${NC}"
echo -e "${YELLOW}  Platforms: ${PLATFORMS}${NC}"
echo -e "${YELLOW}  Image: ${FULL_IMAGE_NAME}${NC}"
echo -e "${YELLOW}  Push to registry: ${PUSH}${NC}"
echo ""

# Check container runtime
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    echo -e "${GREEN}🐙 Using Podman${NC}"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    echo -e "${GREEN}🐳 Using Docker${NC}"
else
    echo -e "${RED}❌ Neither Podman nor Docker found${NC}"
    exit 1
fi

# Setup QEMU for cross-platform builds (if using Docker)
if [[ "$CONTAINER_CMD" == "docker" ]]; then
    echo -e "${BLUE}🔧 Setting up QEMU for cross-platform builds...${NC}"
    docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
fi

# Check if model files are available
MODEL_FILES_DIR="engine/model_files"
if [[ ! -d "$MODEL_FILES_DIR" ]]; then
    echo -e "${YELLOW}⚠️  Model files not found. Downloading models first...${NC}"
    if ! ./engine/download-models.sh; then
        echo -e "${RED}❌ Model download failed${NC}"
        exit 1
    fi
    echo ""
fi

echo -e "${BLUE}🏗️  Starting cross-platform build...${NC}"
echo -e "${YELLOW}This should be fast (using pre-downloaded models)${NC}"
echo ""

# Build the image
if [[ "$CONTAINER_CMD" == "podman" ]]; then
    # Podman build
    $CONTAINER_CMD build \
        --platform="${PLATFORMS}" \
        --tag="${FULL_IMAGE_NAME}" \
        -f engine/Dockerfile.ollamamodel \
        .
else
    # Docker build with buildx
    docker buildx build \
        --platform="${PLATFORMS}" \
        --tag="${FULL_IMAGE_NAME}" \
        --load \
        -f engine/Dockerfile.ollamamodel \
        .
fi

if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
    
    # Show image info
    echo -e "${BLUE}📊 Image Details:${NC}"
    $CONTAINER_CMD images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.Created}}"
    echo ""
    
    # Test the image (basic validation)
    echo -e "${BLUE}🧪 Testing image startup...${NC}"
    CONTAINER_ID=$($CONTAINER_CMD run -d -p 11434:11434 "${FULL_IMAGE_NAME}")
    sleep 10
    
    if curl -s -f http://localhost:11434/api/version > /dev/null; then
        echo -e "${GREEN}✅ Image test passed - Ollama API responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Image test warning - API not responding (may need more time)${NC}"
    fi
    
    # Cleanup test container
    $CONTAINER_CMD stop "$CONTAINER_ID" > /dev/null 2>&1 || true
    $CONTAINER_CMD rm "$CONTAINER_ID" > /dev/null 2>&1 || true
    
    # Push to registry if requested
    if [[ "$PUSH" == "true" ]]; then
        if [[ -n "$REGISTRY" ]]; then
            echo ""
            echo -e "${BLUE}📤 Pushing to registry...${NC}"
            $CONTAINER_CMD push "${FULL_IMAGE_NAME}"
            
            if [[ $? -eq 0 ]]; then
                echo -e "${GREEN}✅ Successfully pushed to registry!${NC}"
            else
                echo -e "${RED}❌ Failed to push to registry${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  --registry not specified, skipping push${NC}"
        fi
    fi
    
    # Clean up model files (optional - saves ~4GB disk space)
    echo ""
    read -p "🗑️  Clean up downloaded model files to save disk space? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}📁 Keeping model files in engine/model_files for future builds${NC}"
    else
        echo -e "${BLUE}🗑️  Cleaning up model files...${NC}"
        rm -rf "$MODEL_FILES_DIR"
        echo -e "${GREEN}✅ Model files cleaned up (saved ~4GB disk space)${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Cross-platform build completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Usage:${NC}"
    echo -e "${BLUE}  Local test: ${CONTAINER_CMD} run -it --rm -p 11434:11434 ${FULL_IMAGE_NAME}${NC}"
    echo -e "${BLUE}  API test: curl http://localhost:11434/api/version${NC}"
    if [[ -n "$REGISTRY" ]]; then
        echo -e "${BLUE}  OpenShift: Use image ${FULL_IMAGE_NAME}${NC}"
    fi
    echo ""
    echo ""
    echo -e "${BLUE}🤖 Available Models:${NC}"
    echo -e "${BLUE}  📝 Text AI: curl -X POST http://localhost:11434/api/generate \\${NC}"
    echo -e "${BLUE}              -H 'Content-Type: application/json' \\${NC}"
    echo -e "${BLUE}              -d '{\"model\": \"llama3.1:8b\", \"prompt\": \"Hello!\", \"stream\": false}'${NC}"
    echo ""  
    echo -e "${BLUE}  👁️  Vision AI: curl -X POST http://localhost:11434/api/generate \\${NC}"
    echo -e "${BLUE}               -H 'Content-Type: application/json' \\${NC}"
    echo -e "${BLUE}               -d '{\"model\": \"llava-llama3:8b\", \"prompt\": \"Describe this image\", \"images\": [\"base64-image\"], \"stream\": false}'${NC}"
    echo ""
    echo -e "${YELLOW}💡 This multi-model AMD64 image will run on OpenShift clusters${NC}"
    
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
