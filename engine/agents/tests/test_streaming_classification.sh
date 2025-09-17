# Test 3: Streaming Classification
echo "🌊 Test 3: Streaming Classification"
echo "----------------------------------"

# Handle base URL parameter
if [ $# -eq 0 ]; then
    # No arguments provided, use default or environment variable
    if [ -z "$BASE_URL" ]; then
        BASE_URL="http://localhost:8001"
        echo "🌐 No BASE_URL provided, using default: $BASE_URL"
    else
        echo "🌐 Using BASE_URL from environment: $BASE_URL"
    fi
elif [ $# -eq 1 ]; then
    # One argument provided, use as BASE_URL
    BASE_URL="$1"
    echo "🌐 Using BASE_URL from parameter: $BASE_URL"
else
    # Too many arguments
    echo "❌ Usage: $0 [BASE_URL]"
    echo "   Example: $0 http://localhost:8001"
    echo "   Or set BASE_URL environment variable"
    exit 1
fi

# Validate BASE_URL format (basic check)
if [[ ! "$BASE_URL" =~ ^https?:// ]]; then
    echo "⚠️  Warning: BASE_URL doesn't start with http:// or https://"
    echo "   Current value: $BASE_URL"
fi

# Check if IMAGE_DATA environment variable is set, if not set default value
if [ -z "$IMAGE_DATA" ]; then
    IMAGE_DATA="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    echo "📷 IMAGE_DATA not set, using default image"
else
    echo "📷 Using provided IMAGE_DATA"
fi


STREAM_REQUEST=$(jq -n \
    --arg session_id "test-stream-$(date +%s)" \
    --arg message "Analyze this leaf for plant diseases with detailed progress updates" \
    --arg image_b64 "$IMAGE_DATA" \
    --argjson context '{"test_mode": true, "streaming": true}' \
    '{
        session_id: $session_id,
        message: $message,
        image_b64: $image_b64,
        context: $context
    }')

echo "📋 Streaming Request (jq formatted):"
echo "$STREAM_REQUEST" | jq '.'
echo ""

echo "🌊 Streaming Response (first 20 lines):"
#timeout 15s curl -s -X POST \
#    -H "Content-Type: application/json" \
#    -d "$STREAM_REQUEST" \
#    "$BASE_URL/planning/chat-stream" | head -20 || echo "⏱️  Streaming test completed (timeout after 15s)"

echo "$BASE_URL/planning/chat-stream"

# curl -s -X POST \
#     -H "Content-Type: application/json" \
#     -d "$STREAM_REQUEST" \
#     "$BASE_URL/planning/chat-stream" | head -20 || echo "⏱️  Streaming test completed (timeout after 15s)"

curl -N -X POST \
    -H "Content-Type: application/json" \
    -d "$STREAM_REQUEST" \
    "$BASE_URL/planning/chat"

echo ""
echo ""
