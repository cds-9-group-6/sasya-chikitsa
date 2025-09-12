#!/bin/bash

# Test Fixed Workflow - CNN Classification should now trigger
# This script tests the fixed IntentCaptureComponent

echo "🔧 Testing Fixed Planning Agent Workflow"
echo "========================================"
echo ""

# Configuration
SERVER_URL="http://localhost:8001"
SESSION_ID="fixed-workflow-test-$(date +%s)"

# Check if server is running
if ! curl -s "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: ./run_planning_server.sh"
    exit 1
fi

echo "✅ Server is running"
echo "🧪 Testing fixed workflow with context parameter..."
echo ""

# Load image data  
IMAGE_DATA=""
IMAGE_FILE_1="/Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt"
IMAGE_FILE_2="/Users/aathalye/dev/sasya-chikitsa/engine/resources/images_for_test/leaf_base64.txt"

if [[ -f "$IMAGE_FILE_1" ]] && [[ -s "$IMAGE_FILE_1" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE_1" | tr -d '\n\r')
    IMAGE_SOURCE="$IMAGE_FILE_1"
elif [[ -f "$IMAGE_FILE_2" ]] && [[ -s "$IMAGE_FILE_2" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE_2" | tr -d '\n\r')
    IMAGE_SOURCE="$IMAGE_FILE_2"
else
    # Fallback sample image
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="
    IMAGE_SOURCE="Sample PNG"
fi

echo "📸 Using image: $IMAGE_SOURCE (${#IMAGE_DATA} chars)"
echo ""

# Create request with proper context (this should now work!)
FIXED_REQUEST=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this plant leaf image for disease detection. Provide detailed diagnosis and treatment recommendations." \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{
        "crop_type": "tomato",
        "location": "California, USA", 
        "season": "summer",
        "test_mode": true,
        "expects_classification": true
    }' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context,
        workflow_action: null
    }')

echo "📋 Request with context:"
echo "$FIXED_REQUEST" | jq '. | {session_id, context, message: (.message | .[0:60] + "..."), image_size: (.image_b64 | length)}'
echo ""

echo "🚀 Sending request to trigger CNN classification..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$FIXED_REQUEST" \
    "$SERVER_URL/planning/chat")

echo ""
echo "📊 Response Analysis:"
echo "===================="

if [[ -n "$RESPONSE" ]]; then
    # Check current state
    CURRENT_STATE=$(echo "$RESPONSE" | jq -r '.current_state // "unknown"')
    echo "🔄 Current State: $CURRENT_STATE"
    
    # Check for success
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    echo "✅ Request Success: $SUCCESS"
    
    # Check response content for classification indicators
    RESPONSE_TEXT=$(echo "$RESPONSE" | jq -r '.response // "no response"')
    
    echo ""
    echo "🔍 Classification Indicators:"
    if [[ "$RESPONSE_TEXT" == *"classification"* ]] || [[ "$RESPONSE_TEXT" == *"CNN"* ]]; then
        echo "   ✅ 'classification' or 'CNN' found in response"
    else
        echo "   ❌ No 'classification' or 'CNN' found"
    fi
    
    if [[ "$RESPONSE_TEXT" == *"confidence"* ]] || [[ "$RESPONSE_TEXT" == *"disease"* ]]; then
        echo "   ✅ 'confidence' or 'disease' found in response"  
    else
        echo "   ❌ No 'confidence' or 'disease' found"
    fi
    
    if [[ "$RESPONSE_TEXT" == *"attention"* ]] || [[ "$RESPONSE_TEXT" == *"visualization"* ]]; then
        echo "   ✅ 'attention' or 'visualization' found in response"
    else
        echo "   ❌ No attention/visualization found"
    fi
    
    if [[ "$CURRENT_STATE" == "classification" ]] || [[ "$CURRENT_STATE" == "prescription" ]]; then
        echo "   ✅ Workflow reached classification/prescription state"
    else
        echo "   ⚠️  Workflow state: $CURRENT_STATE (expected: classification or prescription)"
    fi
    
    echo ""
    echo "📄 Full Response:"
    echo "$RESPONSE" | jq '.'
    
    echo ""
    echo "📝 Response Summary:"
    echo "$(echo "$RESPONSE_TEXT" | head -c 200)..."
    
else
    echo "❌ No response received"
fi

echo ""
echo "🧪 Test completed!"
echo "   Session ID: $SESSION_ID"
echo "   Expected: CNN classification should be triggered"
echo "   Check response above for classification indicators"
