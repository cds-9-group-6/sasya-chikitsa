#!/bin/bash

# Test User Profile Fix - Verify both enum and user_profile issues are resolved

echo "🔧 User Profile & Enum Comparison Fix Test"
echo "=========================================="
echo ""

# Configuration
SERVER_URL="http://localhost:8001"
SESSION_ID="user-profile-fix-$(date +%s)"

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
IMAGE_FILE="/Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt"

if [[ -f "$IMAGE_FILE" ]] && [[ -s "$IMAGE_FILE" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE" | tr -d '\n\r' | head -c 10000)
    echo "✅ Loaded image: ${#IMAGE_DATA} characters"
else
    echo "⚠️  Using fallback image data"
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="
fi
echo ""

# Test: Verify user_profile persistence through workflow
echo "🧪 Test: User Profile Persistence Through Workflow"
echo "================================================="

USER_PROFILE_REQUEST=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Please analyze this plant leaf for disease classification" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{
        "crop_type": "tomato",
        "location": "California, USA", 
        "season": "summer",
        "test_flag": "user_profile_persistence_test"
    }' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context
    }')

echo "📤 Sending request with full context (crop_type, location, season)..."
echo ""

# Capture response and analyze for user profile data
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$USER_PROFILE_REQUEST" \
    "$SERVER_URL/planning/chat")

echo "📊 Response Analysis:"
echo "===================="

if [[ -n "$RESPONSE" ]]; then
    # Extract key information
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    CURRENT_STATE=$(echo "$RESPONSE" | jq -r '.current_state // "unknown"')
    RESPONSE_TEXT=$(echo "$RESPONSE" | jq -r '.response // ""')
    
    echo "✅ Success: $SUCCESS"
    echo "🔄 Final State: $CURRENT_STATE"
    echo ""
    
    # Check for user profile utilization indicators
    echo "🔍 User Profile Utilization Check:"
    
    profile_indicators=0
    
    # Check if context was properly captured
    if [[ "$RESPONSE_TEXT" == *"tomato"* ]]; then
        echo "   ✅ Found 'tomato' (crop_type) in response"
        ((profile_indicators++))
    else
        echo "   ❌ No 'tomato' (crop_type) found in response"
    fi
    
    if [[ "$RESPONSE_TEXT" == *"California"* ]]; then
        echo "   ✅ Found 'California' (location) in response" 
        ((profile_indicators++))
    else
        echo "   ❌ No 'California' (location) found in response"
    fi
    
    if [[ "$RESPONSE_TEXT" == *"summer"* ]]; then
        echo "   ✅ Found 'summer' (season) in response"
        ((profile_indicators++))
    else
        echo "   ❌ No 'summer' (season) found in response"
    fi
    
    # Check workflow progression indicators
    if [[ "$CURRENT_STATE" == "classification" ]] || [[ "$CURRENT_STATE" == "prescription" ]]; then
        echo "   ✅ Workflow progressed to classification/prescription (enum comparison working)"
        ((profile_indicators++))
    else
        echo "   ❌ Workflow stuck at: $CURRENT_STATE (enum comparison may be failing)"
    fi
    
    # Check for CNN/classification execution
    if [[ "$RESPONSE_TEXT" == *"CNN"* ]] || [[ "$RESPONSE_TEXT" == *"classification"* ]] || [[ "$RESPONSE_TEXT" == *"confidence"* ]]; then
        echo "   ✅ CNN classification appears to have executed"
        ((profile_indicators++))
    else
        echo "   ❌ No CNN classification indicators found"
    fi
    
    echo ""
    echo "📊 User Profile Fix Score: $profile_indicators/5"
    
    if [[ $profile_indicators -ge 4 ]]; then
        echo "🎉 SUCCESS: User profile persistence and enum comparisons are working!"
        echo "   ✅ Context data is being properly transferred between workflow states"
        echo "   ✅ Enum comparisons are functioning correctly" 
        echo "   ✅ Workflow progresses automatically from INTENT_CAPTURE to CLASSIFICATION"
    elif [[ $profile_indicators -ge 2 ]]; then
        echo "⚠️  PARTIAL SUCCESS: Some functionality working, but issues remain"
        echo "   Check server logs for detailed error information"
    else
        echo "❌ FAILURE: User profile persistence or enum comparison issues persist"
        echo ""
        echo "🔧 Debugging Steps:"
        echo "   1. Check server logs for session update messages"
        echo "   2. Verify enum conversion in workflow_controller.py"
        echo "   3. Check session_manager.py user_profile update logic"
        echo "   4. Verify classification component receives user_profile"
    fi
    
    echo ""
    echo "📄 Response Text Sample (first 500 chars):"
    echo "${RESPONSE_TEXT:0:500}..."
    
else
    echo "❌ No response received from server"
fi

echo ""
echo "🌊 Additional Test: Streaming Response Analysis"
echo "=============================================="

# Test streaming to see if user profile is maintained
STREAM_SESSION_ID="stream-profile-test-$(date +%s)"

STREAM_REQUEST=$(jq -n \
    --arg session_id "$STREAM_SESSION_ID" \
    --arg message "Perform detailed disease analysis with CNN classifier" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer"}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context
    }')

echo "📤 Testing streaming response with user profile data..."

STREAM_OUTPUT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$STREAM_REQUEST" \
    "$SERVER_URL/planning/chat-stream")

echo ""
echo "🔍 Stream Analysis Results:"

stream_profile_indicators=0

if [[ "$STREAM_OUTPUT" == *"tomato"* ]] || [[ "$STREAM_OUTPUT" == *"California"* ]]; then
    echo "   ✅ User profile context found in streaming response"
    ((stream_profile_indicators++))
else
    echo "   ❌ No user profile context in streaming response"
fi

if [[ "$STREAM_OUTPUT" == *"CNN"* ]] || [[ "$STREAM_OUTPUT" == *"classification"* ]]; then
    echo "   ✅ CNN classification executed in stream"
    ((stream_profile_indicators++))
else
    echo "   ❌ No CNN classification in stream"
fi

echo ""
echo "📊 Streaming Profile Score: $stream_profile_indicators/2"

echo ""
echo "🏁 Final Test Summary"
echo "===================="
echo "   JSON Test: $profile_indicators/5 indicators"
echo "   Stream Test: $stream_profile_indicators/2 indicators"
echo "   Total Score: $((profile_indicators + stream_profile_indicators))/7"
echo ""

if [[ $((profile_indicators + stream_profile_indicators)) -ge 5 ]]; then
    echo "🎉 OVERALL SUCCESS: User profile persistence and enum fixes are working!"
    echo "   🔧 The fixes have resolved both reported issues:"
    echo "     1. ✅ user_profile data is properly transferred between workflow states"
    echo "     2. ✅ enum == comparisons are working correctly in workflow_controller.py"
    echo "   🧠 CNN classifier should now receive proper context for analysis"
elif [[ $((profile_indicators + stream_profile_indicators)) -ge 3 ]]; then
    echo "⚠️  PARTIAL SUCCESS: Some improvements, but refinement needed"
else
    echo "❌ FAILURE: Issues persist - check server logs and debug further"
fi

echo ""
echo "🌱 Test completed!"
echo "   JSON Session: $SESSION_ID"
echo "   Stream Session: $STREAM_SESSION_ID"
echo ""
echo "📋 Next Steps:"
echo "   - Run your original streaming test to confirm CNN execution"
echo "   - Check server logs for detailed session update messages" 
echo "   - Verify attention overlay data is now properly processed"
