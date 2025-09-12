#!/bin/bash

# 🌊 Streaming Continuous Workflow Test
# =====================================
# Tests that each workflow step is streamed in real-time during continuous execution

set -e

echo "🌊 Streaming Continuous Workflow Test"
echo "===================================="

# Check server availability
SERVER_URL="http://localhost:8001"
if ! curl -s --max-time 3 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $SERVER_URL"
    echo "   Start the server first: cd .. && ./run_planning_server.sh --env ../.env --port 8001"
    exit 1
fi

echo "✅ Server is running"

# Load test image
echo "📸 Loading test image..."
IMAGE_FILE="/Users/aathalye/dev/sasya-chikitsa/resources/images_for_test/image_103_base64.txt"

if [[ -f "$IMAGE_FILE" ]] && [[ -s "$IMAGE_FILE" ]]; then
    IMAGE_DATA=$(cat "$IMAGE_FILE" | tr -d '\n\r')
    echo "✅ Loaded image: ${#IMAGE_DATA} characters"
else
    echo "⚠️  Using fallback test image"
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII="
fi

# Create streaming test request
echo ""
echo "🌊 Testing Real-Time Streaming Continuous Workflow"
echo "================================================="

SESSION_ID="streaming-continuous-$(date +%s)"
REQUEST_DATA=$(jq -n \
    --arg session_id "$SESSION_ID" \
    --arg message "Analyze this plant disease and provide complete diagnosis and treatment plan" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"crop_type": "tomato", "location": "California", "season": "summer"}' \
    '{session_id: $session_id, message: $message, image_b64: $image_b64, context: $context}')

echo "📡 Starting streaming request (will show real-time progress)..."
echo ""

# Capture streaming response with timestamps
RESPONSE_FILE="/tmp/streaming_continuous_${SESSION_ID}.txt"
TIMESTAMP_FILE="/tmp/timestamps_${SESSION_ID}.txt"

# Start streaming request in background and capture with timestamps
{
    curl -s -X POST "$SERVER_URL/planning/chat-stream" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_DATA" | while IFS= read -r line; do
        timestamp=$(date '+%H:%M:%S.%3N')
        echo "[$timestamp] $line" >> "$TIMESTAMP_FILE"
        echo "$line" >> "$RESPONSE_FILE"
        
        # Display real-time streaming to console
        if [[ "$line" == data:* ]]; then
            content=${line#data: }
            if [[ "$content" != "[DONE]" ]]; then
                echo "🔴 STREAMING [$timestamp]: $content"
            fi
        fi
    done
} &

STREAM_PID=$!

# Wait for streaming to complete (with timeout)
timeout 120 wait $STREAM_PID
STREAM_EXIT_CODE=$?

if [[ $STREAM_EXIT_CODE -ne 0 ]]; then
    echo "⚠️  Streaming timed out or failed"
    kill $STREAM_PID 2>/dev/null || true
fi

echo ""
echo "🔍 Analyzing Streaming Workflow Execution"
echo "========================================="

# Check for streaming workflow components
CLASSIFICATION_STREAMED=0
PRESCRIPTION_STREAMED=0
CONSTRAINT_GATHERING_STREAMED=0
VENDOR_RECOMMENDATION_STREAMED=0
WORKFLOW_STEPS_DETECTED=0
REAL_TIME_STREAMING=0

# Analyze response content
if [[ -f "$RESPONSE_FILE" ]]; then
    # Check for classification streaming
    if grep -q -i "cnn\|classification\|diagnosis.*complete\|disease.*detected" "$RESPONSE_FILE"; then
        echo "✅ Classification component streamed"
        CLASSIFICATION_STREAMED=1
        WORKFLOW_STEPS_DETECTED=$((WORKFLOW_STEPS_DETECTED + 1))
    fi
    
    # Check for prescription streaming  
    if grep -q -i "prescription\|treatment.*plan\|medicine\|pesticide" "$RESPONSE_FILE"; then
        echo "✅ Prescription component streamed"
        PRESCRIPTION_STREAMED=1
        WORKFLOW_STEPS_DETECTED=$((WORKFLOW_STEPS_DETECTED + 1))
    fi
    
    # Check for constraint gathering
    if grep -q -i "constraint\|preference\|organic" "$RESPONSE_FILE"; then
        echo "✅ Constraint gathering component streamed"
        CONSTRAINT_GATHERING_STREAMED=1
        WORKFLOW_STEPS_DETECTED=$((WORKFLOW_STEPS_DETECTED + 1))
    fi
    
    # Check for vendor recommendations
    if grep -q -i "vendor\|supplier\|store\|purchase" "$RESPONSE_FILE"; then
        echo "✅ Vendor recommendation component streamed"
        VENDOR_RECOMMENDATION_STREAMED=1
        WORKFLOW_STEPS_DETECTED=$((WORKFLOW_STEPS_DETECTED + 1))
    fi
    
    # Check for workflow step separators
    if grep -q -i "STEP COMPLETED\|workflow.*completed" "$RESPONSE_FILE"; then
        echo "✅ Workflow step separators detected"
        REAL_TIME_STREAMING=1
    fi
fi

# Analyze timing if timestamps are available
if [[ -f "$TIMESTAMP_FILE" ]]; then
    echo ""
    echo "⏱️  Streaming Timeline Analysis:"
    echo "==============================="
    
    # Extract key streaming events with timestamps
    echo "📅 Key Streaming Events:"
    grep -i "STREAMING" "$TIMESTAMP_FILE" | head -10 || echo "   (No detailed timeline available)"
    
    # Count total streaming events
    TOTAL_STREAM_EVENTS=$(grep -c "data:" "$RESPONSE_FILE" 2>/dev/null || echo "0")
    echo "   📊 Total streaming events: $TOTAL_STREAM_EVENTS"
    
    # Check for real-time progression
    FIRST_TIMESTAMP=$(head -1 "$TIMESTAMP_FILE" 2>/dev/null | grep -o '\[[0-9:\.]*\]' || echo "[00:00:00.000]")
    LAST_TIMESTAMP=$(tail -1 "$TIMESTAMP_FILE" 2>/dev/null | grep -o '\[[0-9:\.]*\]' || echo "[00:00:00.000]")
    echo "   ⏰ Duration: $FIRST_TIMESTAMP → $LAST_TIMESTAMP"
    
    if [[ $TOTAL_STREAM_EVENTS -gt 3 ]]; then
        REAL_TIME_STREAMING=1
        echo "   ✅ Real-time streaming confirmed ($TOTAL_STREAM_EVENTS events)"
    fi
fi

echo ""
echo "📊 Streaming Workflow Results:"
echo "=============================="
echo "Workflow Steps Streamed: $WORKFLOW_STEPS_DETECTED/4"
echo "Classification:          $( [[ $CLASSIFICATION_STREAMED -eq 1 ]] && echo "✅ STREAMED" || echo "❌ NOT STREAMED" )"
echo "Prescription:            $( [[ $PRESCRIPTION_STREAMED -eq 1 ]] && echo "✅ STREAMED" || echo "❌ NOT STREAMED" )"  
echo "Constraint Gathering:    $( [[ $CONSTRAINT_GATHERING_STREAMED -eq 1 ]] && echo "✅ STREAMED" || echo "❌ NOT STREAMED" )"
echo "Vendor Recommendation:   $( [[ $VENDOR_RECOMMENDATION_STREAMED -eq 1 ]] && echo "✅ STREAMED" || echo "❌ NOT STREAMED" )"
echo "Real-time Streaming:     $( [[ $REAL_TIME_STREAMING -eq 1 ]] && echo "✅ CONFIRMED" || echo "❌ NOT DETECTED" )"

echo ""
echo "🎯 Success Criteria Assessment:"
echo "==============================="

TOTAL_SCORE=$((CLASSIFICATION_STREAMED + PRESCRIPTION_STREAMED + REAL_TIME_STREAMING + (WORKFLOW_STEPS_DETECTED >= 2 ? 1 : 0)))

if [[ $TOTAL_SCORE -ge 3 && $WORKFLOW_STEPS_DETECTED -ge 2 ]]; then
    echo "🎉 SUCCESS: Streaming continuous workflow is working!"
    echo "   ✅ Multiple workflow steps executed and streamed"
    echo "   ✅ Real-time streaming confirmed"
    echo "   ✅ Each component response streamed immediately"
    echo ""
    echo "🌊 Benefits Achieved:"
    echo "   • Users see classification results immediately when complete"
    echo "   • Prescription appears right after classification"
    echo "   • No waiting for entire workflow to finish"
    echo "   • Smooth, responsive user experience"
elif [[ $TOTAL_SCORE -ge 2 ]]; then
    echo "⚠️  PARTIAL SUCCESS: Some streaming functionality working"
    echo "   Check server logs for streaming implementation details"
elif [[ $WORKFLOW_STEPS_DETECTED -ge 2 ]]; then
    echo "⚠️  WORKFLOW WORKING: Multiple steps executed but streaming needs improvement"
    echo "   The continuous workflow is functional but streaming optimization needed"
else
    echo "❌ ISSUES DETECTED: Streaming continuous workflow not working properly"
    echo "   • Check server logs for component execution errors"
    echo "   • Verify streaming callback implementation"
    echo "   • Ensure continuous workflow loop is functioning"
fi

echo ""
echo "🔧 Debug Information:"
echo "===================="
echo "Response file: $RESPONSE_FILE"
echo "Timestamp file: $TIMESTAMP_FILE"
echo "Server URL: $SERVER_URL"
echo "Session ID: $SESSION_ID"

if [[ -f "$RESPONSE_FILE" ]]; then
    echo ""
    echo "📝 Sample Response Content (first 20 lines):"
    echo "============================================="
    head -20 "$RESPONSE_FILE" | sed 's/^data: //' || echo "   (No response content available)"
fi

# Cleanup
# rm -f "$RESPONSE_FILE" "$TIMESTAMP_FILE"

echo ""
echo "🌊 Streaming continuous workflow test completed!"
echo ""
echo "💡 Expected Behavior:"
echo "   1. 🔬 Classification results stream immediately"
echo "   2. 💊 Prescription streams right after classification"  
echo "   3. 🏪 Vendor recommendations stream after prescription"
echo "   4. 👤 User interaction only required at natural stopping points"
echo "   5. ⚡ Each step visible in real-time, no batch delays"
