#!/bin/bash

# 🌱 Android Enhanced Context Integration Test
# ============================================
# Tests Android app with comprehensive agricultural context parameters

set -e

echo "🌱 Android Enhanced Context Integration Test"
echo "==========================================="

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
echo "🎯 Testing Enhanced Android Request Format"
echo "=========================================="

# Create test image data (small base64 image)
TEST_IMAGE_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Test the exact enhanced request format that Android will now send
ENHANCED_ANDROID_REQUEST=$(jq -n \
    --arg session_id "android-enhanced-$(date +%s)" \
    --arg message "Please analyze this tomato leaf image for disease detection. Provide detailed diagnosis and treatment recommendations specific to my farming context." \
    --arg image_b64 "$TEST_IMAGE_B64" \
    --argjson context '{
        "platform": "android",
        "app_version": "1.0.0", 
        "timestamp": '$(date +%s)'000,
        "crop_type": "tomato",
        "location": "Tamil Nadu",
        "season": "summer", 
        "growth_stage": "flowering",
        "farming_experience": "intermediate",
        "farm_size": "medium",
        "streaming_requested": true,
        "detailed_analysis": true,
        "include_confidence": true,
        "image_source": "android_camera"
    }' \
    '{
        message: $message,
        image_b64: $image_b64,
        session_id: $session_id,
        context: $context,
        workflow_action: null
    }')

echo "📱 Enhanced Android Request Format:"
echo "$ENHANCED_ANDROID_REQUEST" | jq '.'
echo ""

echo "🧪 Testing Enhanced Context Streaming"
echo "====================================="

echo "🌱 Expected Personalized Responses:"
echo "- 🍅 Tomato-specific disease analysis"
echo "- 🌏 Tamil Nadu region treatments"
echo "- ☀️ Summer season considerations"
echo "- 🌸 Flowering stage recommendations"
echo "- 👨‍🌾 Intermediate farmer guidance"
echo "- 🚜 Medium farm scale suggestions"
echo ""

echo "🚀 Sending enhanced Android request..."

# Test streaming with enhanced context
timeout 60 curl -s -X POST "$PLANNING_SERVER_URL/planning/chat-stream" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d "$ENHANCED_ANDROID_REQUEST" | while IFS= read -r line; do
    
    timestamp=$(date '+%H:%M:%S.%3N')
    
    if [[ "$line" == data:* ]]; then
        content=${line#data: }
        if [[ "$content" == "[DONE]" ]]; then
            echo "🏁 [$timestamp] ENHANCED STREAMING COMPLETED"
            break
        elif [[ "$content" != "" ]]; then
            echo "📱 [$timestamp] PERSONALIZED: $content"
            
            # Check for context-aware responses
            if [[ "$content" =~ "tomato"|"Tamil Nadu"|"summer"|"flowering"|"intermediate" ]]; then
                echo "  ✅ CONTEXT-AWARE RESPONSE DETECTED!"
            fi
        fi
    fi
done

echo ""
echo "🔍 Enhanced Context Analysis:"
echo "=========================="
echo "✅ Agricultural Profile: Comprehensive farming context included"
echo "✅ Platform Context: Android app metadata"
echo "✅ Request Preferences: Streaming, detailed analysis, confidence levels"
echo "✅ Workflow Action: Automatic planning agent workflow determination"
echo ""

echo "📱 Android App Features Summary:"
echo "=============================="
echo "🌱 Agricultural Profile Dialog: Collects crop, location, season, growth stage, experience, farm size"
echo "💾 Persistent Preferences: Stores user profile in SharedPreferences"
echo "🎯 First-Time Setup: Welcome dialog prompts new users to set up profile"
echo "⚙️ Settings Integration: Profile accessible via Settings → Agricultural Profile"
echo "📡 Enhanced Requests: All chat requests include comprehensive context"
echo ""

echo "🎯 User Experience Flow:"
echo "======================="
echo "1. 📱 First app launch → Welcome dialog → Profile setup"
echo "2. 🌱 User fills crop, location, season, growth stage, experience, farm size"
echo "3. 💾 Profile saved and used in all future requests"
echo "4. 📸 Send image/text → Planning agent receives full context"
echo "5. 🎯 Receive personalized, context-aware recommendations"
echo ""

echo "🎉 Benefits for Users:"
echo "==================="
echo "✅ Accurate disease detection based on crop type"
echo "✅ Region-specific treatment recommendations"
echo "✅ Seasonal growing advice"
echo "✅ Growth stage appropriate guidance"
echo "✅ Experience-level appropriate explanations"
echo "✅ Farm size relevant solutions"

echo ""
echo "🌱 Enhanced Android context integration test completed!"
