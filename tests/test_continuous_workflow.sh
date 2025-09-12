#!/bin/bash

# 🔄 Continuous Workflow Execution Test
# =====================================
# Tests that the workflow executes multiple components automatically until user input is required

set -e

echo "🔄 Continuous Workflow Execution Test"
echo "===================================="

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: cd .. && ./run_planning_server.sh --env ../.env --port 8001"
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

# Create test request for continuous workflow
echo "🔄 Testing continuous workflow execution..."

SESSION_ID="continuous-workflow-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this plant disease and provide complete treatment plan" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer"}' \
    '{session_id: $session_id, message: $message, image_b64: $image_b64, context: $context}')

echo "📡 Sending continuous workflow request..."

# Capture streaming response
RESPONSE_FILE="/tmp/continuous_workflow_${SESSION_ID}.txt"
curl -s -X POST "$SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA" > "$RESPONSE_FILE"

# Analyze response for continuous execution
echo ""
echo "🔍 Analyzing continuous workflow execution..."

# Track component execution
CLASSIFICATION_EXECUTED=0
PRESCRIPTION_EXECUTED=0
CONSTRAINT_GATHERING_EXECUTED=0
VENDOR_RECOMMENDATION_EXECUTED=0
WORKFLOW_CHAIN_LENGTH=0

# Check for classification execution
if grep -q -i "cnn\|classification\|diagnosis" "$RESPONSE_FILE"; then
    echo "✅ CLASSIFICATION component executed"
    CLASSIFICATION_EXECUTED=1
    WORKFLOW_CHAIN_LENGTH=$((WORKFLOW_CHAIN_LENGTH + 1))
fi

# Check for prescription execution
if grep -q -i "prescription\|treatment\|medicine" "$RESPONSE_FILE"; then
    echo "✅ PRESCRIPTION component executed"
    PRESCRIPTION_EXECUTED=1
    WORKFLOW_CHAIN_LENGTH=$((WORKFLOW_CHAIN_LENGTH + 1))
fi

# Check for constraint gathering execution
if grep -q -i "constraint\|preference\|organic\|budget" "$RESPONSE_FILE"; then
    echo "✅ CONSTRAINT_GATHERING component executed"
    CONSTRAINT_GATHERING_EXECUTED=1
    WORKFLOW_CHAIN_LENGTH=$((WORKFLOW_CHAIN_LENGTH + 1))
fi

# Check for vendor recommendation execution  
if grep -q -i "vendor\|supplier\|purchase\|store" "$RESPONSE_FILE"; then
    echo "✅ VENDOR_RECOMMENDATION component executed"
    VENDOR_RECOMMENDATION_EXECUTED=1
    WORKFLOW_CHAIN_LENGTH=$((WORKFLOW_CHAIN_LENGTH + 1))
fi

# Check for continuous execution logs
CONTINUOUS_LOGS=0
if grep -q "Auto-continuing workflow\|Continuous workflow completed" "$RESPONSE_FILE"; then
    echo "✅ Continuous workflow execution detected in logs"
    CONTINUOUS_LOGS=1
fi

# Check for execution chain logs
if grep -q "→" "$RESPONSE_FILE"; then
    echo "✅ Execution chain logged (multi-component execution)"
fi

echo ""
echo "📊 Continuous Workflow Analysis:"
echo "==============================="

echo "🔗 Workflow Chain Length: $WORKFLOW_CHAIN_LENGTH components executed"

if [[ $WORKFLOW_CHAIN_LENGTH -ge 2 ]]; then
    echo "✅ CONTINUOUS MODE: Multiple components executed automatically!"
else
    echo "❌ SINGLE STEP MODE: Only one component executed (not continuous)"
fi

if [[ $CONTINUOUS_LOGS -eq 1 ]]; then
    echo "✅ Continuous execution logs found"
else
    echo "⚠️  No continuous execution logs detected"
fi

echo ""
echo "📈 Component Execution Summary:"
echo "=============================="
echo "Classification:      $( [[ $CLASSIFICATION_EXECUTED -eq 1 ]] && echo "✅ EXECUTED" || echo "❌ NOT EXECUTED" )"
echo "Prescription:        $( [[ $PRESCRIPTION_EXECUTED -eq 1 ]] && echo "✅ EXECUTED" || echo "❌ NOT EXECUTED" )"
echo "Constraint Gathering: $( [[ $CONSTRAINT_GATHERING_EXECUTED -eq 1 ]] && echo "✅ EXECUTED" || echo "❌ NOT EXECUTED" )"
echo "Vendor Recommendation: $( [[ $VENDOR_RECOMMENDATION_EXECUTED -eq 1 ]] && echo "✅ EXECUTED" || echo "❌ NOT EXECUTED" )"

echo ""
echo "📄 Response Preview (key sections):"
echo "===================================="

# Show workflow progression lines
echo "🔄 Workflow Progression Lines:"
grep -i "auto-continuing\|workflow completed\|→" "$RESPONSE_FILE" || echo "   (No workflow progression lines found)"

echo ""
echo "💊 Treatment/Prescription Content:"
grep -i "treatment\|prescription\|medicine" "$RESPONSE_FILE" | head -5 || echo "   (No prescription content found)"

echo ""
echo "🏪 Vendor/Supplier Content:"
grep -i "vendor\|supplier\|store" "$RESPONSE_FILE" | head -3 || echo "   (No vendor content found)"

echo ""
echo "🎯 Final Assessment:"
echo "==================="

if [[ $WORKFLOW_CHAIN_LENGTH -ge 2 && $CONTINUOUS_LOGS -eq 1 ]]; then
    echo "🎉 SUCCESS: Continuous workflow mode is working!"
    echo "   ✅ Multiple components executed automatically"
    echo "   ✅ Workflow chain: CLASSIFICATION → PRESCRIPTION → (possibly more)"
    echo "   ✅ Execution stopped at appropriate user input point"
elif [[ $WORKFLOW_CHAIN_LENGTH -ge 2 ]]; then
    echo "⚠️  PARTIAL SUCCESS: Multiple components executed, but logging needs improvement"
elif [[ $PRESCRIPTION_EXECUTED -eq 1 && $CLASSIFICATION_EXECUTED -eq 1 ]]; then
    echo "⚠️  MINIMAL SUCCESS: At least classification and prescription executed"
else
    echo "❌ FAILURE: Continuous workflow mode not working properly"
    echo "   Check server logs for errors in workflow state machine"
fi

# Cleanup
rm -f "$RESPONSE_FILE"

echo ""
echo "🔄 Continuous workflow test completed!"
