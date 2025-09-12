#!/bin/bash

# ✅ Complete Streaming Fix Verification Test
# ==========================================
# Tests the complete classification → prescription streaming workflow

set -e

echo "✅ Complete Streaming Fix Verification Test"
echo "==========================================="

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Please start the server with:"
    echo "   cd ../engine/agents && ./run_planning_server.sh --port 8001 &"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Create test image data (small base64 image) 
TEST_IMAGE_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Prepare comprehensive test request
SESSION_ID="streaming-fix-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "please analyze this tomato plant disease and recommend treatment" \
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

echo "🎯 Testing Complete Workflow: CLASSIFICATION → PRESCRIPTION"
echo "=========================================================="
echo "URL: $SERVER_URL/planning/chat-stream"
echo "Session ID: $SESSION_ID" 
echo ""

echo "🔧 Key Fixes Applied:"
echo "===================="
echo "✅ PRESCRIPTION reads from 'classification_results' (not 'diagnosis_results')"
echo "✅ SESSION MANAGER provides both key formats for compatibility"
echo "✅ ENHANCED DEBUG logging throughout the workflow"
echo "✅ STREAMING callback properly logs execution at each step"
echo ""

echo "📊 Expected Streaming Sequence:"
echo "==============================="
echo "1. 🧠 CLASSIFICATION executes → streams disease analysis" 
echo "2. 🔄 **CLASSIFICATION STEP COMPLETED**"
echo "3. 💊 PRESCRIPTION executes → streams treatment recommendations"
echo "4. 🔄 **PRESCRIPTION STEP COMPLETED** "
echo "5. [DONE]"
echo ""

# Track what we actually see
has_classification_content=false
has_prescription_content=false
has_classification_separator=false 
has_prescription_separator=false

echo "🚀 Sending streaming request..."
echo "=============================="

timeout 60 curl -s -X POST "$SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_DATA" | while IFS= read -r line; do
    
    timestamp=$(date '+%H:%M:%S.%3N')
    
    if [[ "$line" == data:* ]]; then
        content=${line#data: }
        if [[ "$content" == "[DONE]" ]]; then
            echo "🏁 STREAMING [$timestamp]: COMPLETED"
            break
        elif [[ "$content" != "" ]]; then
            echo "🔴 [$timestamp] $content"
            
            # Track content types
            if [[ "$content" =~ "CLASSIFICATION STEP COMPLETED" ]]; then
                has_classification_separator=true
                echo "  ✅ FOUND CLASSIFICATION SEPARATOR"
            elif [[ "$content" =~ "PRESCRIPTION STEP COMPLETED" ]]; then
                has_prescription_separator=true  
                echo "  ✅ FOUND PRESCRIPTION SEPARATOR"
            elif [[ "$content" =~ "disease"|"blight"|"classification"|"diagnosis" ]]; then
                has_classification_content=true
                echo "  ✅ FOUND CLASSIFICATION CONTENT"
            elif [[ "$content" =~ "Treatment"|"prescription"|"💊"|"chemical"|"organic"|"fungicide" ]]; then
                has_prescription_content=true
                echo "  ✅ FOUND PRESCRIPTION CONTENT"
            fi
        fi
    fi
done

echo ""
echo "🔍 Streaming Fix Analysis:"
echo "=========================="

# Classification analysis
if [[ "$has_classification_content" == "true" && "$has_classification_separator" == "true" ]]; then
    echo "✅ CLASSIFICATION: Working properly (content + separator)"
else
    echo "❌ CLASSIFICATION: Issue detected"
    [[ "$has_classification_content" != "true" ]] && echo "   • Missing classification content"
    [[ "$has_classification_separator" != "true" ]] && echo "   • Missing classification separator"
fi

# Prescription analysis  
if [[ "$has_prescription_content" == "true" && "$has_prescription_separator" == "true" ]]; then
    echo "✅ PRESCRIPTION: Working properly (content + separator) - FIX SUCCESSFUL!"
else
    echo "❌ PRESCRIPTION: Issue remains"
    [[ "$has_prescription_content" != "true" ]] && echo "   • Missing prescription content (KEY ISSUE)"
    [[ "$has_prescription_separator" != "true" ]] && echo "   • Missing prescription separator"
fi

echo ""
if [[ "$has_prescription_content" == "true" ]]; then
    echo "🎉 SUCCESS: Complete streaming workflow is now working!"
    echo "🎉 The classification_results → prescription key fix resolved the issue!"
else
    echo "🔍 TROUBLESHOOTING: Check server logs for:"
    echo "========================================="
    echo "🏥 Diagnosis results: {disease_name: 'X', confidence: Y}"
    echo "💊 Generating RAG-based prescription..."  
    echo "📄 Formatted response length: X chars"
    echo "✅ Successfully streamed PRESCRIPTION response: X chars"
fi

echo ""
echo "✅ Complete streaming fix verification completed!"
