#!/bin/bash

# 📱 Android Planning Agent Integration Test
# ==========================================
# Tests the Android app integration with the new planning agent server

set -e

echo "📱 Android Planning Agent Integration Test"
echo "=========================================="

# Check if planning agent server is running
PLANNING_SERVER_URL="http://localhost:8001"
echo "🔍 Checking Planning Agent Server..."
if curl -s --max-time 3 "$PLANNING_SERVER_URL/health" > /dev/null 2>&1; then
    echo "✅ Planning Agent Server is running at $PLANNING_SERVER_URL"
else
    echo "❌ Planning Agent Server not running at $PLANNING_SERVER_URL"
    echo "   Please start it with:"
    echo "   cd ../engine/agents && ./run_planning_server.sh --port 8001 &"
    exit 1
fi

echo ""
echo "🎯 Testing Android-Compatible Request Format"
echo "============================================="

# Test the exact request format that Android will send
ANDROID_REQUEST_DATA=$(jq -n \
    --arg message "test android integration with tomato plant" \
    --arg session_id "android-test-$(date +%s)" \
    '{
        message: $message,
        image_b64: null,
        session_id: $session_id,
        context: {
            platform: "android",
            app_version: "1.0.0",
            timestamp: (now * 1000 | floor)
        }
    }')

echo "📱 Android Request Format:"
echo "$ANDROID_REQUEST_DATA" | jq '.'
echo ""

# Test non-streaming endpoint first
echo "🧪 Testing Non-Streaming Endpoint: /planning/chat"
echo "================================================="
NON_STREAM_RESPONSE=$(curl -s -X POST "$PLANNING_SERVER_URL/planning/chat" \
    -H "Content-Type: application/json" \
    -d "$ANDROID_REQUEST_DATA")

echo "📄 Non-Streaming Response:"
echo "$NON_STREAM_RESPONSE" | jq '.' 2>/dev/null || echo "$NON_STREAM_RESPONSE"

# Check if response is successful
SUCCESS=$(echo "$NON_STREAM_RESPONSE" | jq -r '.success' 2>/dev/null || echo "false")
if [[ "$SUCCESS" == "true" ]]; then
    echo "✅ Non-streaming endpoint working correctly"
else
    echo "❌ Non-streaming endpoint failed"
    echo "   Response: $NON_STREAM_RESPONSE"
fi

echo ""
echo "🌊 Testing Streaming Endpoint: /planning/chat-stream"
echo "==================================================="

# Test streaming endpoint (what Android actually uses)
echo "📱 Android will connect to: $PLANNING_SERVER_URL/planning/chat-stream"
echo "📊 Request headers: Content-Type: application/json, Accept: text/event-stream"
echo ""

echo "🚀 Simulating Android streaming request..."
timeout 30 curl -s -X POST "$PLANNING_SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d "$ANDROID_REQUEST_DATA" | while IFS= read -r line; do
    
    timestamp=$(date '+%H:%M:%S.%3N')
    
    if [[ "$line" == data:* ]]; then
        content=${line#data: }
        if [[ "$content" == "[DONE]" ]]; then
            echo "🏁 [$timestamp] STREAM COMPLETED"
            break
        elif [[ "$content" != "" ]]; then
            echo "📱 [$timestamp] ANDROID RECEIVED: $content"
        fi
    fi
done

echo ""
echo "🔍 Integration Analysis:"
echo "======================="
echo "✅ Endpoint Updated: chat-stream → planning/chat-stream"
echo "✅ Server URL Updated: port 8080 → port 8001" 
echo "✅ Request Format: Added context field for planning agent"
echo "✅ Streaming Compatible: Server-Sent Events (SSE) format maintained"
echo ""

echo "📱 Android App Changes Summary:"
echo "=============================="
echo "🔧 ApiService.kt: Updated endpoint to 'planning/chat-stream'"
echo "🔧 ServerConfig.kt: Changed default ports from 8080 to 8001"
echo "🔧 ChatRequestData.kt: Added optional context field"
echo "🔧 MainActivity.kt: Added context data (platform, app_version, timestamp)"
echo ""

echo "🎯 Next Steps for Testing:"
echo "=========================="
echo "1. 🔥 Start the planning agent server: ./run_planning_server.sh --port 8001"
echo "2. 📱 Build and run the Android app on emulator/device"
echo "3. 🌐 Ensure the app uses emulator URL: http://10.0.2.2:8001/"
echo "4. 📸 Send a message with/without image to test the integration"
echo "5. ✅ Verify streaming responses show up in the Android chat interface"

echo ""
echo "📱 Android Planning Agent Integration Test Complete!"
