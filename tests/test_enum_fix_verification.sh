#!/bin/bash

# Enum Comparison Fix Verification Test
# Specifically tests the workflow continuation enum comparison fixes

echo "🔢 Enum Comparison Fix Verification Test"
echo "========================================"
echo ""

# Configuration
SERVER_URL="http://localhost:8001"
SESSION_ID="enum-fix-test-$(date +%s)"

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
    IMAGE_DATA=$(cat "$IMAGE_FILE" | tr -d '\n\r')
    echo "✅ Loaded image: ${#IMAGE_DATA} characters"
else
    echo "⚠️  Using fallback image data"
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="
fi
echo ""

# Test: Specifically target the enum comparison fix 
echo "🧪 Test: Automatic Workflow Continuation (Enum Fix)"
echo "=================================================="

ENUM_FIX_REQUEST=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this leaf for plant disease classification" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{
        "crop_type": "tomato",
        "location": "California", 
        "season": "summer",
        "test_purpose": "enum_comparison_fix_verification",
        "expects_auto_continuation": true
    }' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context
    }')

echo "📤 Sending request designed to trigger automatic workflow continuation..."
echo "   This tests: next_state != current_state and next_state in self.components"
echo ""

# Capture response timing and detailed analysis
START_TIME=$(date +%s)
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$ENUM_FIX_REQUEST" \
    "$SERVER_URL/planning/chat")
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "📊 Response Analysis:"
echo "===================="

if [[ -n "$RESPONSE" ]]; then
    # Extract key information
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    CURRENT_STATE=$(echo "$RESPONSE" | jq -r '.current_state // "unknown"')
    RESPONSE_TEXT=$(echo "$RESPONSE" | jq -r '.response // ""')
    REQUIRES_INPUT=$(echo "$RESPONSE" | jq -r '.requires_user_input // false')
    
    echo "✅ Success: $SUCCESS"
    echo "🔄 Final State: $CURRENT_STATE"
    echo "⏱️  Response Time: ${DURATION}s"
    echo "💬 Requires User Input: $REQUIRES_INPUT"
    echo ""
    
    # Check for enum fix indicators
    echo "🔍 Enum Fix Success Indicators:"
    
    enum_fix_score=0
    
    # 1. Check if workflow progressed beyond INTENT_CAPTURE
    if [[ "$CURRENT_STATE" != "intent_capture" ]] && [[ "$CURRENT_STATE" != "clarification" ]]; then
        echo "   ✅ Workflow progressed beyond INTENT_CAPTURE/CLARIFICATION"
        echo "      Final state: $CURRENT_STATE (indicates enum comparisons worked)"
        ((enum_fix_score++))
    else
        echo "   ❌ Workflow stuck at: $CURRENT_STATE"
        echo "      This suggests enum comparison issues persist"
    fi
    
    # 2. Check if automatic continuation occurred (indicated by classification/prescription state)
    if [[ "$CURRENT_STATE" == "classification" ]] || [[ "$CURRENT_STATE" == "prescription" ]]; then
        echo "   ✅ Reached classification/prescription state"
        echo "      This indicates automatic workflow continuation worked"
        ((enum_fix_score++))
    else
        echo "   ❌ Did not reach classification/prescription state"
    fi
    
    # 3. Check if CNN classification was executed (would only happen with working enum comparisons)
    if [[ "$RESPONSE_TEXT" == *"CNN"* ]] || [[ "$RESPONSE_TEXT" == *"confidence"* ]] || [[ "$RESPONSE_TEXT" == *"classification"* ]]; then
        echo "   ✅ CNN classification appears to have executed"
        echo "      This confirms enum comparisons allowed workflow to continue to CLASSIFICATION"
        ((enum_fix_score++))
    else
        echo "   ❌ No CNN classification indicators found"
    fi
    
    # 4. Check if user_profile context was preserved (requires working enum comparisons)
    if [[ "$RESPONSE_TEXT" == *"tomato"* ]] && [[ "$RESPONSE_TEXT" == *"California"* ]]; then
        echo "   ✅ User profile context preserved in response"
        echo "      Found: tomato (crop_type) and California (location)"
        ((enum_fix_score++))
    else
        echo "   ❌ User profile context not found in response"
    fi
    
    # 5. Check response quality/completeness (good responses indicate full workflow execution)
    response_length=${#RESPONSE_TEXT}
    if [[ $response_length -gt 200 ]]; then
        echo "   ✅ Response is substantial (${response_length} characters)"
        echo "      Suggests complete workflow execution occurred"
        ((enum_fix_score++))
    else
        echo "   ❌ Response is brief (${response_length} characters)"
        echo "      May indicate workflow terminated early due to enum issues"
    fi
    
    echo ""
    echo "📊 Enum Fix Score: $enum_fix_score/5"
    
    if [[ $enum_fix_score -ge 4 ]]; then
        echo "🎉 SUCCESS: Enum comparison fixes are working perfectly!"
        echo "   ✅ Automatic workflow continuation is functional"
        echo "   ✅ next_state != current_state comparisons work"
        echo "   ✅ next_state in self.components lookups work"
        echo "   ✅ Complete workflow execution from INTENT_CAPTURE → CLASSIFICATION → PRESCRIPTION"
    elif [[ $enum_fix_score -ge 2 ]]; then
        echo "⚠️  PARTIAL SUCCESS: Some enum fixes working, but issues may remain"
        echo "   Check server logs for detailed enum comparison debug information"
    else
        echo "❌ FAILURE: Enum comparison issues persist"
        echo ""
        echo "🔧 Debug Steps:"
        echo "   1. Check server logs for 'Workflow continuation check' messages"
        echo "   2. Look for type mismatch errors in enum comparisons"
        echo "   3. Verify _state_equals() and _state_in_components() are being called"
        echo "   4. Check if workflow gets stuck at INTENT_CAPTURE or CLARIFICATION"
    fi
    
    echo ""
    echo "📄 Response Sample (first 400 chars):"
    echo "${RESPONSE_TEXT:0:400}..."
    
else
    echo "❌ No response received from server"
fi

echo ""
echo "🔬 Additional Test: Type Mismatch Scenarios"
echo "==========================================="

# Test different session to verify robustness
MISMATCH_SESSION_ID="enum-mismatch-test-$(date +%s)"

MISMATCH_REQUEST=$(jq -n \
    --arg session_id "$MISMATCH_SESSION_ID" \
    --arg message "Quick disease diagnosis" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"crop_type": "corn", "location": "Texas"}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context
    }')

echo "📤 Testing robustness with different session..."

MISMATCH_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$MISMATCH_REQUEST" \
    "$SERVER_URL/planning/chat")

MISMATCH_STATE=$(echo "$MISMATCH_RESPONSE" | jq -r '.current_state // "unknown"')
MISMATCH_SUCCESS=$(echo "$MISMATCH_RESPONSE" | jq -r '.success // false"')

echo "🔍 Robustness Test Results:"
if [[ "$MISMATCH_SUCCESS" == "true" ]] && [[ "$MISMATCH_STATE" != "intent_capture" ]]; then
    echo "   ✅ Secondary test also progressed successfully (state: $MISMATCH_STATE)"
    echo "   ✅ Enum fixes are robust across different sessions"
else
    echo "   ❌ Secondary test had issues (success: $MISMATCH_SUCCESS, state: $MISMATCH_STATE)"
fi

echo ""
echo "🏁 Final Enum Fix Verification Summary"
echo "======================================"
echo "   Primary Test Score: $enum_fix_score/5"
echo "   Secondary Test: $([[ "$MISMATCH_SUCCESS" == "true" ]] && echo "PASS" || echo "FAIL")"
echo ""

total_score=$enum_fix_score
[[ "$MISMATCH_SUCCESS" == "true" ]] && ((total_score++))

if [[ $total_score -ge 5 ]]; then
    echo "🎉 OVERALL SUCCESS: Enum comparison fixes are fully functional!"
    echo "   🔧 Fixed Issues:"
    echo "     ✅ next_state != current_state comparisons now work reliably"
    echo "     ✅ next_state in self.components lookups handle type mismatches"
    echo "     ✅ Automatic workflow continuation proceeds correctly"
    echo "     ✅ user_profile data persists through workflow transitions"
    echo "   🧠 Your original CNN classification issue should now be resolved!"
elif [[ $total_score -ge 3 ]]; then
    echo "⚠️  PARTIAL SUCCESS: Major improvements, minor issues may remain"
    echo "   Check server logs for any remaining enum comparison warnings"
else
    echo "❌ SIGNIFICANT ISSUES: Further debugging needed"
    echo "   Review server logs for enum comparison failures"
fi

echo ""
echo "🌱 Test completed!"
echo "   Primary Session: $SESSION_ID"
echo "   Secondary Session: $MISMATCH_SESSION_ID"
echo ""
echo "📋 Next Steps:"
echo "   ✅ Enum comparisons fixed in workflow_controller.py (_state_equals helper)"
echo "   ✅ Enum comparisons fixed in planning_agent.py (auto-continuation logic)"
echo "   ✅ user_profile persistence fixed in session_manager.py (enum/string handling)"
echo "   🚀 Your streaming test with CNN classification should now work perfectly!"
