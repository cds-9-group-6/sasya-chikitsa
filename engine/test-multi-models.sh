#!/bin/bash

# Test script for Ollama Multi-Model container
# Tests both llama3.1:8b (text) and llava-llama3:8b (vision) models

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
CONTAINER_IMAGE="${1:-localhost/ollama-multi-model:linux-amd64-v1.0}"

echo -e "${BLUE}🧪 Testing Ollama Multi-Model Container${NC}"
echo -e "${BLUE}Image: ${CONTAINER_IMAGE}${NC}"
echo -e "${BLUE}Ollama URL: ${OLLAMA_URL}${NC}"
echo ""

# Function to wait for Ollama to be ready
wait_for_ollama() {
    echo -e "${YELLOW}⏳ Waiting for Ollama to be ready...${NC}"
    for i in {1..30}; do
        if curl -s -f "${OLLAMA_URL}/api/version" > /dev/null; then
            echo -e "${GREEN}✅ Ollama is ready!${NC}"
            return 0
        fi
        sleep 2
        echo -n "."
    done
    echo -e "${RED}❌ Ollama failed to start within 60 seconds${NC}"
    return 1
}

# Function to test text model
test_text_model() {
    echo ""
    echo -e "${BLUE}📝 Testing Text AI (llama3.1:8b)...${NC}"
    
    local response=$(curl -s -X POST "${OLLAMA_URL}/api/generate" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "llama3.1:8b",
            "prompt": "What is the best organic treatment for tomato blight disease? Give a brief answer.",
            "stream": false
        }')
    
    if echo "$response" | grep -q "response"; then
        echo -e "${GREEN}✅ Text AI working!${NC}"
        echo -e "${BLUE}Response preview:${NC}"
        echo "$response" | grep -o '"response":"[^"]*' | cut -d'"' -f4 | head -c 200
        echo "..."
        return 0
    else
        echo -e "${RED}❌ Text AI test failed${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Function to test vision model with a sample image
test_vision_model() {
    echo ""
    echo -e "${BLUE}👁️ Testing Vision AI (llava-llama3:8b)...${NC}"
    
    # Simple 1x1 white pixel as test image (base64: iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==)
    local test_image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    local response=$(curl -s -X POST "${OLLAMA_URL}/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"llava-llama3:8b\",
            \"prompt\": \"Describe what you see in this image.\",
            \"images\": [\"${test_image}\"],
            \"stream\": false
        }")
    
    if echo "$response" | grep -q "response"; then
        echo -e "${GREEN}✅ Vision AI working!${NC}"
        echo -e "${BLUE}Response preview:${NC}"
        echo "$response" | grep -o '"response":"[^"]*' | cut -d'"' -f4 | head -c 200
        echo "..."
        return 0
    else
        echo -e "${RED}❌ Vision AI test failed${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Function to list available models
list_models() {
    echo ""
    echo -e "${BLUE}📋 Available Models:${NC}"
    
    local response=$(curl -s "${OLLAMA_URL}/api/tags")
    if echo "$response" | grep -q "models"; then
        echo "$response" | jq -r '.models[].name' 2>/dev/null || echo "$response"
    else
        echo -e "${YELLOW}⚠️  Could not retrieve model list${NC}"
        echo "Response: $response"
    fi
}

# Function to get system info
get_system_info() {
    echo ""
    echo -e "${BLUE}ℹ️  System Information:${NC}"
    
    local response=$(curl -s "${OLLAMA_URL}/api/version")
    if echo "$response" | grep -q "version"; then
        echo "Ollama version: $(echo "$response" | grep -o '"version":"[^"]*' | cut -d'"' -f4)"
    fi
}

# Main test function
main() {
    # Check if we need to start a container
    local start_container=false
    if [[ "$OLLAMA_URL" == "http://localhost:11434" ]]; then
        if ! curl -s -f "${OLLAMA_URL}/api/version" > /dev/null; then
            start_container=true
        fi
    fi
    
    local container_id=""
    
    if [[ "$start_container" == "true" ]]; then
        echo -e "${BLUE}🚀 Starting test container...${NC}"
        
        # Check if image exists
        if ! podman image exists "$CONTAINER_IMAGE" && ! docker image inspect "$CONTAINER_IMAGE" > /dev/null 2>&1; then
            echo -e "${RED}❌ Image not found: $CONTAINER_IMAGE${NC}"
            echo -e "${YELLOW}💡 Build it first: ./engine/build-cross-platform.sh --version v1.0${NC}"
            exit 1
        fi
        
        # Start container
        if command -v podman &> /dev/null; then
            container_id=$(podman run -d -p 11434:11434 "$CONTAINER_IMAGE")
        elif command -v docker &> /dev/null; then
            container_id=$(docker run -d -p 11434:11434 "$CONTAINER_IMAGE")
        else
            echo -e "${RED}❌ No container runtime found (podman or docker)${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Container started: $container_id${NC}"
    fi
    
    # Wait for Ollama to be ready
    if ! wait_for_ollama; then
        exit 1
    fi
    
    # Get system info
    get_system_info
    
    # List models
    list_models
    
    # Test both models
    local text_result=0
    local vision_result=0
    
    test_text_model || text_result=1
    test_vision_model || vision_result=1
    
    # Results summary
    echo ""
    echo -e "${BLUE}📊 Test Results:${NC}"
    
    if [[ $text_result -eq 0 ]]; then
        echo -e "${GREEN}  ✅ Text AI (llama3.1:8b): PASSED${NC}"
    else
        echo -e "${RED}  ❌ Text AI (llama3.1:8b): FAILED${NC}"
    fi
    
    if [[ $vision_result -eq 0 ]]; then
        echo -e "${GREEN}  ✅ Vision AI (llava-llama3:8b): PASSED${NC}"
    else
        echo -e "${RED}  ❌ Vision AI (llava-llama3:8b): FAILED${NC}"
    fi
    
    # Cleanup
    if [[ -n "$container_id" ]]; then
        echo ""
        echo -e "${BLUE}🗑️  Cleaning up test container...${NC}"
        
        if command -v podman &> /dev/null; then
            podman stop "$container_id" > /dev/null
            podman rm "$container_id" > /dev/null
        elif command -v docker &> /dev/null; then
            docker stop "$container_id" > /dev/null
            docker rm "$container_id" > /dev/null
        fi
        
        echo -e "${GREEN}✅ Container cleaned up${NC}"
    fi
    
    # Final result
    if [[ $text_result -eq 0 && $vision_result -eq 0 ]]; then
        echo ""
        echo -e "${GREEN}🎉 All tests passed! Multi-model container is working correctly.${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"
        exit 1
    fi
}

# Show usage if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [IMAGE_NAME]"
    echo ""
    echo "Test script for Ollama multi-model container"
    echo ""
    echo "Arguments:"
    echo "  IMAGE_NAME    Docker image to test (default: localhost/ollama-multi-model:linux-amd64-v1.0)"
    echo ""
    echo "Environment Variables:"
    echo "  OLLAMA_URL    Ollama API URL (default: http://localhost:11434)"
    echo ""
    echo "Examples:"
    echo "  $0                                              # Test default local image"
    echo "  $0 quay.io/myorg/ollama-multi-model:v1.0      # Test remote image"
    echo "  OLLAMA_URL=http://remote:11434 $0              # Test remote Ollama"
    exit 0
fi

# Run main function
main
