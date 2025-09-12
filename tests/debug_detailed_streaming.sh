#!/bin/bash

# 🔍 Detailed Streaming Debug Test
# =================================
# Tests streaming with comprehensive logging to identify issues

set -e

echo "🔍 Detailed Streaming Debug Test"
echo "==============================="

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first with detailed logging enabled"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Prepare minimal test data
SESSION_ID="detailed-debug-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "test streaming debug" \
    '{session_id: $session_id, message: $message}')

echo "🎯 Testing Streaming Endpoint with Detailed Debug"
echo "==============================================="
echo "URL: $SERVER_URL/planning/chat-stream"
echo "Session ID: $SESSION_ID"
echo ""

echo "📡 Expected Log Messages to Look For:"
echo "====================================="
echo "1. 📞 stream_callback type: function, callable: True"
echo "2. 🌊 Workflow streaming mode: ENABLED"
echo "3. 🔍 is_streaming = True"
echo "4. 🔍 Initial streaming check: is_streaming=True, response_length=XXX"
echo "5. 📡 About to stream initial response: XXX chars"
echo "6. ✅ Successfully streamed initial [STATE] response"
echo "7. 🔍 Streaming check: is_streaming=True, response_length=XXX"
echo "8. 📡 About to stream separator: '🔄 **[STATE] STEP COMPLETED**'"
echo "9. 📡 About to stream response: XXX chars"
echo "10. ✅ Successfully streamed [STATE] response"
echo ""

echo "🚀 Sending streaming request..."

# Start streaming request in background and capture with timestamps
{
    curl -s -X POST "$SERVER_URL/planning/chat-stream" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_DATA" | while IFS= read -r line; do
        
        timestamp=$(date '+%H:%M:%S.%3N')
        
        # Log to console with timestamp
        if [[ "$line" == data:* ]]; then
            content=${line#data: }
            if [[ "$content" != "[DONE]" && "$content" != "" ]]; then
                echo "🔴 STREAMING [$timestamp]: $content"
            elif [[ "$content" == "[DONE]" ]]; then
                echo "🏁 STREAMING [$timestamp]: COMPLETED"
                break
            fi
        fi
    done
} &

STREAM_PID=$!

# Wait for streaming to complete (with timeout)
timeout 30 wait $STREAM_PID 2>/dev/null || {
    echo ""
    echo "⏰ Streaming timed out after 30 seconds"
    kill $STREAM_PID 2>/dev/null || true
}

echo ""
echo "🔍 Debug Analysis:"
echo "=================="
echo "✅ If you see streaming output above, the queue/callback mechanism works"
echo "❌ If you see only initial messages, check server logs for:"
echo "   • stream_callback type: None, callable: False  (callback not passed)"
echo "   • is_streaming = False  (callback evaluation failed)" 
echo "   • Streaming check: is_streaming=False  (streaming disabled)"
echo ""
echo "🛠️  Troubleshooting Steps:"
echo "========================="
echo "1. Check server logs for callback type and streaming mode"
echo "2. Verify 'About to stream' messages appear in logs"
echo "3. Look for stream callback errors or exceptions"
echo "4. Ensure continuous workflow is executing (multiple components)"
echo ""
echo "💡 Common Issues:"
echo "================"
echo "• Callback not passed correctly from planning_server.py"
echo "• Stream callback function has errors/exceptions"
echo "• Component responses are empty (nothing to stream)"
echo "• Queue mechanism not working properly"

echo ""
echo "🔍 Detailed streaming debug test completed!"
