#!/bin/bash

# Debug Workflow Script - Shows why CNN classification isn't triggered
# This script demonstrates the workflow issue

echo "🐛 Planning Agent Workflow Debug"
echo "==============================="
echo ""

# The issue explanation
cat << 'EOF'
🔍 ISSUE IDENTIFIED:

The CNN classification workflow isn't executing because:

1. ✅ Image is provided → Goes to INTENT_CAPTURE state
2. ❌ IntentCaptureComponent extracts context ONLY from user text
3. ❌ Missing crop_type/location → _needs_clarification() returns true
4. ❌ Workflow goes to CLARIFICATION instead of CLASSIFICATION
5. ❌ CNN never gets called

PROBLEM: IntentCaptureComponent ignores the 'context' parameter containing:
{
  "crop_type": "tomato", 
  "location": "California, USA",
  "season": "summer"
}

EOF

echo ""
echo "🧪 Testing current behavior..."
echo ""

# Test what happens with our current request
SERVER_URL="http://localhost:8001"
SESSION_ID="debug-workflow-$(date +%s)"

# Create request that should trigger classification but doesn't
DEBUG_REQUEST=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this plant disease from the uploaded image" \
    --arg image_b64 "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII=" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer", "debug": true}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context,
        workflow_action: null
    }')

echo "📤 Sending debug request..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$DEBUG_REQUEST" \
    "$SERVER_URL/planning/chat" 2>/dev/null)

if [[ $? -eq 0 ]] && [[ -n "$RESPONSE" ]]; then
    echo ""
    echo "📊 Response Analysis:"
    
    # Check current state
    CURRENT_STATE=$(echo "$RESPONSE" | jq -r '.current_state // "unknown"')
    echo "   Current State: $CURRENT_STATE"
    
    # Check if classification happened
    RESPONSE_TEXT=$(echo "$RESPONSE" | jq -r '.response // "no response"')
    if [[ "$RESPONSE_TEXT" == *"classification"* ]] || [[ "$RESPONSE_TEXT" == *"CNN"* ]] || [[ "$RESPONSE_TEXT" == *"confidence"* ]]; then
        echo "   ✅ Classification detected in response"
    else
        echo "   ❌ NO classification detected in response"
    fi
    
    # Show what it's actually doing
    echo ""
    echo "📄 Actual Response:"
    echo "$RESPONSE" | jq '.'
else
    echo "❌ Server not responding. Start server with: ./run_planning_server.sh"
fi

echo ""
echo "🔧 SOLUTION:"
echo "============"
echo ""

cat << 'EOF'
The IntentCaptureComponent needs to be fixed to use the context parameter:

In components/intent_capture.py, the _build_initial_user_profile method should:

1. Check the 'context' parameter passed to execute()
2. Use context values for crop_type, location, etc.
3. Only fall back to extracting from user text if context is empty

This will allow the workflow to proceed directly to CLASSIFICATION when
proper context is provided, triggering the CNN analysis.

WORKAROUND: Include explicit crop and location in the message text:
"Analyze this tomato plant disease in California"
EOF

echo ""
echo "🌊 Try the workaround:"
echo "====================="

# Show workaround command
cat << 'EOF'
# Workaround command with explicit crop/location in message:
IMAGE_DATA=$(head -c 5000 /Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt | tr -d '\n\r')

curl -X POST "http://localhost:8001/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
        --arg session_id "workaround-$(date +%s)" \
        --arg message "Analyze this tomato plant disease in California. I need classification and diagnosis." \
        --arg image_b64 "$IMAGE_DATA" \
        '{session_id: $session_id, message: $message, image_b64: $image_b64, context: {}}')"
EOF
