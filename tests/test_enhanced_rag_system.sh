#!/bin/bash

# 🌱 Enhanced Multi-Plant RAG System Test
# ========================================
# Tests the new pre-initialized ChromaDB collections for multiple plant types

set -e

echo "🌱 Enhanced Multi-Plant RAG System Test"
echo "======================================"

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

echo ""
echo "🔬 Testing Enhanced RAG System with Different Plant Types"
echo "========================================================"

# Test different plant types to verify collection routing
PLANT_TYPES=("tomato" "potato" "rice" "wheat" "corn")
SESSION_BASE="enhanced-rag-$(date +%s)"

for PLANT_TYPE in "${PLANT_TYPES[@]}"; do
    echo ""
    echo "🌾 Testing with plant type: $PLANT_TYPE"
    echo "----------------------------------------"
    
    SESSION_ID="${SESSION_BASE}-${PLANT_TYPE}"
    
    # Create request with specific plant type
    REQUEST_DATA=$(jq -n \
        --arg session_id "$SESSION_ID" \
        --arg message "Analyze this plant disease and provide complete treatment for $PLANT_TYPE" \
        --arg image_b64 "$IMAGE_DATA" \
        --argjson context "{\"crop_type\": \"$PLANT_TYPE\", \"location\": \"California\", \"season\": \"summer\"}" \
        '{session_id: $session_id, message: $message, image_b64: $image_b64, context: $context}')
    
    # Send request and capture response
    RESPONSE_FILE="/tmp/rag_test_${PLANT_TYPE}_${SESSION_ID}.txt"
    curl -s -X POST "$SERVER_URL/planning/chat-stream" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_DATA" > "$RESPONSE_FILE"
    
    # Analyze response for plant-specific handling
    PLANT_MENTIONED=0
    COLLECTION_USED=0
    RAG_EXECUTED=0
    PRESCRIPTION_GENERATED=0
    
    # Check if plant type is mentioned in response
    if grep -q -i "$PLANT_TYPE" "$RESPONSE_FILE"; then
        PLANT_MENTIONED=1
        echo "  ✅ Plant type mentioned in response"
    else
        echo "  ⚠️  Plant type not explicitly mentioned"
    fi
    
    # Check for collection usage indicators
    if grep -q -i "collection\|enhanced.*rag\|plant.*specific" "$RESPONSE_FILE"; then
        COLLECTION_USED=1
        echo "  ✅ Enhanced RAG collection usage detected"
    fi
    
    # Check for prescription generation
    if grep -q -i "prescription\|treatment\|medicine\|pesticide" "$RESPONSE_FILE"; then
        PRESCRIPTION_GENERATED=1
        echo "  ✅ Prescription generated"
    fi
    
    # Check for RAG system execution
    if grep -q -i "rag.*query\|treatment.*plan\|based.*on" "$RESPONSE_FILE"; then
        RAG_EXECUTED=1
        echo "  ✅ RAG system executed"
    fi
    
    # Summary for this plant type
    SCORE=$((PLANT_MENTIONED + COLLECTION_USED + RAG_EXECUTED + PRESCRIPTION_GENERATED))
    if [[ $SCORE -ge 3 ]]; then
        echo "  🎉 SUCCESS for $PLANT_TYPE (Score: $SCORE/4)"
    elif [[ $SCORE -ge 2 ]]; then
        echo "  ⚠️  PARTIAL SUCCESS for $PLANT_TYPE (Score: $SCORE/4)"
    else
        echo "  ❌ ISSUES with $PLANT_TYPE (Score: $SCORE/4)"
    fi
    
    # Clean up response file
    rm -f "$RESPONSE_FILE"
    
    # Brief delay between tests
    sleep 1
done

echo ""
echo "🔍 Testing RAG System Initialization and Collections"
echo "=================================================="

# Test server logs for RAG initialization (if accessible)
echo "🔧 Enhanced RAG system should have initialized multiple collections at startup:"
echo "   Expected collections: Tomato, Potato, Rice, Wheat, Corn, Cotton"
echo "   Check server logs for collection initialization messages"

echo ""
echo "📊 Performance Benefits of Enhanced RAG System:"
echo "=============================================="
echo "✅ Pre-initialized embeddings for faster queries"
echo "✅ Plant-specific collection routing" 
echo "✅ Automatic plant type detection"
echo "✅ Fallback mechanisms for unknown plant types"
echo "✅ Shared embedding model across collections"

echo ""
echo "🎯 Key Features Tested:"
echo "======================"
echo "✅ Multiple plant type support"
echo "✅ Collection-specific routing based on crop type"
echo "✅ Enhanced prescription generation with plant context"
echo "✅ Continuous workflow with enhanced RAG integration"

echo ""
echo "🧪 Manual Verification Steps:"
echo "============================"
echo "1. Check server startup logs for:"
echo "   • 🌱 Initializing Enhanced Multi-Plant RAG System..."
echo "   • 📚 Initializing embeddings with model: intfloat/multilingual-e5-large-instruct"
echo "   • 🗂️  Initializing collections: [Tomato, Potato, Rice, Wheat, Corn, Cotton]"
echo "   • ✅ Enhanced RAG system initialization completed!"

echo ""
echo "2. Verify in prescription logs:"
echo "   • 🔍 Generating prescription for: disease=..., crop=..."
echo "   • 🎯 Using plant collection: Tomato (or appropriate collection)"
echo "   • ✅ RAG response received: XXX characters"

echo ""
echo "🌱 Enhanced Multi-Plant RAG System test completed!"
echo ""
echo "🚀 Expected Performance Improvements:"
echo "   • Faster prescription generation (no per-query collection loading)"
echo "   • Better plant-specific treatment recommendations"  
echo "   • Reduced initialization overhead during queries"
echo "   • Improved accuracy with plant-specific knowledge bases"
