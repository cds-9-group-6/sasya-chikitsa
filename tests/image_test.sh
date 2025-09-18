#!/bin/bash

# FSM Agent Image Classification Test Script
# Tests image upload and classification

set -e

# Configuration
FSM_SERVER_URL="${FSM_SERVER_URL:-http://localhost:8080}"
CHAT_STREAM_ENDPOINT="$FSM_SERVER_URL/sasya-chikitsa/chat-stream"
IMAGE_PATH="${1:-engine/resources/images_for_test/tomato_mosaic_virus.png}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🖼️  FSM Image Classification Test${NC}"
echo -e "Server: $FSM_SERVER_URL"
echo -e "Image: $IMAGE_PATH"
echo ""

# Check if image exists
if [[ ! -f "$IMAGE_PATH" ]]; then
    echo -e "${RED}❌ Image not found: $IMAGE_PATH${NC}"
    echo ""
    echo "Usage: $0 [image_path]"
    echo "Available test images:"
    ls engine/resources/images_for_test/ 2>/dev/null | head -5
    exit 1
fi

# Check server health
echo -e "${YELLOW}Checking server...${NC}"
if ! curl -s --connect-timeout 5 "$FSM_SERVER_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server not responding${NC}"
    echo "Please start: cd engine/fsm_agent && python3 run_fsm_server.py"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"

# Encode image to base64
echo -e "${YELLOW}Encoding image...${NC}"
ext="${IMAGE_PATH##*.}"
case "${ext,,}" in
    jpg|jpeg) mime_type="image/jpeg" ;;
    png) mime_type="image/png" ;;
    *) mime_type="image/jpeg" ;;
esac

base64_data=$(base64 -i "$IMAGE_PATH" | tr -d '\n')
image_data="data:${mime_type};base64,${base64_data}"

echo -e "${GREEN}✅ Image encoded (${#image_data} characters)${NC}"

# Determine plant type from filename
plant_type="Tomato"
if [[ "$IMAGE_PATH" == *"apple"* || "$IMAGE_PATH" == *"Apple"* ]]; then
    plant_type="Apple"
elif [[ "$IMAGE_PATH" == *"potato"* || "$IMAGE_PATH" == *"Potato"* ]]; then
    plant_type="Potato"
fi

# Create request
SESSION_ID="image-test-$(date +%s)"

echo -e "${YELLOW}Creating request for $plant_type classification...${NC}"

cat > /tmp/image_test_request.json <<EOF
{
    "message": "Please analyze this plant image and tell me what disease or condition it has. Provide detailed diagnosis and treatment recommendations.",
    "session_id": "$SESSION_ID",
    "context": {
        "plant_type": "$plant_type",
        "location": "Maharashtra, India",
        "season": "Summer",
        "growth_stage": "Vegetative",
        "farm_size": "5 acres",
        "farming_experience": "3+ years"
    },
    "image": "$image_data"
}
EOF

echo -e "${BLUE}📤 Sending image classification request...${NC}"
echo -e "${CYAN}This may take a few moments for AI processing...${NC}"
echo ""

# Send request and show streaming response
timeout=60
curl -X POST "$CHAT_STREAM_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d @/tmp/image_test_request.json \
    --no-buffer \
    -s \
    --max-time $timeout | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        event_data="${line#data: }"
        if [[ $event_data == "{"* ]]; then
            # Try to parse and display JSON content
            content=$(echo "$event_data" | jq -r '.content // .message // .' 2>/dev/null || echo "$event_data")
            if [[ $content != "null" && $content != "$event_data" ]]; then
                echo -e "${GREEN}🤖 $content${NC}"
            else
                # Check for specific event types
                event_type=$(echo "$event_data" | jq -r '.type // empty' 2>/dev/null)
                case $event_type in
                    "classification_result")
                        disease=$(echo "$event_data" | jq -r '.disease_name // "Unknown"' 2>/dev/null)
                        confidence=$(echo "$event_data" | jq -r '.confidence // "N/A"' 2>/dev/null)
                        echo -e "${CYAN}🎯 Disease Detected: $disease (Confidence: $confidence)${NC}"
                        ;;
                    "attention_overlay")
                        echo -e "${YELLOW}🔍 AI Attention Overlay Generated${NC}"
                        ;;
                    *)
                        echo -e "${GREEN}📥 $event_data${NC}"
                        ;;
                esac
            fi
        else
            echo -e "${GREEN}📥 $event_data${NC}"
        fi
    elif [[ $line == event:* ]]; then
        event_type="${line#event: }"
        case $event_type in
            "classifying")
                echo -e "${YELLOW}🔬 [Analyzing image...]${NC}"
                ;;
            "thinking")
                echo -e "${BLUE}🧠 [AI thinking...]${NC}"
                ;;
            "complete")
                echo -e "${GREEN}✅ [Analysis complete]${NC}"
                ;;
            *)
                echo -e "${CYAN}[Event: $event_type]${NC}"
                ;;
        esac
    fi
done

echo ""
echo -e "${GREEN}✅ Image classification test completed!${NC}"
echo -e "${CYAN}💡 Check the response above for disease diagnosis and treatment recommendations${NC}"

# Cleanup
rm -f /tmp/image_test_request.json
