#!/bin/bash

# 🔍 Prescription Component Debug Test
# ===================================
# Tests prescription generation with detailed logging

set -e

echo "🔍 Prescription Component Debug Test"
echo "==================================="

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Please start the server first:"
    echo "   cd ../engine/agents && ./run_planning_server.sh --port 8001 &"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Create test image data (small base64 image)
TEST_IMAGE_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Prepare test request with both user input and image
SESSION_ID="prescription-debug-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "analyze this tomato leaf disease" \
    --arg image_b64 "$TEST_IMAGE_B64" \
    '{
        session_id: $session_id, 
        message: $message,
        image_b64: $image_b64,
        context: {
            crop: "tomato",
            location: "California", 
            season: "summer"
        }
    }')

echo "🎯 Testing Prescription Generation with Debug Logging"
echo "===================================================="
echo "URL: $SERVER_URL/planning/chat-stream"
echo "Session ID: $SESSION_ID"
echo ""

echo "📊 Expected Prescription Debug Logs:"
echo "==================================="
echo "1. 🔬 Starting prescription generation for session [id]"
echo "2. 🔍 Session data keys: [list of keys]"  
echo "3. 🔍 Full session data: [complete data]"
echo "4. 👤 User profile: {crop, location, season}"
echo "5. 🏥 Diagnosis results: {disease_name, confidence, etc}"
echo "6. 🔍 Generating prescription for: disease='[name]', crop='tomato'"
echo "7. 📞 Calling RAG system with query: '[query]'"
echo "8. ✅ RAG response received: [X] characters"
echo "9. 📄 Formatted response length: [X] chars"
echo "10. ✅ Successfully streamed PRESCRIPTION response: [X] chars"
echo ""

echo "🚀 Sending streaming request..."

# Start streaming request and capture output with timestamps
timeout 60 curl -s -X POST "$SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA" | while IFS= read -r line; do
    
    timestamp=$(date '+%H:%M:%S.%3N')
    
    # Log to console with timestamp
    if [[ "$line" == data:* ]]; then
        content=${line#data: }
        if [[ "$content" == "[DONE]" ]]; then
            echo "🏁 STREAMING [$timestamp]: COMPLETED"
            break
        elif [[ "$content" != "" ]]; then
            echo "🔴 STREAMING [$timestamp]: $content"
        fi
    fi
done

echo ""
echo "🔍 Prescription Debug Analysis:"
echo "=============================="
echo "✅ Check server logs for prescription component execution"
echo "🔍 Look for these issues:"
echo "   • Empty or missing diagnosis_results in session_data"
echo "   • No disease_name in diagnosis results"  
echo "   • RAG system initialization or query failures"
echo "   • Exception in prescription generation"
echo "   • Empty formatted response"
echo ""
echo "💡 Common Issues:"
echo "================"
echo "• Session data not passed between CLASSIFICATION → PRESCRIPTION"
echo "• diagnosis_results stored under wrong key or format"
echo "• RAG system not working (falling back to empty response)"
echo "• Prescription formatting returning empty string"
echo "• Component result not properly created"

echo ""
echo "🔍 Prescription component debug test completed!"
