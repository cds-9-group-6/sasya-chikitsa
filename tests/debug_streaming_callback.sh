#!/bin/bash

# 🔍 Debug Streaming Callback Investigation
# ==========================================
# Explicitly test streaming endpoint to verify callback behavior

set -e

echo "🔍 Debug Streaming Callback Investigation"
echo "========================================"

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: cd .. && ./run_planning_server.sh --env ../.env --port 8001"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Prepare test data
SESSION_ID="debug-callback-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Test streaming callback behavior with minimal request" \
    '{session_id: $session_id, message: $message}')

echo "🎯 Testing EXACTLY the streaming endpoint to verify callback passing"
echo "=================================================================="
echo "URL: $SERVER_URL/planning/chat-stream"
echo "Method: POST"
echo "Expected in logs:"
echo "  📞 stream_callback type: function, callable: True"
echo "  🌊 Workflow streaming mode: ENABLED"
echo ""

echo "🚀 Sending request to streaming endpoint..."
echo "Request data: $REQUEST_DATA"
echo ""

# Make request and show first few lines of response to verify streaming works
echo "📡 Streaming response (first 10 lines):"
echo "========================================"

curl -s -X POST "$SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA" | head -10

echo ""
echo ""
echo "🔍 What to check in server logs:"
echo "==============================="
echo "1. Look for: '📞 stream_callback type: function, callable: True'"
echo "   - If you see: 'type: None, callable: False' → callback not passed!"
echo ""
echo "2. Look for: '🌊 Workflow streaming mode: ENABLED'"
echo "   - If you see: 'DISABLED' → is_streaming logic failed!"
echo ""
echo "3. Look for: '📡 Streamed [STATE] response: XXX chars'"
echo "   - If missing → streaming logic not executing!"
echo ""
echo "4. Look for: '📝 Collected [STATE] response (no streaming): XXX chars'"
echo "   - If present → streaming logic bypassed!"

echo ""
echo "🧪 Quick Verification Test:"
echo "=========================="

# Test non-streaming endpoint for comparison
echo "Testing non-streaming endpoint for comparison..."
NON_STREAMING_RESPONSE=$(curl -s -X POST "$SERVER_URL/planning/chat" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA")

echo "Non-streaming response length: $(echo "$NON_STREAMING_RESPONSE" | wc -c) characters"

echo ""
echo "📊 Expected Log Comparison:"
echo "=========================="
echo "Non-streaming endpoint logs should show:"
echo "  📞 stream_callback type: None, callable: False"
echo "  🌊 Workflow streaming mode: DISABLED"
echo ""
echo "Streaming endpoint logs should show:"
echo "  📞 stream_callback type: function, callable: True  ← KEY DIFFERENCE!"
echo "  🌊 Workflow streaming mode: ENABLED                ← KEY DIFFERENCE!"

echo ""
echo "🔍 Debug streaming callback investigation completed!"
echo ""
echo "💡 If you still see 'stream_callback type: None' for the streaming endpoint,"
echo "   then there's an issue in planning_api.py where queue_callback isn't being passed properly."
