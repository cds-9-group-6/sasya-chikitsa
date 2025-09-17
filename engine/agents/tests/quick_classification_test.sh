#!/bin/bash

# Quick Classification Test - Ready to use jq + curl commands
# Copy and paste these commands to test the Planning Agent classification

echo "🧪 Quick Planning Agent Classification Test"
echo "=========================================="

# Configuration
SERVER_URL="http://localhost:8001"
SESSION_ID="quick-test-$(date +%s)"

echo ""
echo "🔧 Configuration:"
echo "   Server: $SERVER_URL"
echo "   Session ID: $SESSION_ID"
echo ""

# Sample base64 image (1x1 transparent PNG - for testing without real image)
SAMPLE_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="

echo "📋 1. jq Request Creation:"
echo "========================="

# Create classification request with jq
CLASSIFICATION_REQUEST=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Please analyze this plant leaf image for disease detection. What disease or condition do you see? Provide diagnosis and treatment recommendations." \
    --arg image_b64 "$SAMPLE_IMAGE" \
    --argjson context '{"crop_type": "tomato", "location": "test_environment", "season": "summer", "test_mode": true}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context,
        workflow_action: null
    }')

echo "Generated JSON Request:"
echo "$CLASSIFICATION_REQUEST" | jq '.'

echo ""
echo "🚀 2. curl basic Command Execution:"
echo "============================"

# Execute the curl command
echo "Sending classification request..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$CLASSIFICATION_REQUEST" \
    "$SERVER_URL/planning/chat")

echo ""
echo "📊 Response:"
echo "$RESPONSE" | jq '.'

echo ""
echo "✅ Classification test completed!"
