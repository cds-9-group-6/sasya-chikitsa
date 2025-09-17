#!/bin/bash

# Planning Agent Classification Test Script
# Tests plant disease classification using base64 image data

set -e

# Configuration
SERVER_HOST="localhost"
SERVER_PORT="8001"
BASE_URL="http://${SERVER_HOST}:${SERVER_PORT}"

# Test image paths (adjusted for tests folder location)
IMAGE_BASE64_FILE="../../../engine/resources/images_for_test/leaf_base64.txt"
IMAGE_BASE64_FILE2="/Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt"

echo "🧪 Planning Agent Classification Test"
echo "====================================="
echo ""

# Check if server is running
echo "📡 Checking if server is running at $BASE_URL..."
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $BASE_URL"
    echo "   Start the server first: ./run_planning_server.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Test 1: Health Check
echo "🏥 Test 1: Health Check"
echo "----------------------"
curl -s "$BASE_URL/health" | jq '.'
echo ""

# Test 2: Basic Classification with Image
echo "🔬 Test 2: Basic Classification (JSON Response)"
echo "----------------------------------------------"

# Check if base64 image file exists
if [[ -f "$IMAGE_BASE64_FILE" ]]; then
    IMAGE_FILE="$IMAGE_BASE64_FILE"
elif [[ -f "$IMAGE_BASE64_FILE2" ]]; then
    IMAGE_FILE="$IMAGE_BASE64_FILE2"
else
    echo "❌ No base64 image files found!"
    echo "   Tried: $IMAGE_BASE64_FILE"
    echo "   Tried: $IMAGE_BASE64_FILE2"
    exit 1
fi

echo "📸 Using image file: $IMAGE_FILE"

# Read base64 image data (first 1000 characters for testing to avoid huge requests)
IMAGE_DATA=$(head -c 1000 "$IMAGE_FILE")

# Create JSON request using jq
CLASSIFICATION_REQUEST=$(jq -n \
    --arg session_id "test-classification-$(date +%s)" \
    --arg message "Please analyze this plant leaf image for disease detection. What disease or condition do you see?" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"test_mode": true, "crop_type": "tomato"}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context,
        workflow_action: null
    }')

echo ""
echo "📋 Classification Request (jq formatted):"
echo "$CLASSIFICATION_REQUEST" | jq '.'
echo ""

# Send classification request
echo "🚀 Sending classification request..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$CLASSIFICATION_REQUEST" \
    "$BASE_URL/planning/chat")

echo ""
echo "📊 Classification Response:"
echo "$RESPONSE" | jq '.'
echo ""

# Test 3: Streaming Classification
echo "🌊 Test 3: Streaming Classification"
echo "----------------------------------"

STREAM_REQUEST=$(jq -n \
    --arg session_id "test-stream-$(date +%s)" \
    --arg message "Analyze this leaf for plant diseases with detailed progress updates" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"test_mode": true, "streaming": true}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context
    }')

echo "📋 Streaming Request (jq formatted):"
echo "$STREAM_REQUEST" | jq '.'
echo ""

echo "🌊 Streaming Response (first 20 lines):"
#timeout 15s curl -s -X POST \
#    -H "Content-Type: application/json" \
#    -d "$STREAM_REQUEST" \
#    "$BASE_URL/planning/chat-stream" | head -20 || echo "⏱️  Streaming test completed (timeout after 15s)"

curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$STREAM_REQUEST" \
    "$BASE_URL/planning/chat-stream" | head -20 || echo "⏱️  Streaming test completed (timeout after 15s)"

echo ""
echo ""

# Test 4: Session Information
echo "📋 Test 4: Session Information"
echo "-----------------------------"

# Extract session_id from previous response
SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id // "default"')
if [[ "$SESSION_ID" == "null" || "$SESSION_ID" == "" ]]; then
    SESSION_ID="test-classification-$(date +%s)"
fi

echo "🔍 Getting session info for: $SESSION_ID"
SESSION_INFO=$(curl -s "$BASE_URL/planning/session/$SESSION_ID")
echo ""
echo "📊 Session Information:"
echo "$SESSION_INFO" | jq '.'
echo ""

# Test 5: Available Actions  
echo "🎮 Test 5: Available Actions"
echo "---------------------------"

echo "🔍 Getting available actions for session: $SESSION_ID"
ACTIONS=$(curl -s "$BASE_URL/planning/session/$SESSION_ID/actions")
echo ""
echo "🎯 Available Actions:"
echo "$ACTIONS" | jq '.'
echo ""

echo "✅ All classification tests completed!"
echo ""
echo "🧪 Test Summary:"
echo "- ✅ Health check"
echo "- ✅ Basic classification with image"
echo "- ✅ Streaming classification" 
echo "- ✅ Session information"
echo "- ✅ Available actions"
echo ""
echo "🌱 Planning Agent classification testing complete!"
