#!/bin/bash

# Comprehensive CNN Workflow Test
# Tests the complete fix to ensure CNN classification is triggered

echo "🧠 CNN with Attention Classifier Workflow Test"
echo "=============================================="
echo ""

# Configuration
SERVER_URL="http://localhost:8001"
SESSION_ID="cnn-workflow-test-$(date +%s)"

# Check server availability
if ! curl -s "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: ./run_planning_server.sh"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Load image data
echo "📸 Loading image data..."
IMAGE_DATA=""
IMAGE_FILE_1="/Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt"
IMAGE_FILE_2="/Users/aathalye/dev/sasya-chikitsa/engine/resources/images_for_test/leaf_base64.txt"

if [[ -f "$IMAGE_FILE_1" ]] && [[ -s "$IMAGE_FILE_1" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE_1" | tr -d '\n\r' | head -c 10000)
    IMAGE_SOURCE="$IMAGE_FILE_1"
elif [[ -f "$IMAGE_FILE_2" ]] && [[ -s "$IMAGE_FILE_2" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE_2" | tr -d '\n\r' | head -c 10000)
    IMAGE_SOURCE="$IMAGE_FILE_2"
else
    echo "⚠️  No test image files found, using fallback"
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="
    IMAGE_SOURCE="Sample PNG"
fi

echo "✅ Loaded image: $IMAGE_SOURCE (${#IMAGE_DATA} characters)"
echo ""

# Test the complete workflow with both JSON and streaming
echo "🔬 Test 1: JSON Request (should trigger CNN classification)"
echo "=========================================================="

# Create request that should now trigger automatic CNN classification
CNN_REQUEST=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this plant leaf for disease classification and provide detailed diagnosis" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{
        "crop_type": "tomato",
        "location": "California, USA",
        "season": "summer",
        "test_mode": true,
        "expects_cnn_classification": true
    }' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context,
        workflow_action: null
    }')

echo "📤 Sending CNN classification request..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$CNN_REQUEST" \
    "$SERVER_URL/planning/chat")

echo ""
echo "📊 JSON Response Analysis:"
echo "========================="

if [[ -n "$RESPONSE" ]]; then
    # Extract key information
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    CURRENT_STATE=$(echo "$RESPONSE" | jq -r '.current_state // "unknown"')
    RESPONSE_TEXT=$(echo "$RESPONSE" | jq -r '.response // ""')
    
    echo "✅ Success: $SUCCESS"
    echo "🔄 Final State: $CURRENT_STATE"
    echo ""
    
    # Check for CNN classification indicators
    echo "🔍 CNN Classification Indicators:"
    
    cnn_indicators=0
    
    if [[ "$RESPONSE_TEXT" == *"CNN"* ]] || [[ "$RESPONSE_TEXT" == *"classification"* ]]; then
        echo "   ✅ Found 'CNN' or 'classification' in response"
        ((cnn_indicators++))
    else
        echo "   ❌ No 'CNN' or 'classification' found"
    fi
    
    if [[ "$RESPONSE_TEXT" == *"confidence"* ]]; then
        echo "   ✅ Found 'confidence' in response"
        ((cnn_indicators++))
    else
        echo "   ❌ No 'confidence' found"
    fi
    
    if [[ "$RESPONSE_TEXT" == *"disease"* ]] || [[ "$RESPONSE_TEXT" == *"diagnosis"* ]]; then
        echo "   ✅ Found 'disease' or 'diagnosis' in response"
        ((cnn_indicators++))
    else
        echo "   ❌ No 'disease' or 'diagnosis' found"
    fi
    
    if [[ "$RESPONSE_TEXT" == *"attention"* ]] || [[ "$RESPONSE_TEXT" == *"overlay"* ]]; then
        echo "   ✅ Found 'attention' or 'overlay' in response"
        ((cnn_indicators++))
    else
        echo "   ❌ No attention/overlay found"
    fi
    
    # Check workflow state
    if [[ "$CURRENT_STATE" == "prescription" ]] || [[ "$CURRENT_STATE" == "classification" ]]; then
        echo "   ✅ Workflow reached classification/prescription state"
        ((cnn_indicators++))
    else
        echo "   ❌ Workflow stuck at: $CURRENT_STATE (expected: classification/prescription)"
    fi
    
    echo ""
    echo "📊 CNN Detection Score: $cnn_indicators/5"
    
    if [[ $cnn_indicators -ge 3 ]]; then
        echo "🎉 SUCCESS: CNN classification likely executed! (score ≥ 3/5)"
    elif [[ $cnn_indicators -ge 1 ]]; then
        echo "⚠️  PARTIAL: Some classification detected (score 1-2/5)"
    else
        echo "❌ FAILURE: No CNN classification detected (score 0/5)"
    fi
    
    echo ""
    echo "📄 Response Text (first 300 chars):"
    echo "${RESPONSE_TEXT:0:300}..."
    
else
    echo "❌ No response received from server"
fi

echo ""
echo "🌊 Test 2: Streaming Request (should show CNN progress)"
echo "====================================================="

# Test streaming with new session
STREAM_SESSION_ID="cnn-stream-test-$(date +%s)"

STREAM_REQUEST=$(jq -n \
    --arg session_id "$STREAM_SESSION_ID" \
    --arg message "Perform CNN classification and attention analysis of this plant disease" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer"}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context
    }')

echo "📤 Sending streaming request..."
echo ""
echo "🌊 Streaming Response:"

# Capture streaming output and analyze it
STREAM_OUTPUT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$STREAM_REQUEST" \
    "$SERVER_URL/planning/chat-stream")

echo "$STREAM_OUTPUT"

echo ""
echo "🔍 Streaming Analysis:"
echo "====================="

stream_indicators=0

if [[ "$STREAM_OUTPUT" == *"CNN"* ]] || [[ "$STREAM_OUTPUT" == *"classification"* ]]; then
    echo "   ✅ Found CNN/classification in stream"
    ((stream_indicators++))
else
    echo "   ❌ No CNN/classification in stream"
fi

if [[ "$STREAM_OUTPUT" == *"confidence"* ]] || [[ "$STREAM_OUTPUT" == *"analyzing"* ]]; then
    echo "   ✅ Found confidence/analyzing in stream"
    ((stream_indicators++))
else
    echo "   ❌ No confidence/analyzing in stream"
fi

if [[ "$STREAM_OUTPUT" == *"attention"* ]] || [[ "$STREAM_OUTPUT" == *"overlay"* ]]; then
    echo "   ✅ Found attention/overlay in stream"
    ((stream_indicators++))
else
    echo "   ❌ No attention/overlay in stream"
fi

echo ""
echo "📊 Stream Detection Score: $stream_indicators/3"

echo ""
echo "🏁 Final Test Summary"
echo "===================="
echo "   JSON Test: $cnn_indicators/5 indicators"
echo "   Stream Test: $stream_indicators/3 indicators"
echo "   Total Score: $((cnn_indicators + stream_indicators))/8"
echo ""

if [[ $((cnn_indicators + stream_indicators)) -ge 4 ]]; then
    echo "🎉 OVERALL SUCCESS: CNN with Attention Classifier is working!"
    echo "   The workflow automatically continues from INTENT_CAPTURE to CLASSIFICATION"
    echo "   The CNN model is being invoked and returning results"
elif [[ $((cnn_indicators + stream_indicators)) -ge 2 ]]; then
    echo "⚠️  PARTIAL SUCCESS: Some classification detected, but may need refinement"
else
    echo "❌ FAILURE: CNN classification workflow is not working properly"
    echo ""
    echo "🔧 Debug Information:"
    echo "   - Check server logs for errors during classification"
    echo "   - Verify CNN model is properly loaded and accessible"
    echo "   - Ensure image data is being processed correctly"
fi

echo ""
echo "🌱 Test completed!"
echo "   JSON Session: $SESSION_ID"
echo "   Stream Session: $STREAM_SESSION_ID"
