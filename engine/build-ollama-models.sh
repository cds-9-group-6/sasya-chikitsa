#!/bin/bash

# Sasya Chikitsa Ollama Multi-Model Build Script
# Builds 6 different combinations of platforms and models for ollama
# Usage: ./engine/build-ollama-models.sh [OPTIONS]

set -e

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ .*/sasya-chikitsa$ ]]; then
    echo -e "${RED}Error: This script must be run from the sasya-chikitsa directory.${NC}"
    echo -e "${YELLOW}Current directory: $CURRENT_DIR${NC}"
    echo -e "${YELLOW}Expected to end with: sasya-chikitsa${NC}"
    exit 1
fi

# Source container runtime utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/container-runtime-utils.sh"

# Detect and configure container runtime
if ! detect_container_runtime; then
    exit 1
fi

# Default configuration
VERSION="latest"
BUILD_PLATFORMS=("arm64" "amd64")
MODEL_COMBINATIONS=(
    "llama-3.1:8b|llama31-only"
    "llava-llama3:8b|llava-only"
    "llama-3.1:8b,llava-llama3:8b|both-models"
)
BUILD_ALL=true
DRY_RUN=false
REGISTRY="quay.io/rajivranjan"
PUSH_TO_REGISTRY=false

# Function to display usage
show_usage() {
    echo -e "${CYAN}Sasya Chikitsa Ollama Multi-Model Build Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --version <version>     Version tag for the images (default: latest)"
    echo "  --platform <platform>   Build for specific platform: amd64, arm64, or both (default: both)"
    echo "  --models <combination>   Build specific model combination:"
    echo "                           llama31 = llama-3.1:8b only"
    echo "                           llava = llava-llama3:8b only"  
    echo "                           both = both models"
    echo "                           all = all combinations (default)"
    echo "  --registry <registry>    Registry to push to (default: quay.io/rajivranjan)"
    echo "  --push                   Automatically push to registry (default: interactive)"
    echo "  --dry-run               Show what would be built without actually building"
    echo "  --help                  Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 --version v1.0 --platform arm64 --models llama31"
    echo "  $0 --version v1.0 --platform both --models all"
    echo "  $0 --dry-run --platform amd64"
    echo ""
    echo -e "${YELLOW}Build Matrix (6 total images):${NC}"
    echo "  1. arm64 + llama-3.1:8b only"
    echo "  2. amd64 + llama-3.1:8b only"
    echo "  3. arm64 + llava-llama3:8b only"
    echo "  4. amd64 + llava-llama3:8b only"
    echo "  5. arm64 + both models"
    echo "  6. amd64 + both models"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            if [[ $# -lt 2 ]] || [[ "$2" =~ ^-- ]]; then
                echo -e "${RED}Error: --version requires a value${NC}"
                exit 1
            fi
            VERSION="$2"
            shift 2
            ;;
        --platform)
            if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^(amd64|arm64|both)$ ]]; then
                echo -e "${RED}Error: --platform requires a value (amd64, arm64, or both)${NC}"
                exit 1
            fi
            if [[ "$2" == "both" ]]; then
                BUILD_PLATFORMS=("arm64" "amd64")
            else
                BUILD_PLATFORMS=("$2")
            fi
            shift 2
            ;;
        --models)
            if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^(llama31|llava|both|all)$ ]]; then
                echo -e "${RED}Error: --models requires a value (llama31, llava, both, or all)${NC}"
                exit 1
            fi
            BUILD_ALL=false
            case "$2" in
                "llama31")
                    MODEL_COMBINATIONS=("llama-3.1:8b|llama31-only")
                    ;;
                "llava")
                    MODEL_COMBINATIONS=("llava-llama3:8b|llava-only")
                    ;;
                "both")
                    MODEL_COMBINATIONS=("llama-3.1:8b,llava-llama3:8b|both-models")
                    ;;
                "all")
                    BUILD_ALL=true
                    ;;
            esac
            shift 2
            ;;
        --registry)
            if [[ $# -lt 2 ]] || [[ "$2" =~ ^-- ]]; then
                echo -e "${RED}Error: --registry requires a value${NC}"
                exit 1
            fi
            REGISTRY="$2"
            shift 2
            ;;
        --push)
            PUSH_TO_REGISTRY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Show runtime information
show_runtime_info

# Function to build a single ollama image
build_ollama_image() {
    local platform="$1"
    local models="$2"
    local model_tag="$3"
    local image_tag="ollama-$model_tag:$platform-$VERSION"
    local registry_tag="$REGISTRY/$image_tag"
    
    echo -e "${CYAN}🔨 Building Ollama image: $image_tag${NC}"
    echo -e "${YELLOW}  Platform: $platform${NC}"
    echo -e "${YELLOW}  Models: $models${NC}"
    echo -e "${YELLOW}  Tag: $image_tag${NC}"
    echo ""
    
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${PURPLE}[DRY RUN] Would build image with:${NC}"
        echo -e "${PURPLE}  Dockerfile: engine/Dockerfile.ollama-models${NC}"
        echo -e "${PURPLE}  Platform: linux/$platform${NC}"
        echo -e "${PURPLE}  Models: $models${NC}"
        echo -e "${PURPLE}  Tag: $image_tag${NC}"
        echo ""
        return 0
    fi
    
    # Build the image
    local build_args="--build-arg PLATFORM=$platform --build-arg MODELS=\"$models\" --build-arg VERSION=$VERSION"
    
    if build_image "engine/Dockerfile.ollama-models" "$image_tag" "$platform" "$build_args" "false"; then
        echo -e "${GREEN}✅ Successfully built: $image_tag${NC}"
        
        # Show image info
        echo -e "${CYAN}📊 Image details:${NC}"
        $CONTAINER_RUNTIME images "$image_tag" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        echo ""
        
        # Handle registry push
        if [ "$PUSH_TO_REGISTRY" = "true" ]; then
            push_decision="y"
        else
            echo -e "${CYAN}🎯 Image built successfully for $platform!${NC}"
            echo -e "${YELLOW}📦 Local image: $image_tag${NC}"
            echo -e "${YELLOW}🌐 Registry target: $registry_tag${NC}"
            echo ""
            echo -e "${BLUE}ℹ️  This image contains: $models${NC}"
            read -p "Do you want to push this image to the registry? (y/N): " -n 1 -r
            echo ""
            push_decision="$REPLY"
        fi
        
        if [[ $push_decision =~ ^[Yy]$ ]]; then
            echo -e "${CYAN}📤 Tagging and pushing to registry...${NC}"
            $CONTAINER_RUNTIME tag "$image_tag" "$registry_tag"
            
            if $CONTAINER_RUNTIME push "$registry_tag"; then
                echo -e "${GREEN}✅ Successfully pushed: $registry_tag${NC}"
            else
                echo -e "${RED}❌ Failed to push to registry. Please check your credentials.${NC}"
                registry_login_help "$REGISTRY"
                return 1
            fi
        else
            echo -e "${YELLOW}⏭️  Skipping registry push. Image available locally.${NC}"
            echo -e "${BLUE}🔧 You can manually push later with:${NC}"
            echo -e "${BLUE}   $CONTAINER_RUNTIME tag $image_tag $registry_tag${NC}"
            echo -e "${BLUE}   $CONTAINER_RUNTIME push $registry_tag${NC}"
        fi
        
        echo ""
        
    else
        echo -e "${RED}❌ Build failed for: $image_tag${NC}"
        return 1
    fi
}

# Main build function
main() {
    echo -e "${CYAN}🚀 Starting Sasya Chikitsa Ollama Multi-Model Build${NC}"
    echo ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo -e "${YELLOW}  Version: $VERSION${NC}"
    echo -e "${YELLOW}  Platforms: ${BUILD_PLATFORMS[*]}${NC}"
    echo -e "${YELLOW}  Registry: $REGISTRY${NC}"
    echo -e "${YELLOW}  Auto-push: $PUSH_TO_REGISTRY${NC}"
    echo -e "${YELLOW}  Dry run: $DRY_RUN${NC}"
    echo ""
    
    # Calculate total builds
    local total_builds=$((${#BUILD_PLATFORMS[@]} * ${#MODEL_COMBINATIONS[@]}))
    echo -e "${CYAN}📋 Build Matrix: $total_builds total images${NC}"
    echo ""
    
    local build_count=0
    local success_count=0
    local failed_builds=()
    
    # Build all combinations
    for platform in "${BUILD_PLATFORMS[@]}"; do
        for model_combo in "${MODEL_COMBINATIONS[@]}"; do
            build_count=$((build_count + 1))
            
            # Parse model combination (format: models|tag)
            IFS='|' read -r models model_tag <<< "$model_combo"
            
            echo -e "${PURPLE}🔄 Build $build_count/$total_builds${NC}"
            
            if build_ollama_image "$platform" "$models" "$model_tag"; then
                success_count=$((success_count + 1))
            else
                failed_builds+=("$platform-$model_tag")
            fi
            
            # Add separator between builds
            if [ $build_count -lt $total_builds ]; then
                echo -e "${CYAN}────────────────────────────────────────${NC}"
                echo ""
            fi
        done
    done
    
    # Build summary
    echo -e "${CYAN}🎉 Build Summary${NC}"
    echo -e "${GREEN}  ✅ Successful builds: $success_count/$total_builds${NC}"
    
    if [ ${#failed_builds[@]} -gt 0 ]; then
        echo -e "${RED}  ❌ Failed builds: ${#failed_builds[@]}${NC}"
        for failed in "${failed_builds[@]}"; do
            echo -e "${RED}     • $failed${NC}"
        done
    fi
    
    echo ""
    echo -e "${CYAN}📦 Built Images:${NC}"
    $CONTAINER_RUNTIME images | grep "ollama-" | head -20
    
    if [ "$DRY_RUN" = "false" ] && [ $success_count -gt 0 ]; then
        echo ""
        echo -e "${BLUE}🔧 Useful Commands:${NC}"
        echo -e "${BLUE}  • List all ollama images: $CONTAINER_RUNTIME images | grep ollama${NC}"
        echo -e "${BLUE}  • Run an image: $CONTAINER_RUNTIME run -it --rm -p 11434:11434 ollama-llama31-only:arm64-$VERSION${NC}"
        echo -e "${BLUE}  • Test API: curl http://localhost:11434/api/version${NC}"
        echo -e "${BLUE}  • List models in container: $CONTAINER_RUNTIME exec <container> ollama list${NC}"
    fi
    
    if [ ${#failed_builds[@]} -gt 0 ]; then
        exit 1
    fi
}

# Change to engine directory for build context
cd engine || {
    echo -e "${RED}Error: engine directory not found${NC}"
    exit 1
}

# Run main function
main

echo -e "${GREEN}🎯 Build script completed!${NC}"
