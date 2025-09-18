#!/bin/bash

# FSM Agent Chat Stream Endpoint Test Script
# Tests the agricultural AI chat streaming endpoint with images and context

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
FSM_SERVER_URL="${FSM_SERVER_URL:-http://localhost:8080}"
CHAT_STREAM_ENDPOINT="$FSM_SERVER_URL/sasya-chikitsa/chat-stream"

# Check if chat stream endpoint is accessible
echo -e "${YELLOW}🔍 Checking chat stream endpoint connectivity...${NC}"
if ! curl -s --connect-timeout 5 -X OPTIONS "$CHAT_STREAM_ENDPOINT" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to chat stream endpoint at $CHAT_STREAM_ENDPOINT${NC}"
    echo -e "${RED}   Please verify the endpoint is available${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Chat stream endpoint is accessible${NC}"

SESSION_ID="test-session-$(date +%s)"
IMAGES_DIR="${IMAGES_DIR:-$(pwd)/engine/resources/images_for_test}"

# Check if images directory exists
if [[ ! -d "$IMAGES_DIR" ]]; then
    echo -e "${RED}❌ Images directory not found: $IMAGES_DIR${NC}"
    echo -e "${RED}   Please ensure the images directory exists or set IMAGES_DIR environment variable${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Images directory found: $IMAGES_DIR${NC}"
TEMP_DIR="/tmp/fsm_test_$$"

# Create temp directory
mkdir -p "$TEMP_DIR"

echo -e "${BLUE}🚀 FSM Agent Chat Stream Test Suite${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "Server URL: ${CYAN}$FSM_SERVER_URL${NC}"
echo -e "Session ID: ${CYAN}$SESSION_ID${NC}"
echo -e "Images Dir: ${CYAN}$IMAGES_DIR${NC}"
echo ""

# Function to encode image to base64
encode_image() {
    local image_path="$1"
    if [[ ! -f "$image_path" ]]; then
        echo -e "${RED}❌ Image not found: $image_path${NC}" >&2
        return 1
    fi
    
    # Get file extension and create data URL
    local ext="${image_path##*.}"
    local mime_type
    case "${ext,,}" in
        jpg|jpeg) mime_type="image/jpeg" ;;
        png) mime_type="image/png" ;;
        *) mime_type="image/jpeg" ;;
    esac
    
    local base64_data=$(base64 -i "$image_path" | tr -d '\n')
    echo "data:${mime_type};base64,${base64_data}"
}

# Function to create agricultural context
create_context() {
    local plant_type="$1"
    local location="$2"
    local season="$3"
    local growth_stage="$4"
    local farm_size="$5"
    
    cat <<EOF
{
    "plant_type": "$plant_type",
    "location": "$location",
    "season": "$season",
    "growth_stage": "$growth_stage",
    "farm_size": "$farm_size",
    "farming_experience": "5+ years",
    "farming_type": "Sustainable Agriculture",
    "irrigation_method": "Drip Irrigation",
    "soil_type": "Loamy",
    "previous_diseases": []
}
EOF
}

# Function to send chat request and handle SSE stream
send_chat_request() {
    local message="$1"
    local context="$2"
    local image_data="$3"
    local test_name="$4"
    
    echo -e "${YELLOW}📤 Test: $test_name${NC}"
    echo -e "Message: ${CYAN}$message${NC}"
    
    # Create request payload
    local payload=$(cat <<EOF
{
    "message": "$message",
    "session_id": "$SESSION_ID",
    "context": $context$([ -n "$image_data" ] && echo ",
    \"image\": \"$image_data\"" || echo "")
}
EOF
)
    
    # Save payload to temp file for debugging
    echo "$payload" > "$TEMP_DIR/request_${test_name//[^a-zA-Z0-9]/_}.json"
    
    echo -e "${PURPLE}🔄 Sending request...${NC}"
    
    # Send request and handle SSE stream
    local response_file="$TEMP_DIR/response_${test_name//[^a-zA-Z0-9]/_}.txt"
    
    curl -X POST "$CHAT_STREAM_ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Accept: text/event-stream" \
        -d "$payload" \
        --no-buffer \
        -s \
        --max-time 120 \
        --connect-timeout 10 > "$response_file" 2>&1 &
    
    local curl_pid=$!
    
    # Monitor the stream with timeout
    local timeout=60
    local elapsed=0
    
    echo -e "${GREEN}📡 Streaming response:${NC}"
    echo "----------------------------------------"
    
    # Wait for initial response
    sleep 2
    
    while kill -0 $curl_pid 2>/dev/null && [ $elapsed -lt $timeout ]; do
        if [[ -f "$response_file" && -s "$response_file" ]]; then
            # Process SSE events
            tail -n +1 "$response_file" 2>/dev/null | while IFS= read -r line; do
                if [[ $line == data:* ]]; then
                    local event_data="${line#data: }"
                    if [[ $event_data == "{"* ]]; then
                        # Pretty print JSON
                        echo "$event_data" | jq -r '.content // .type // .' 2>/dev/null || echo "$event_data"
                    else
                        echo "$event_data"
                    fi
                elif [[ $line == event:* ]]; then
                    local event_type="${line#event: }"
                    echo -e "${BLUE}[Event: $event_type]${NC}"
                fi
            done
            break
        fi
        sleep 1
        ((elapsed++))
    done
    
    # Clean up curl process
    kill $curl_pid 2>/dev/null || true
    wait $curl_pid 2>/dev/null || true
    
    echo "----------------------------------------"
    
    if [[ -f "$response_file" && -s "$response_file" ]]; then
        echo -e "${GREEN}✅ Response received successfully${NC}"
        
        # Check for errors in response
        if grep -q "error" "$response_file" 2>/dev/null; then
            echo -e "${RED}⚠️  Error detected in response:${NC}"
            grep "error" "$response_file" | head -3
        fi
        
        # Check for attention overlay
        if grep -q "attention_overlay" "$response_file" 2>/dev/null; then
            echo -e "${CYAN}🎯 Attention overlay detected in response${NC}"
        fi
        
        # Check for streaming completion
        if grep -q "COMPLETE\|FINISHED" "$response_file" 2>/dev/null; then
            echo -e "${GREEN}✅ Streaming completed successfully${NC}"
        fi
    else
        echo -e "${RED}❌ No response received${NC}"
        return 1
    fi
    
    echo ""
}

# Function to check server health
check_server_health() {
    echo -e "${YELLOW}🏥 Checking server health...${NC}"
    
    local health_url="$FSM_SERVER_URL/health"
    if curl -s --connect-timeout 5 "$health_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Server is not responding${NC}"
        echo -e "${YELLOW}💡 Please start the FSM server:${NC}"
        echo -e "   cd engine/fsm_agent && python3 run_fsm_server.py"
        return 1
    fi
}

# Test scenarios
run_tests() {
    echo -e "${BLUE}🧪 Running Test Scenarios${NC}"
    echo ""
    
    # Test 1: Simple text query without image
    local context1=$(create_context "Tomato" "Maharashtra, India" "Kharif" "Flowering" "2 acres")
    send_chat_request \
        "My tomato plants have yellowing leaves. What could be the problem?" \
        "$context1" \
        "" \
        "Simple Text Query"
    
    sleep 3
    
    # Test 2: Image classification with tomato disease
    if [[ -f "$IMAGES_DIR/tomato_mosaic_virus.png" ]]; then
        local tomato_image=$(encode_image "$IMAGES_DIR/tomato_mosaic_virus.png")
        local context2=$(create_context "Tomato" "Karnataka, India" "Summer" "Vegetative" "5 acres")
        send_chat_request \
            "Please analyze this tomato plant image and tell me what disease it has." \
            "$context2" \
            "$tomato_image" \
            "Tomato Disease Classification"
        
        sleep 5
    else
        echo -e "${YELLOW}⚠️  Tomato test image not found, skipping image test${NC}"
    fi
    
    # Test 3: Apple disease classification
    if [[ -f "$IMAGES_DIR/apple_alternaria_Early_blight_multi_leaves_1.jpeg" ]]; then
        local apple_image=$(encode_image "$IMAGES_DIR/apple_alternaria_Early_blight_multi_leaves_1.jpeg")
        local context3=$(create_context "Apple" "Himachal Pradesh, India" "Summer" "Fruiting" "10 acres")
        send_chat_request \
            "I found these spots on my apple leaves. Can you identify the disease and suggest treatment?" \
            "$context3" \
            "$apple_image" \
            "Apple Disease Diagnosis"
        
        sleep 5
    fi
    
    # Test 4: Potato health check
    if [[ -f "$IMAGES_DIR/potato_healthy_multi_leaves_1.JPG" ]]; then
        local potato_image=$(encode_image "$IMAGES_DIR/potato_healthy_multi_leaves_1.JPG")
        local context4=$(create_context "Potato" "Punjab, India" "Rabi" "Maturation" "25 acres")
        send_chat_request \
            "Are my potato plants healthy? Please analyze this image." \
            "$context4" \
            "$potato_image" \
            "Potato Health Assessment"
        
        sleep 5
    fi
    
    # Test 5: Complex agricultural advice query
    local context5=$(create_context "Tomato" "Tamil Nadu, India" "Winter" "Transplanting" "1.5 acres")
    send_chat_request \
        "I'm planning to grow tomatoes in winter season. What are the best practices for pest management and fertilization in Tamil Nadu climate?" \
        "$context5" \
        "" \
        "Agricultural Advisory"
    
    sleep 3
    
    # Test 6: Follow-up question in same session
    send_chat_request \
        "What about organic alternatives for pest control?" \
        "$context5" \
        "" \
        "Follow-up Query"
}

# Performance test
run_performance_test() {
    echo -e "${BLUE}⚡ Performance Test${NC}"
    echo "Testing concurrent requests and response times..."
    
    local context=$(create_context "Tomato" "Kerala, India" "Monsoon" "Flowering" "3 acres")
    local start_time=$(date +%s.%N)
    
    send_chat_request \
        "Quick test: What are common tomato diseases in monsoon?" \
        "$context" \
        "" \
        "Performance Test"
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l)
    
    echo -e "${CYAN}⏱️  Response time: ${duration}s${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}Starting FSM Agent Chat Stream Tests...${NC}"
    echo ""
    
    # Check if server is running
    if ! check_server_health; then
        exit 1
    fi
    
    echo ""
    
    # Check if images directory exists
    if [[ ! -d "$IMAGES_DIR" ]]; then
        echo -e "${YELLOW}⚠️  Images directory not found: $IMAGES_DIR${NC}"
        echo -e "${YELLOW}   Some image tests will be skipped${NC}"
    else
        echo -e "${GREEN}✅ Images directory found: $IMAGES_DIR${NC}"
        echo -e "${CYAN}Available test images: $(ls "$IMAGES_DIR" | wc -l)${NC}"
    fi
    
    echo ""
    
    # Run tests
    run_tests
    
    echo ""
    
    # Run performance test
    run_performance_test
    
    echo ""
    echo -e "${GREEN}🎉 All tests completed!${NC}"
    echo -e "${CYAN}📁 Test artifacts saved in: $TEMP_DIR${NC}"
    echo -e "${YELLOW}💡 You can review request/response files for debugging${NC}"
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    # Keep temp files for debugging
    echo -e "${CYAN}Test files preserved in: $TEMP_DIR${NC}"
}

# Set up cleanup trap
trap cleanup EXIT

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        missing_deps+=("jq")
    fi
    
    if ! command -v base64 >/dev/null 2>&1; then
        missing_deps+=("base64")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Please install missing dependencies and try again${NC}"
        exit 1
    fi
}

# Check dependencies first
check_dependencies

# Run main function
main

echo -e "${GREEN}✨ FSM Agent Chat Stream Test Complete! ✨${NC}"
