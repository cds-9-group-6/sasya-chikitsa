#!/bin/bash

# Streaming Classification Test with Real Image Data
# Uses base64 image from image_103_base64.txt

set -e

# Configuration
SERVER_URL="http://localhost:8001"
SESSION_ID="streaming-image-test-$(date +%s)"

echo "🌊 Planning Agent Streaming Classification Test with Image"
echo "========================================================="
echo ""

# Image file paths
IMAGE_FILE_1="/Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt"
IMAGE_FILE_2="/Users/aathalye/dev/sasya-chikitsa/engine/images/image_103_base64.txt"  
IMAGE_FILE_3="/Users/aathalye/dev/sasya-chikitsa/engine/resources/images_for_test/leaf_base64.txt"

# Check server availability
echo "📡 Checking server availability..."
if ! curl -s "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: ./run_planning_server.sh"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Find and load image data
echo "📸 Loading image data..."
IMAGE_DATA=""

if [[ -f "$IMAGE_FILE_1" ]] && [[ -s "$IMAGE_FILE_1" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE_1" | tr -d '\n\r')
    IMAGE_SOURCE="$IMAGE_FILE_1"
    echo "✅ Loaded image from: $IMAGE_SOURCE (truncated to 10KB for testing)"
elif [[ -f "$IMAGE_FILE_2" ]] && [[ -s "$IMAGE_FILE_2" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE_2" | tr -d '\n\r')
    IMAGE_SOURCE="$IMAGE_FILE_2"
    echo "✅ Loaded image from: $IMAGE_SOURCE (truncated to 10KB for testing)"
elif [[ -f "$IMAGE_FILE_3" ]] && [[ -s "$IMAGE_FILE_3" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE_3" | tr -d '\n\r')
    IMAGE_SOURCE="$IMAGE_FILE_3"
    echo "✅ Loaded image from: $IMAGE_SOURCE (truncated to 10KB for testing)"
else
    # Fallback: Sample base64 image (1x1 transparent PNG)
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="
    IMAGE_SOURCE="Sample 1x1 PNG (fallback)"
    echo "⚠️  No image files found, using fallback sample image"
fi

echo "📊 Image data size: ${#IMAGE_DATA} characters"
echo "📋 First 50 characters: ${IMAGE_DATA:0:50}..."
echo ""

# Create streaming request with jq
echo "🔧 Creating streaming request..."
STREAM_REQUEST=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Please analyze this plant leaf image for disease detection. Provide detailed diagnosis, confidence levels, and treatment recommendations. Stream the analysis progress." \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{
        "test_mode": true,
        "crop_type": "tomato", 
        "location": "Tamilnadu",
        "season": "summer",
        "growth_stage": "flowering",
        "streaming_requested": true,
        "image_source": "'$IMAGE_SOURCE'"
    }' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context,
        workflow_action: null
    }')

echo "✅ Request created with session ID: $SESSION_ID"
echo ""

# Display the request (truncated for readability)
echo "📋 Streaming Request Structure:"
echo "$STREAM_REQUEST" | jq '. | {session_id, message: (.message | .[0:100] + "..."), image_b64: (.image_b64 | .[0:50] + "..."), context}'
echo ""

echo "🌊 Starting streaming classification..."
echo "======================================"

# Send streaming request
curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$STREAM_REQUEST" \
    "$SERVER_URL/planning/chat-stream"

echo ""
echo ""
echo "✅ Streaming test completed!"
echo ""
echo "📊 Test Summary:"
echo "- Session ID: $SESSION_ID"
echo "- Image Source: $IMAGE_SOURCE"
echo "- Image Data Size: ${#IMAGE_DATA} characters"
echo "- Server: $SERVER_URL"
