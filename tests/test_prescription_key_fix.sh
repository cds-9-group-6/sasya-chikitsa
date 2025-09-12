#!/bin/bash

# 🔧 Prescription Key Mismatch Fix Test
# ===================================
# Tests prescription with classification_results key fix

set -e

echo "🔧 Prescription Key Mismatch Fix Test"
echo "====================================="

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
SESSION_ID="key-fix-test-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "analyze this tomato leaf disease and provide treatment" \
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

echo "🎯 Testing Key Fix: classification_results → prescription"
echo "======================================================"
echo "URL: $SERVER_URL/planning/chat-stream"
echo "Session ID: $SESSION_ID" 
echo ""

echo "🔍 What Should Happen Now:"
echo "=========================="
echo "✅ CLASSIFICATION state: Store results as 'classification_results'"
echo "✅ PRESCRIPTION state: Read from 'classification_results' (FIXED!)"
echo "✅ Stream both separator AND prescription content"
echo "✅ No more empty prescription responses"
echo ""

echo "🚀 Sending streaming request..."

# Start streaming request and capture actual prescription content
prescription_content=""
has_prescription_content=false

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
            
            # Check if this looks like prescription content
            if [[ "$content" =~ "Treatment"|"prescription"|"💊"|"**Treatment" ]]; then
                has_prescription_content=true
                echo "✅ FOUND PRESCRIPTION CONTENT! ✅"
            fi
        fi
    fi
done

echo ""
echo "🔍 Key Fix Analysis:"
echo "==================="
if [[ "$has_prescription_content" == "true" ]]; then
    echo "✅ SUCCESS: Found prescription content in stream!"
    echo "✅ The classification_results → prescription key fix worked!"
else
    echo "❌ ISSUE: Still no prescription content detected"
    echo "   Check server logs for:"
    echo "   • 🏥 Diagnosis results: {disease_name: 'X', confidence: Y}"  
    echo "   • 💊 Generating RAG-based prescription..."
    echo "   • 📄 Formatted response length: X chars"
fi

echo ""
echo "📊 Expected Server Log Sequence (if working):"
echo "============================================="
echo "1. 🧠 Classification component stores: 'classification_results'"
echo "2. 🔄 Workflow continues to PRESCRIPTION state"
echo "3. 🔍 Session data keys: ['user_profile', 'classification_results', ...]"
echo "4. 🏥 Diagnosis results: {disease_name: 'some_disease', confidence: 0.8}"
echo "5. 💊 Generating RAG-based prescription..."
echo "6. 📄 Formatted response length: 500+ chars"
echo "7. ✅ Successfully streamed PRESCRIPTION response: 500+ chars"

echo ""
echo "🔧 Key fix test completed!"
