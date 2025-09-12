#!/bin/bash

# 🔍 Streaming vs Non-Streaming Endpoint Comparison
# ==================================================
# Tests both endpoints to show when stream_callback is None vs provided

set -e

echo "🔍 Streaming vs Non-Streaming Endpoint Comparison"
echo "================================================="

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: cd .. && ./run_planning_server.sh --env ../.env --port 8001"
    exit 1
fi

echo "✅ Server is running"

# Prepare test data
SESSION_ID="streaming-test-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Test workflow streaming behavior" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer"}' \
    '{session_id: $session_id, message: $message, context: $context}')

echo ""
echo "🔬 Testing Non-Streaming Endpoint (/planning/chat)"
echo "================================================="
echo "Expected: stream_callback = None (DISABLED)"
echo ""

# Test non-streaming endpoint
NON_STREAMING_RESPONSE=$(curl -s -X POST "$SERVER_URL/planning/chat" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA")

echo "📄 Non-Streaming Response:"
echo "$NON_STREAMING_RESPONSE" | jq -r '.response' 2>/dev/null || echo "$NON_STREAMING_RESPONSE"

echo ""
echo "🌊 Testing Streaming Endpoint (/planning/chat-stream)"  
echo "==================================================="
echo "Expected: stream_callback = queue_callback (ENABLED)"
echo ""

# Test streaming endpoint
echo "📡 Streaming Response (real-time):"
STREAMING_OUTPUT=$(curl -s -X POST "$SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA")

echo "$STREAMING_OUTPUT" | grep "^data:" | sed 's/^data: //' | head -10

echo ""
echo "🎯 Key Differences in Server Logs:"
echo "=================================="
echo "Non-Streaming Endpoint Logs:"
echo "  🌊 Workflow streaming mode: DISABLED"
echo "  📝 Collected [STATE] response (no streaming): XXX chars"
echo "  ✅ Non-streaming continuous workflow completed: ..."
echo ""
echo "Streaming Endpoint Logs:"
echo "  🌊 Workflow streaming mode: ENABLED" 
echo "  📡 Streamed [STATE] response: XXX chars"
echo "  ✅ Streaming continuous workflow completed: ..."

echo ""
echo "📊 Endpoint Behavior Summary:"
echo "============================"
echo "┌─────────────────────────────┬─────────────────┬─────────────────────┐"
echo "│ Endpoint                    │ stream_callback │ Streaming Behavior  │"
echo "├─────────────────────────────┼─────────────────┼─────────────────────┤"
echo "│ /planning/chat              │ None            │ ❌ DISABLED         │"
echo "│ /planning/chat-stream       │ queue_callback  │ ✅ ENABLED          │"
echo "│ /legacy/streaming           │ None            │ ❌ DISABLED         │"
echo "│ Direct API calls            │ None            │ ❌ DISABLED         │"
echo "└─────────────────────────────┴─────────────────┴─────────────────────┘"

echo ""
echo "🔧 Why stream_callback is Sometimes None:"
echo "========================================="
echo "✅ CORRECT BEHAVIOR - Only streaming endpoints should have callbacks"
echo "✅ Non-streaming endpoints work faster without streaming overhead"  
echo "✅ Streaming is opt-in behavior for real-time use cases"
echo ""
echo "🎯 To Test Streaming Behavior:"
echo "   • Use: curl -X POST $SERVER_URL/planning/chat-stream"
echo "   • Watch server logs for: '🌊 Workflow streaming mode: ENABLED'"
echo "   • Look for: '📡 Streamed [STATE] response: XXX chars'"
echo ""
echo "🔍 To Test Non-Streaming Behavior:"
echo "   • Use: curl -X POST $SERVER_URL/planning/chat" 
echo "   • Watch server logs for: '🌊 Workflow streaming mode: DISABLED'"
echo "   • Look for: '📝 Collected [STATE] response (no streaming): XXX chars'"

echo ""
echo "🔍 Streaming vs Non-Streaming comparison completed!"
