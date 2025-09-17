#!/bin/bash

# 🎯 Attention Overlay Streaming Test
# ===================================
# Tests that the attention overlay base64 data is properly streamed to client

set -e

echo "🎯 Attention Overlay Streaming Test"
echo "=================================="

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: cd .. && ./run_planning_server.sh"
    exit 1
fi

echo "✅ Server is running"

# Load test image
echo "📸 Loading test image..."
IMAGE_FILE="/Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt"

if [[ -f "$IMAGE_FILE" ]] && [[ -s "$IMAGE_FILE" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE" | tr -d '\n\r')
    echo "✅ Loaded image: ${#IMAGE_DATA} characters"
else
    echo "⚠️  Using fallback test image"
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="
fi

# Create test request
echo "🔬 Testing attention overlay streaming..."

SESSION_ID="attention-test-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this plant disease and show attention overlay" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer"}' \
    '{session_id: $session_id, message: $message, image_b64: $image_b64, context: $context}')

echo "📡 Sending streaming request..."

# Capture streaming response
RESPONSE_FILE="/tmp/attention_overlay_response_${SESSION_ID}.txt"
curl -s -X POST "$SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA" > "$RESPONSE_FILE"

# Check if response contains attention overlay
echo ""
echo "🔍 Analyzing response for attention overlay..."

if grep -q "ATTENTION_OVERLAY_BASE64:" "$RESPONSE_FILE"; then
    echo "✅ ATTENTION OVERLAY DETECTED in streaming response!"
    
    # Extract and validate the attention overlay data
    OVERLAY_DATA=$(grep "ATTENTION_OVERLAY_BASE64:" "$RESPONSE_FILE" | head -1 | sed 's/data: ATTENTION_OVERLAY_BASE64://')
    OVERLAY_LENGTH=${#OVERLAY_DATA}
    
    echo "   📊 Attention overlay length: $OVERLAY_LENGTH characters"
    echo "   🔤 First 100 characters: ${OVERLAY_DATA:0:100}..."
    
    if [[ $OVERLAY_LENGTH -gt 1000 ]]; then
        echo "   ✅ Attention overlay data appears valid (sufficient length)"
        echo ""
        echo "🎉 SUCCESS: Attention overlay streaming is working correctly!"
    else
        echo "   ⚠️  Warning: Attention overlay data seems too short"
    fi
    
else
    echo "❌ NO ATTENTION OVERLAY found in streaming response"
    echo ""
    echo "📄 Response preview:"
    head -10 "$RESPONSE_FILE"
fi

echo ""
echo "🎯 Attention overlay streaming test completed!"
