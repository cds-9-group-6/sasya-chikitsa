#!/bin/bash

# 💊 Prescription Component Execution Test
# ========================================
# Tests that the prescription component executes after classification

set -e

echo "💊 Prescription Component Execution Test"
echo "======================================="

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

# Create test request
echo "🔬 Testing prescription component execution..."

SESSION_ID="prescription-test-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this plant disease and provide treatment prescription" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer"}' \
    '{session_id: $session_id, message: $message, image_b64: $image_b64, context: $context}')

echo "📡 Sending classification + prescription request..."

# Capture streaming response
RESPONSE_FILE="/tmp/prescription_test_response_${SESSION_ID}.txt"
curl -s -X POST "$SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA" > "$RESPONSE_FILE"

# Analyze response for prescription execution
echo ""
echo "🔍 Analyzing response for prescription execution..."

PRESCRIPTION_FOUND=0
CLASSIFICATION_FOUND=0
CNN_EXECUTED=0
WORKFLOW_PROGRESSION=0

# Check for classification execution
if grep -q -i "cnn\|classification\|diagnosis" "$RESPONSE_FILE"; then
    echo "✅ CNN/Classification executed"
    CLASSIFICATION_FOUND=1
fi

# Check for prescription generation
if grep -q -i "prescription\|treatment\|medicine\|pesticide" "$RESPONSE_FILE"; then
    echo "✅ PRESCRIPTION COMPONENT executed!"
    PRESCRIPTION_FOUND=1
fi

# Check for RAG system usage
if grep -q -i "rag\|treatment.* for\|recommended" "$RESPONSE_FILE"; then
    echo "✅ RAG system appears to be working"
fi

# Check workflow state progression
if grep -q -i "prescription" "$RESPONSE_FILE" && grep -q -i "classification" "$RESPONSE_FILE"; then
    echo "✅ Workflow progressed from CLASSIFICATION → PRESCRIPTION"
    WORKFLOW_PROGRESSION=1
fi

# Check for attention overlay
if grep -q "ATTENTION_OVERLAY_BASE64:" "$RESPONSE_FILE"; then
    echo "✅ Attention overlay generated during classification"
fi

echo ""
echo "📊 Test Results Summary:"
echo "======================="

if [[ $CLASSIFICATION_FOUND -eq 1 ]]; then
    echo "✅ Classification Component: EXECUTED"
else
    echo "❌ Classification Component: NOT DETECTED"
fi

if [[ $PRESCRIPTION_FOUND -eq 1 ]]; then
    echo "✅ Prescription Component: EXECUTED"
else
    echo "❌ Prescription Component: NOT EXECUTED"
fi

if [[ $WORKFLOW_PROGRESSION -eq 1 ]]; then
    echo "✅ Workflow Progression: CLASSIFICATION → PRESCRIPTION"
else
    echo "❌ Workflow Progression: FAILED"
fi

echo ""
echo "📄 Response Preview (first 20 lines):"
echo "======================================"
head -20 "$RESPONSE_FILE"

echo ""
if [[ $PRESCRIPTION_FOUND -eq 1 && $CLASSIFICATION_FOUND -eq 1 && $WORKFLOW_PROGRESSION -eq 1 ]]; then
    echo "🎉 SUCCESS: Prescription component is executing correctly!"
    echo "   The workflow progresses from classification to prescription automatically."
else
    echo "❌ ISSUES DETECTED:"
    if [[ $CLASSIFICATION_FOUND -eq 0 ]]; then
        echo "   • Classification component not executing"
    fi
    if [[ $PRESCRIPTION_FOUND -eq 0 ]]; then
        echo "   • Prescription component not executing - check server logs for errors"
    fi
    if [[ $WORKFLOW_PROGRESSION -eq 0 ]]; then
        echo "   • Workflow not progressing properly between states"
    fi
fi

# Cleanup
rm -f "$RESPONSE_FILE"

echo ""
echo "💊 Prescription execution test completed!"
